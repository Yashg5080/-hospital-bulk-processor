import asyncio
import os
from typing import Any, Dict, List, Optional
import httpx

UPSTREAM_BASE_URL = os.getenv(
    "HOSPITAL_API_BASE_URL", "https://hospital-directory.onrender.com"
).rstrip("/")


class HospitalDirectoryClient:
    def __init__(self, base_url: str = UPSTREAM_BASE_URL, timeout: float = 30.0, max_retries: int = 3):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

    async def _request_with_retry(
        self,
        client: httpx.AsyncClient,
        method: str,
        path: str,
        json_payload: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        url = f"{self.base_url}{path}"
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await client.request(method, url, json=json_payload, timeout=self.timeout)
                if response.status_code >= 500 and attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                    continue
                response.raise_for_status()
                return response
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                if (
                    isinstance(exc, httpx.HTTPStatusError)
                    and 400 <= exc.response.status_code < 500
                    and exc.response.status_code != 429
                ):
                    raise
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))

        assert last_exc is not None
        raise last_exc

    async def create_hospital(
        self,
        client: httpx.AsyncClient,
        name: str,
        address: str,
        phone: Optional[str],
        batch_id: str,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "name": name,
            "address": address,
            "creation_batch_id": batch_id,
        }
        if phone is not None:
            payload["phone"] = phone

        resp = await self._request_with_retry(client, "POST", "/hospitals/", json_payload=payload)
        return resp.json()

    async def activate_batch(self, client: httpx.AsyncClient, batch_id: str) -> Dict[str, Any]:
        resp = await self._request_with_retry(
            client, "PATCH", f"/hospitals/batch/{batch_id}/activate"
        )
        return resp.json() if resp.content else {"activated": True}

    async def get_batch_hospitals(self, client: httpx.AsyncClient, batch_id: str) -> List[Dict[str, Any]]:
        resp = await self._request_with_retry(client, "GET", f"/hospitals/batch/{batch_id}")
        return resp.json()

    async def delete_batch(self, client: httpx.AsyncClient, batch_id: str) -> Dict[str, Any]:
        resp = await self._request_with_retry(client, "DELETE", f"/hospitals/batch/{batch_id}")
        return resp.json() if resp.content else {"deleted": True}
