from decimal import Decimal
from enum import Enum
from uuid import UUID
from datetime import datetime, timezone
import hashlib
import json

from sqlalchemy import func, text

from app.models.audit_log import AuditLog

def _json_safe(value):
    if isinstance(value, Enum):
        return _json_safe(value.value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", "replace")
    return value

def snapshot_model(obj):
    if obj is None:
        return None
    return {
        column.name: _json_safe(getattr(obj, column.name))
        for column in obj.__table__.columns
        if column.name not in {"password_hash"}
    }


HASH_VERSION = "SHA256-V1"


def _canonical_payload(action, entity_type, entity_id, user_id, details, created_at):
    normalized_time = created_at.replace(tzinfo=timezone.utc) if created_at.tzinfo is None else created_at.astimezone(timezone.utc)
    return json.dumps({
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "user_id": user_id,
        "details": _json_safe(details or {}),
        "created_at": normalized_time.isoformat(timespec="microseconds"),
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _checksum(payload):
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _lock_chain(db):
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": 0x4E554D4D41554449})


def verify_audit_chain(db):
    rows = db.query(AuditLog).order_by(AuditLog.id).all()
    first_hashed_id = next((row.id for row in rows if row.hash_version), None)
    legacy_rows = sum(1 for row in rows if not row.hash_version and (first_hashed_id is None or row.id < first_hashed_id))
    previous = None
    checked = 0
    errors = []
    for row in rows:
        if not row.hash_version:
            if first_hashed_id is not None and row.id >= first_hashed_id:
                errors.append({"audit_id": row.id, "error": "Unhashed record after ledger boundary"})
            continue
        checked += 1
        payload = _canonical_payload(row.action, row.entity_type, row.entity_id, row.user_id, row.details, row.created_at)
        checksum = _checksum(payload)
        if checksum != row.payload_checksum:
            errors.append({"audit_id": row.id, "error": "Payload checksum mismatch"})
        if previous is None:
            if not (row.previous_hash or "").startswith("LEGACY:"):
                errors.append({"audit_id": row.id, "error": "Invalid ledger boundary"})
        elif row.previous_hash != previous:
            errors.append({"audit_id": row.id, "error": "Broken previous-hash link"})
        expected = _checksum(f"{row.previous_hash}|{row.payload_checksum}|{row.hash_version}")
        if expected != row.current_hash:
            errors.append({"audit_id": row.id, "error": "Current hash mismatch"})
        previous = row.current_hash
    return {
        "status": "VALID" if not errors else "BROKEN",
        "hash_version": HASH_VERSION,
        "legacy_unhashed_records": legacy_rows,
        "hashed_records_checked": checked,
        "boundary_audit_id": first_hashed_id,
        "latest_hash": previous,
        "errors": errors[:100],
    }

def write_audit(db, action, entity_type, entity_id=None, user_id=None, details=None, commit=True):
    _lock_chain(db)
    created_at = datetime.now(timezone.utc)
    safe_details = _json_safe(details or {})
    latest = db.query(AuditLog).filter(AuditLog.current_hash.isnot(None)).order_by(AuditLog.id.desc()).first()
    if latest:
        previous_hash = latest.current_hash
    else:
        legacy_id = db.query(func.max(AuditLog.id)).scalar() or 0
        previous_hash = f"LEGACY:{legacy_id}"
    payload_checksum = _checksum(_canonical_payload(
        action, entity_type, entity_id, user_id, safe_details, created_at
    ))
    current_hash = _checksum(f"{previous_hash}|{payload_checksum}|{HASH_VERSION}")
    obj = AuditLog(
        action=action, entity_type=entity_type, entity_id=entity_id,
        user_id=user_id, details=safe_details, created_at=created_at,
        previous_hash=previous_hash, current_hash=current_hash,
        payload_checksum=payload_checksum, hash_version=HASH_VERSION,
    )
    db.add(obj)
    if commit:
        db.commit()
        db.refresh(obj)
    else:
        db.flush()
    return obj
