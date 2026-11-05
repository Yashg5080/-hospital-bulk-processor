from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import httpx

from app.client import HospitalDirectoryClient
from app.csv_parser import parse_and_validate_csv
from app.models import (
    BatchProgressResponse,
    BulkProcessResponse,
    CSVValidationResponse,
)
from app.service import BulkHospitalService
from app.ui import UI_HTML

app = FastAPI(
    title="Paribus Hospital Bulk Processing API",
    description="Bulk CSV processor integrating with the Hospital Directory API.",
    version="1.0.0",
)

# Enable CORS for cross-origin access and browser dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

directory_client = HospitalDirectoryClient()
bulk_service = BulkHospitalService(directory_client=directory_client)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root_dashboard():
    return HTMLResponse(content=UI_HTML)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


@app.post(
    "/hospitals/bulk/validate",
    response_model=CSVValidationResponse,
    tags=["Bulk Processing"],
    summary="Validate a CSV file before processing",
)
async def validate_bulk_csv(file: UploadFile = File(...)):
    rows, issues = await parse_and_validate_csv(file)
    return CSVValidationResponse(
        valid=len(issues) == 0,
        total_rows=len(rows),
        issues=issues,
    )


@app.post(
    "/hospitals/bulk",
    response_model=BulkProcessResponse,
    tags=["Bulk Processing"],
    summary="Bulk create and activate hospitals from a CSV file",
)
async def bulk_create_hospitals(file: UploadFile = File(...)):
    rows, issues = await parse_and_validate_csv(file)
    if issues:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "CSV row validation failed.",
                "issues": [issue.model_dump() for issue in issues],
            },
        )
    return await bulk_service.create_bulk(rows)


@app.get(
    "/hospitals/bulk/{batch_id}/status",
    response_model=BatchProgressResponse,
    tags=["Progress & Recovery"],
    summary="Poll real-time progress for a bulk batch",
)
async def get_batch_status(batch_id: str):
    return bulk_service.get_status(batch_id)


@app.post(
    "/hospitals/bulk/{batch_id}/resume",
    response_model=BulkProcessResponse,
    tags=["Progress & Recovery"],
    summary="Resume a partially failed bulk operation",
)
async def resume_bulk_batch(batch_id: str):
    return await bulk_service.resume_batch(batch_id)


async def _handle_ws(websocket: WebSocket, batch_id: str):
    await websocket.accept()
    record = bulk_service.batches.get(batch_id)
    if not record:
        await websocket.send_json({"error": f"Batch {batch_id} not found."})
        await websocket.close(code=1008)
        return

    record.subscribers.add(websocket)
    try:
        await websocket.send_json(record.to_progress_response().model_dump())
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        record.subscribers.discard(websocket)


@app.websocket("/ws/hospitals/bulk/{batch_id}")
async def batch_progress_websocket(websocket: WebSocket, batch_id: str):
    await _handle_ws(websocket, batch_id)


@app.websocket("/ws/batch/{batch_id}")
async def batch_progress_websocket_alias(websocket: WebSocket, batch_id: str):
    await _handle_ws(websocket, batch_id)


@app.get(
    "/hospitals/batch/{batch_id}",
    tags=["Upstream Proxy"],
    summary="Fetch hospitals in a batch from upstream Hospital Directory API",
)
async def get_upstream_batch(batch_id: str):
    async with httpx.AsyncClient() as client:
        return await directory_client.get_batch_hospitals(client, batch_id)


@app.delete(
    "/hospitals/batch/{batch_id}",
    tags=["Upstream Proxy"],
    summary="Delete all hospitals in a batch from upstream Hospital Directory API",
)
async def delete_upstream_batch(batch_id: str):
    async with httpx.AsyncClient() as client:
        return await directory_client.delete_batch(client, batch_id)
