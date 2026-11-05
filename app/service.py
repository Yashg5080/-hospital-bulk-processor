import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Set
from fastapi import HTTPException, WebSocket
import httpx

from app.client import HospitalDirectoryClient
from app.models import (
    BatchProgressResponse,
    BulkProcessResponse,
    HospitalCSVRow,
    HospitalRowResult,
)

CONCURRENCY_LIMIT = 10


@dataclass
class BatchRecord:
    batch_id: str
    rows: List[HospitalCSVRow]
    results: Dict[int, HospitalRowResult] = field(default_factory=dict)
    state: str = "processing"
    batch_activated: bool = False
    processing_time_seconds: float = 0.0
    subscribers: Set[WebSocket] = field(default_factory=set)

    @property
    def total_hospitals(self) -> int:
        return len(self.rows)

    @property
    def processed_hospitals(self) -> int:
        return sum(
            1
            for r in self.results.values()
            if r.status in ("created_inactive", "created_and_activated")
        )

    @property
    def failed_hospitals(self) -> int:
        return sum(1 for r in self.results.values() if r.status == "failed")

    def to_progress_response(self) -> BatchProgressResponse:
        ordered_results = [self.results[row.row] for row in self.rows if row.row in self.results]
        return BatchProgressResponse(
            batch_id=self.batch_id,
            state=self.state,
            total_hospitals=self.total_hospitals,
            processed_hospitals=self.processed_hospitals,
            failed_hospitals=self.failed_hospitals,
            batch_activated=self.batch_activated,
            processing_time_seconds=round(self.processing_time_seconds, 3),
            hospitals=ordered_results,
        )

    def to_bulk_response(self) -> BulkProcessResponse:
        ordered_results = [self.results[row.row] for row in self.rows if row.row in self.results]
        return BulkProcessResponse(
            batch_id=self.batch_id,
            total_hospitals=self.total_hospitals,
            processed_hospitals=self.processed_hospitals,
            failed_hospitals=self.failed_hospitals,
            processing_time_seconds=round(self.processing_time_seconds, 3),
            batch_activated=self.batch_activated,
            hospitals=ordered_results,
        )


class BulkHospitalService:
    def __init__(self, directory_client: HospitalDirectoryClient):
        self.directory_client = directory_client
        self.batches: Dict[str, BatchRecord] = {}

    async def _notify_subscribers(self, record: BatchRecord) -> None:
        if not record.subscribers:
            return
        payload = record.to_progress_response().model_dump()
        stale: List[WebSocket] = []
        for ws in record.subscribers:
            try:
                await ws.send_json(payload)
            except Exception:
                stale.append(ws)
        for ws in stale:
            record.subscribers.discard(ws)

    async def _process_rows(
        self, record: BatchRecord, rows_to_process: List[HospitalCSVRow]
    ) -> None:
        start_time = time.perf_counter()
        record.state = "processing"
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

        timeout = httpx.Timeout(30.0, connect=10.0)
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
        async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:

            async def create_one(csv_row: HospitalCSVRow) -> None:
                async with semaphore:
                    try:
                        created = await self.directory_client.create_hospital(
                            client=client,
                            name=csv_row.name,
                            address=csv_row.address,
                            phone=csv_row.phone,
                            batch_id=record.batch_id,
                        )
                        record.results[csv_row.row] = HospitalRowResult(
                            row=csv_row.row,
                            hospital_id=created.get("id"),
                            name=csv_row.name,
                            status="created_inactive",
                        )
                    except Exception as exc:
                        record.results[csv_row.row] = HospitalRowResult(
                            row=csv_row.row,
                            hospital_id=None,
                            name=csv_row.name,
                            status="failed",
                            error=str(exc),
                        )
                    await self._notify_subscribers(record)

            await asyncio.gather(*(create_one(r) for r in rows_to_process))

            if record.failed_hospitals == 0 and record.processed_hospitals == record.total_hospitals:
                try:
                    await self.directory_client.activate_batch(client, record.batch_id)
                    record.batch_activated = True
                    record.state = "completed"
                    for r in record.results.values():
                        r.status = "created_and_activated"
                except Exception as exc:
                    record.batch_activated = False
                    record.state = "partially_failed"
                    for r in record.results.values():
                        r.error = f"Batch activation failed: {exc}"
            else:
                record.state = "partially_failed"

        elapsed = time.perf_counter() - start_time
        record.processing_time_seconds += elapsed
        await self._notify_subscribers(record)

    async def create_bulk(self, rows: List[HospitalCSVRow]) -> BulkProcessResponse:
        batch_id = str(uuid.uuid4())
        initial_results = {
            r.row: HospitalRowResult(row=r.row, name=r.name, status="pending")
            for r in rows
        }
        record = BatchRecord(batch_id=batch_id, rows=rows, results=initial_results)
        self.batches[batch_id] = record

        await self._process_rows(record, rows)
        return record.to_bulk_response()

    async def resume_batch(self, batch_id: str) -> BulkProcessResponse:
        record = self.batches.get(batch_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found in memory.")

        if record.batch_activated and record.failed_hospitals == 0:
            return record.to_bulk_response()

        failed_rows = [
            r
            for r in record.rows
            if record.results[r.row].status in ("failed", "pending")
        ]
        await self._process_rows(record, failed_rows)
        return record.to_bulk_response()

    def get_status(self, batch_id: str) -> BatchProgressResponse:
        record = self.batches.get(batch_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found.")
        return record.to_progress_response()
