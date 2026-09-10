from abc import ABC, abstractmethod
import asyncio
import hashlib
import json
import threading
import time
from urllib.parse import urljoin, urlsplit
import httpx

from app.config.settings import settings


class ERPConnector(ABC):
    name = "BASE"
    _rate_lock = threading.Lock()
    _next_request_at = 0.0

    @abstractmethod
    async def fetch_materials(self, cpse_id: int, delta_token: str | None = None):
        raise NotImplementedError

    @abstractmethod
    async def push_national_mappings(self, cpse_id: int, mappings: list[dict]):
        raise NotImplementedError

    @abstractmethod
    async def fetch_national_mappings(self, cpse_id: int):
        raise NotImplementedError

    @abstractmethod
    async def health_check(self):
        raise NotImplementedError

    def __init__(self):
        pass

    async def _throttle(self):
        interval = 1.0 / max(settings.SAP_RATE_LIMIT_PER_SECOND, 0.1)
        with ERPConnector._rate_lock:
            scheduled_at = max(time.monotonic(), ERPConnector._next_request_at)
            ERPConnector._next_request_at = scheduled_at + interval
        delay = scheduled_at - time.monotonic()
        if delay > 0:
            await asyncio.sleep(delay)

    async def _request(self, method, url, **kwargs):
        last_error = None
        for attempt in range(3):
            try:
                await self._throttle()
                client_options = {
                    "timeout": settings.SAP_TIMEOUT_SECONDS,
                    "verify": settings.SAP_VERIFY_TLS,
                }
                if settings.SAP_CLIENT_CERT and settings.SAP_CLIENT_KEY:
                    client_options["cert"] = (settings.SAP_CLIENT_CERT, settings.SAP_CLIENT_KEY)
                async with httpx.AsyncClient(**client_options) as client:
                    response = await client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code < 500 and exc.response.status_code not in {408, 429}:
                    raise
                await asyncio.sleep(0.25 * (2 ** attempt))
        raise last_error


class MockSAPConnector(ERPConnector):
    name = "MOCK"

    async def fetch_materials(self, cpse_id, delta_token=None):
        response = await self._request("GET", f"{settings.MOCK_SAP_URL}/api/materials", params={"cpse_id": cpse_id})
        data = response.json()
        return (data if isinstance(data, list) else data.get("materials", [])), None

    async def push_national_mappings(self, cpse_id, mappings):
        body = {"cpse_id": cpse_id, "mappings": mappings}
        key = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        response = await self._request(
            "POST", f"{settings.MOCK_SAP_URL}/api/mappings",
            headers={"Idempotency-Key": key}, json=body,
        )
        return {"connector": self.name, **response.json()}

    async def fetch_national_mappings(self, cpse_id):
        response = await self._request(
            "GET", f"{settings.MOCK_SAP_URL}/api/mappings", params={"cpse_id": cpse_id}
        )
        return response.json().get("value", [])

    async def health_check(self):
        response = await self._request("GET", f"{settings.MOCK_SAP_URL}/health")
        return {"connector": self.name, "status": response.json().get("status", "unknown")}


class SAPODataConnector(ERPConnector):
    name = "ODATA"

    def __init__(self):
        super().__init__()
        self._oauth_token = None
        self._oauth_expires_at = 0.0

    async def _bearer_token(self):
        if settings.SAP_ODATA_TOKEN:
            return settings.SAP_ODATA_TOKEN
        if not all((settings.SAP_OAUTH_TOKEN_URL, settings.SAP_OAUTH_CLIENT_ID, settings.SAP_OAUTH_CLIENT_SECRET)):
            return None
        if self._oauth_token and time.monotonic() < self._oauth_expires_at - 30:
            return self._oauth_token
        response = await self._request(
            "POST",
            settings.SAP_OAUTH_TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(settings.SAP_OAUTH_CLIENT_ID, settings.SAP_OAUTH_CLIENT_SECRET),
        )
        payload = response.json()
        self._oauth_token = payload["access_token"]
        self._oauth_expires_at = time.monotonic() + int(payload.get("expires_in", 300))
        return self._oauth_token

    async def _headers(self):
        token = await self._bearer_token()
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _require_url(self):
        if not settings.SAP_ODATA_URL:
            raise RuntimeError("SAP_ODATA_URL is required for the OData connector")

    async def fetch_materials(self, cpse_id, delta_token=None):
        self._require_url()
        url = delta_token or f"{settings.SAP_ODATA_URL}/Materials"
        params = None if delta_token else {"$filter": f"CpseId eq {cpse_id}"}
        rows = []
        final_delta = delta_token
        for _page in range(100):
            url = urljoin(settings.SAP_ODATA_URL + "/", url)
            base, target = urlsplit(settings.SAP_ODATA_URL), urlsplit(url)
            if (base.scheme, base.netloc) != (target.scheme, target.netloc):
                raise RuntimeError("OData continuation links must stay on the configured SAP origin")
            response = await self._request("GET", url, headers=await self._headers(), params=params)
            payload = response.json()
            data = payload.get("d", payload)
            rows.extend(data.get("results", data.get("value", [])) if isinstance(data, dict) else data)
            next_url = data.get("__next") or data.get("@odata.nextLink") if isinstance(data, dict) else None
            final_delta = data.get("@odata.deltaLink", final_delta) if isinstance(data, dict) else final_delta
            if not next_url:
                break
            url, params = next_url, None
        else:
            raise RuntimeError("SAP OData pagination exceeded the 100-page safety limit")
        return rows, final_delta

    async def push_national_mappings(self, cpse_id, mappings):
        self._require_url()
        body = {"cpse_id": cpse_id, "mappings": mappings}
        idempotency_key = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        response = await self._request("POST", f"{settings.SAP_ODATA_URL}/NationalMaterialMappings", headers={**(await self._headers()), "Content-Type": "application/json", "Idempotency-Key": idempotency_key}, json=body)
        return {"connector": self.name, "status": "COMPLETED", "records": len(mappings), "response": response.json() if response.content else None}

    async def fetch_national_mappings(self, cpse_id):
        self._require_url()
        response = await self._request(
            "GET", f"{settings.SAP_ODATA_URL}/NationalMaterialMappings",
            headers=await self._headers(), params={"$filter": f"CpseId eq {cpse_id}"},
        )
        payload = response.json()
        data = payload.get("d", payload)
        return data.get("results", data.get("value", [])) if isinstance(data, dict) else data

    async def health_check(self):
        self._require_url()
        response = await self._request(
            "GET", f"{settings.SAP_ODATA_URL}/$metadata", headers=await self._headers()
        )
        return {"connector": self.name, "status": "ok", "http_status": response.status_code}


def connector_for(name: str | None):
    key = (name or "MOCK").upper()
    if key == "MOCK":
        return MockSAPConnector()
    if key == "ODATA":
        return SAPODataConnector()
    raise ValueError(f"Unsupported ERP connector: {name}")
