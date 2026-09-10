import hashlib
import json
import threading
import time

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator


router = APIRouter(prefix="/api/mappings", tags=["National Material Mappings"])
_mappings_by_cpse = {}
_idempotency_results = {}
_state_lock = threading.Lock()
IDEMPOTENCY_TTL_SECONDS = 24 * 60 * 60
IDEMPOTENCY_MAX_ENTRIES = 10_000


def _evict_idempotency_entries(now):
    expired = [
        key for key, entry in _idempotency_results.items()
        if entry["expires_at"] <= now
    ]
    for key in expired:
        _idempotency_results.pop(key, None)


class MappingRecord(BaseModel):
    legacy_material_code: str = Field(min_length=1)
    national_material_code: str = Field(min_length=1)
    mapping_type: str | None = None

    @field_validator("legacy_material_code", "national_material_code")
    @classmethod
    def non_blank_code(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("mapping codes cannot be blank")
        return value


class MappingPayload(BaseModel):
    cpse_id: int
    mappings: list[MappingRecord] = Field(default_factory=list)


@router.post("")
def push_mappings(
    payload: MappingPayload,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    fingerprint = hashlib.sha256(
        json.dumps(payload.model_dump(mode="json"), sort_keys=True).encode()
    ).hexdigest()
    scoped_key = (payload.cpse_id, idempotency_key) if idempotency_key else None
    records = {
        (item.legacy_material_code, item.national_material_code): item.model_dump()
        for item in payload.mappings
    }
    result = {"status": "COMPLETED", "records": len(records)}
    with _state_lock:
        now = time.monotonic()
        _evict_idempotency_entries(now)
        if scoped_key and scoped_key in _idempotency_results:
            cached = _idempotency_results[scoped_key]
            if cached["fingerprint"] != fingerprint:
                raise HTTPException(409, "Idempotency key was reused with a different payload")
            return cached["result"]
        _mappings_by_cpse[payload.cpse_id] = list(records.values())
        if scoped_key:
            while len(_idempotency_results) >= IDEMPOTENCY_MAX_ENTRIES:
                _idempotency_results.pop(next(iter(_idempotency_results)))
            _idempotency_results[scoped_key] = {
                "fingerprint": fingerprint,
                "result": result,
                "expires_at": now + IDEMPOTENCY_TTL_SECONDS,
            }
        return result


@router.get("")
def list_mappings(cpse_id: int):
    with _state_lock:
        return {"value": list(_mappings_by_cpse.get(cpse_id, []))}
