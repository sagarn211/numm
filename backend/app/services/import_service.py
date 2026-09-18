from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json, math, uuid, zipfile
from fastapi import HTTPException
from sqlalchemy import or_
from app.config.settings import settings
from app.models.import_batch import ImportBatch
from app.models.import_error import ImportRowError
from app.models.material import Material
from app.models.inventory import Inventory
from app.models.cpse import CPSE
from app.services.csv_service import read_csv_file
from app.services.excel_service import read_excel_file
from app.services.cleaning_service import clean_description, normalize_uom, standardize_description
from app.services.canonicalization_service import canonicalize_inventory_row, canonicalize_row
from app.services.validation_service import validate_columns, validate_material_row
from app.services.classification_service import classify_material
from app.services.audit_service import write_audit
from app.config.database import SessionLocal
from app.services.material_schema_service import canonical_standard_description

def _save(file):
    d = Path(settings.UPLOAD_DIR)
    d.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".csv", ".xlsx", ".zip"}:
        raise HTTPException(400, "Material imports support CSV, XLSX, or ZIP; inventory imports support CSV or XLSX")
    path = d / f"{uuid.uuid4().hex}{suffix}"
    written = 0
    try:
        with path.open("wb") as out:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > settings.MAX_IMPORT_FILE_BYTES:
                    raise HTTPException(413, "Import file exceeds the configured size limit")
                out.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    if suffix != ".zip":
        return path, suffix
    # ZIP imports are deliberately material-only and accept a single materials.csv plus images/.
    target = path.with_suffix("")
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > 10000 or sum(entry.file_size for entry in members) > 200 * 1024 * 1024:
                raise HTTPException(413, "ZIP archive exceeds safe extraction limits")
            for entry in members:
                member = Path(entry.filename)
                if member.is_absolute() or ".." in member.parts:
                    raise HTTPException(400, "ZIP contains an unsafe path")
            csv_entries = [entry for entry in members if Path(entry.filename).name.lower() == "materials.csv"]
            if len(csv_entries) != 1:
                raise HTTPException(400, "ZIP must contain exactly one materials.csv")
            archive.extractall(target)
            csv_path = target / csv_entries[0].filename
            if not csv_path.is_file(): raise HTTPException(400, "ZIP materials.csv could not be extracted")
    except zipfile.BadZipFile as exc:
        raise HTTPException(400, "Uploaded ZIP is invalid") from exc
    finally:
        path.unlink(missing_ok=True)
    return csv_path, ".csv"

def _read(path, suffix):
    return read_csv_file(str(path)) if suffix == ".csv" else read_excel_file(str(path))


def _prepare_import_material(item):
    cpse_id, batch_id, code, desc, row = item
    specs = row.get("specifications") or {}
    if not isinstance(specs, dict):
        try:
            specs = json.loads(specs)
        except Exception:
            specs = {"raw": str(specs)}
    cleaned = clean_description(desc)
    classification = classify_material(cleaned, row.get("category"), specs)
    return Material(
        cpse_id=cpse_id, import_batch_id=batch_id, material_code=code,
        description=desc, original_description=desc, cleaned_description=cleaned,
        normalized_description=standardize_description(cleaned),
        recommended_standard_description=canonical_standard_description(
            cleaned, classification.subcategory, specs
        ),
        category=classification.category, subcategory=classification.subcategory,
        classification_confidence=classification.confidence,
        classification_source=classification.source,
        classification_version=classification.rule_version,
        unit=normalize_uom(row.get("unit")), manufacturer=row.get("manufacturer"),
        model=row.get("model"), specifications=specs, source="IMPORT",
    )


def _prepare_import_chunk(items):
    if not items:
        return []
    workers = max(1, min(settings.IMPORT_CLASSIFICATION_WORKERS, len(items)))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(_prepare_import_material, items))

def preview_import(db, file, cpse_id, actor_id=None):
    path, suffix = _save(file)
    try:
        df = _read(path, suffix)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    if len(df) > settings.MAX_IMPORT_ROWS:
        path.unlink(missing_ok=True)
        raise HTTPException(413, "Import file exceeds the configured row limit")
    missing = validate_columns(df.columns)
    if missing:
        path.unlink(missing_ok=True)
        raise HTTPException(400, f"Missing required columns: {', '.join(missing)}")

    batch = ImportBatch(
        filename=file.filename or path.name,
        file_type=suffix.lstrip("."),
        file_path=str(path),
        cpse_id=cpse_id,
        total_rows=len(df),
        status="PREVIEW_READY",
    )
    db.add(batch); db.flush()

    error_rows = set()
    seen_codes = set()
    existing_codes = {
        str(code).strip().upper()
        for (code,) in db.query(Material.material_code).filter(
            Material.cpse_id == cpse_id
        ).all()
        if code
    }
    preview = []
    for idx, raw in df.iterrows():
        row_number = int(idx) + 2
        row = canonicalize_row(raw.to_dict())

        for field, code, message in validate_material_row(row):
            error_rows.add(row_number)
            db.add(ImportRowError(
                batch_id=batch.id, row_number=row_number, field_name=field,
                raw_value=str(row.get(field)), error_code=code,
                error_message=message, severity="ERROR"
            ))

        normalized_code = str(row.get("material_code") or "").strip().upper()
        if normalized_code and (
            normalized_code in seen_codes or normalized_code in existing_codes
        ):
            error_rows.add(row_number)
            db.add(ImportRowError(
                batch_id=batch.id, row_number=row_number, field_name="material_code",
                raw_value=str(row["material_code"]), error_code="DUPLICATE_MATERIAL_CODE",
                error_message="Material code already exists for this CPSE", severity="ERROR"
            ))
        if normalized_code:
            seen_codes.add(normalized_code)

        if len(preview) < 20:
            preview.append(row)

    batch.failed_rows = len(error_rows)
    write_audit(db, "IMPORT_PREVIEWED", "ImportBatch", batch.id, actor_id, {
        "filename": batch.filename, "total_rows": batch.total_rows, "error_rows": len(error_rows),
    }, commit=False)
    db.commit(); db.refresh(batch)

    return {
        "batch_id": batch.id,
        "filename": batch.filename,
        "total_rows": batch.total_rows,
        "valid_rows": batch.total_rows - len(error_rows),
        "warning_rows": batch.warning_rows,
        "error_rows": len(error_rows),
        "status": batch.status,
        "preview": preview,
    }


def _inventory_number(value, field_name, required=False):
    if value is None or str(value).strip() == "":
        if required:
            raise ValueError(f"{field_name.replace('_', ' ').title()} is required")
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name.replace('_', ' ').title()} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field_name.replace('_', ' ').title()} must be finite")
    if number < 0:
        raise ValueError(f"{field_name.replace('_', ' ').title()} cannot be negative")
    return number


def _add_import_issue(db, batch_id, row_number, field, value, code, message, severity="ERROR"):
    db.add(ImportRowError(
        batch_id=batch_id,
        row_number=row_number,
        field_name=field,
        raw_value="" if value is None else str(value),
        error_code=code,
        error_message=message,
        severity=severity,
    ))


def preview_inventory_import(db, file, cpse_id, conflict_policy="REJECT", actor_id=None):
    policy = str(conflict_policy or "REJECT").upper()
    if policy not in {"REJECT", "UPDATE"}:
        raise HTTPException(400, "Inventory conflict policy must be REJECT or UPDATE")

    path, suffix = _save(file)
    try:
        df = _read(path, suffix)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    if len(df) > settings.MAX_IMPORT_ROWS:
        path.unlink(missing_ok=True)
        raise HTTPException(413, "Import file exceeds the configured row limit")

    recognized = canonicalize_inventory_row({column: "present" for column in df.columns})
    missing = [
        field for field in ("material_code", "warehouse", "available_quantity")
        if recognized.get(field) != "present"
    ]
    if missing:
        path.unlink(missing_ok=True)
        raise HTTPException(400, f"Missing required inventory columns: {', '.join(missing)}")

    cpse = db.query(CPSE).filter(CPSE.id == cpse_id).first()
    if not cpse:
        path.unlink(missing_ok=True)
        raise HTTPException(404, "CPSE not found")

    batch = ImportBatch(
        filename=file.filename or path.name,
        file_type=suffix.lstrip("."),
        file_path=str(path),
        import_type="INVENTORY",
        conflict_policy=policy,
        cpse_id=cpse_id,
        total_rows=len(df),
        status="PREVIEW_READY",
    )
    db.add(batch)
    db.flush()

    materials = db.query(Material).filter(Material.cpse_id == cpse_id).all()
    material_by_code = {
        str(material.material_code).strip().upper(): material for material in materials
    }
    existing_keys = {
        (inventory.material_id, inventory.warehouse.strip().upper())
        for inventory in db.query(Inventory).filter(Inventory.cpse_id == cpse_id).all()
    }
    seen_keys = set()
    error_rows = set()
    warning_rows = set()
    preview = []

    for idx, raw in df.iterrows():
        row_number = int(idx) + 2
        row = canonicalize_inventory_row(raw.to_dict())
        code = str(row.get("material_code") or "").strip().upper()
        warehouse = str(row.get("warehouse") or "").strip().upper()
        material = material_by_code.get(code)

        if not code:
            error_rows.add(row_number)
            _add_import_issue(db, batch.id, row_number, "material_code", row.get("material_code"), "MISSING_MATERIAL_CODE", "Material code is required")
        elif not material:
            error_rows.add(row_number)
            _add_import_issue(db, batch.id, row_number, "material_code", code, "UNKNOWN_MATERIAL_CODE", f"Material {code} does not exist for {cpse.code}")
        if not warehouse:
            error_rows.add(row_number)
            _add_import_issue(db, batch.id, row_number, "warehouse", row.get("warehouse"), "MISSING_WAREHOUSE", "Warehouse or depot is required")
        supplied_cpse = str(row.get("cpse_code") or "").strip().upper()
        if supplied_cpse and supplied_cpse != cpse.code.upper():
            error_rows.add(row_number)
            _add_import_issue(db, batch.id, row_number, "cpse_code", supplied_cpse, "CPSE_MISMATCH", f"Row CPSE {supplied_cpse} does not match selected CPSE {cpse.code}")

        available = reserved = unit_cost = None
        for field, required in (("available_quantity", True), ("reserved_quantity", False), ("unit_cost", False)):
            try:
                parsed = _inventory_number(row.get(field), field, required)
                if field == "available_quantity": available = parsed
                elif field == "reserved_quantity": reserved = parsed if parsed is not None else 0.0
                else: unit_cost = parsed
            except ValueError as exc:
                error_rows.add(row_number)
                _add_import_issue(db, batch.id, row_number, field, row.get(field), f"INVALID_{field.upper()}", str(exc))
        if available is not None and reserved is not None and reserved > available:
            error_rows.add(row_number)
            _add_import_issue(db, batch.id, row_number, "reserved_quantity", reserved, "RESERVED_EXCEEDS_AVAILABLE", "Reserved quantity cannot exceed available quantity")

        key = (material.id, warehouse) if material and warehouse else None
        if key and key in seen_keys:
            error_rows.add(row_number)
            _add_import_issue(db, batch.id, row_number, "warehouse", warehouse, "DUPLICATE_FILE_STOCK_ROW", "This material and warehouse combination appears more than once in the file")
        elif key:
            seen_keys.add(key)
            if key in existing_keys:
                if policy == "REJECT":
                    error_rows.add(row_number)
                    _add_import_issue(db, batch.id, row_number, "warehouse", warehouse, "STOCK_RECORD_EXISTS", "Stock already exists for this material and warehouse")
                else:
                    warning_rows.add(row_number)
                    _add_import_issue(db, batch.id, row_number, "warehouse", warehouse, "STOCK_RECORD_WILL_UPDATE", "Existing stock will be updated", "WARNING")

        if len(preview) < 20:
            preview.append({
                "cpse_code": cpse.code,
                "material_code": code,
                "warehouse": warehouse,
                "available_quantity": available,
                "reserved_quantity": reserved,
                "unit": normalize_uom(row.get("unit")) or (material.unit if material else None) or "EA",
                "unit_cost": unit_cost,
                "action": "UPDATE" if key in existing_keys and policy == "UPDATE" else "CREATE",
            })

    batch.failed_rows = len(error_rows)
    batch.warning_rows = len(warning_rows)
    write_audit(db, "INVENTORY_IMPORT_PREVIEWED", "ImportBatch", batch.id, actor_id, {
        "filename": batch.filename,
        "cpse_id": cpse_id,
        "conflict_policy": policy,
        "total_rows": batch.total_rows,
        "error_rows": len(error_rows),
        "warning_rows": len(warning_rows),
    }, commit=False)
    db.commit()
    db.refresh(batch)
    return {
        "batch_id": batch.id,
        "filename": batch.filename,
        "import_type": batch.import_type,
        "conflict_policy": batch.conflict_policy,
        "total_rows": batch.total_rows,
        "valid_rows": batch.total_rows - len(error_rows),
        "warning_rows": batch.warning_rows,
        "error_rows": batch.failed_rows,
        "status": batch.status,
        "preview": preview,
    }


def confirm_inventory_import(db, batch_id, actor_id=None):
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).with_for_update().first()
    if not batch:
        raise HTTPException(404, "Import batch not found")
    if batch.import_type != "INVENTORY":
        raise HTTPException(400, "Import batch is not an inventory import")
    if batch.status in {"COMPLETED", "COMPLETED_WITH_ERRORS"}:
        return batch
    if batch.cancellation_requested:
        batch.status = "CANCELLED"
        batch.current_stage = "CANCELLED"
        db.commit()
        return batch
    if not batch.file_path or not Path(batch.file_path).exists():
        raise HTTPException(409, "Uploaded file for this import batch is no longer available")

    df = _read(batch.file_path, Path(batch.file_path).suffix.lower())
    failed_rows = {
        row_number for (row_number,) in db.query(ImportRowError.row_number).filter(
            ImportRowError.batch_id == batch.id,
            ImportRowError.severity == "ERROR",
        ).all()
    }
    materials = db.query(Material).filter(Material.cpse_id == batch.cpse_id).all()
    material_by_code = {str(item.material_code).strip().upper(): item for item in materials}
    inventories = db.query(Inventory).filter(Inventory.cpse_id == batch.cpse_id).order_by(Inventory.id).with_for_update().all()
    inventory_by_key = {
        (item.material_id, item.warehouse.strip().upper()): item for item in inventories
    }

    batch.status = "PROCESSING"
    batch.current_stage = "INVENTORY_STORE"
    created = updated = 0
    for position, (idx, raw) in enumerate(df.iterrows(), start=1):
        row_number = int(idx) + 2
        batch.processed_rows = position
        batch.progress_percent = min(99, int(position * 100 / max(batch.total_rows, 1)))
        if row_number in failed_rows:
            continue
        row = canonicalize_inventory_row(raw.to_dict())
        code = str(row.get("material_code") or "").strip().upper()
        warehouse = str(row.get("warehouse") or "").strip().upper()
        material = material_by_code.get(code)
        if not material:
            raise HTTPException(409, "A source material changed after preview; preview the file again")
        available = _inventory_number(row.get("available_quantity"), "available_quantity", True)
        reserved = _inventory_number(row.get("reserved_quantity"), "reserved_quantity") or 0.0
        unit_cost = _inventory_number(row.get("unit_cost"), "unit_cost")
        if reserved > available:
            raise HTTPException(400, "Reserved quantity cannot exceed available stock")
        if not warehouse or len(warehouse) > 255:
            raise HTTPException(400, "A valid warehouse is required")
        if normalize_uom(row.get("unit") or material.unit) != normalize_uom(material.unit):
            raise HTTPException(400, "Stock import must use the material base unit")
        key = (material.id, warehouse)
        inventory = inventory_by_key.get(key)
        values = {
            "available_quantity": available,
            "reserved_quantity": reserved,
            "uom": normalize_uom(row.get("unit")) or material.unit or "EA",
            "unit_cost": unit_cost,
            "last_updated": datetime.utcnow(),
        }
        if inventory:
            if batch.conflict_policy != "UPDATE":
                raise HTTPException(409, "Stock was created after preview; preview the file again")
            if reserved < inventory.reserved_quantity:
                raise HTTPException(409, "Stock imports cannot release existing reservations")
            if unit_cost is None:
                values.pop("unit_cost")
            for field, value in values.items():
                setattr(inventory, field, value)
            updated += 1
        else:
            inventory = Inventory(
                cpse_id=batch.cpse_id,
                material_id=material.id,
                warehouse=warehouse,
                **values,
            )
            db.add(inventory)
            inventory_by_key[key] = inventory
            created += 1

    batch.successful_rows = created + updated
    batch.processed_rows = batch.total_rows
    batch.progress_percent = 100
    batch.current_stage = "COMPLETED"
    batch.status = "COMPLETED_WITH_ERRORS" if failed_rows else "COMPLETED"
    batch.confirmed_at = datetime.utcnow()
    write_audit(db, "INVENTORY_IMPORT_COMPLETED", "ImportBatch", batch.id, actor_id, {
        "filename": batch.filename,
        "cpse_id": batch.cpse_id,
        "conflict_policy": batch.conflict_policy,
        "created": created,
        "updated": updated,
        "failed_rows": len(failed_rows),
    }, commit=False)
    db.commit()
    db.refresh(batch)
    return batch

def confirm_import(db, batch_id, actor_id=None, chunk_size=None):
    chunk_size = chunk_size or settings.IMPORT_CHUNK_SIZE
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(404, "Import batch not found")

    if not batch.file_path or not Path(batch.file_path).exists():
        raise HTTPException(409, "Uploaded file for this import batch is no longer available")
    df = _read(batch.file_path, Path(batch.file_path).suffix.lower())
    failed_rows = {
        x.row_number for x in db.query(ImportRowError).filter(
            ImportRowError.batch_id == batch.id,
            ImportRowError.severity == "ERROR"
        ).all()
    }

    batch.status = "PROCESSING"
    batch.current_stage = "NORMALIZE"
    db.commit()
    existing_codes = {
        str(code).strip().upper()
        for (code,) in db.query(Material.material_code).filter(
            Material.cpse_id == batch.cpse_id,
            or_(
                Material.import_batch_id.is_(None),
                Material.import_batch_id != batch.id,
            ),
        ).all()
        if code
    }
    current_batch_codes = {
        str(code).strip().upper()
        for (code,) in db.query(Material.material_code).filter(
            Material.import_batch_id == batch.id
        ).all()
        if code
    }
    pending = []
    for position, (idx, raw) in enumerate(df.iterrows(), start=1):
        row_number = int(idx) + 2
        batch.processed_rows = min(position, batch.total_rows)
        batch.progress_percent = min(99, int(batch.processed_rows * 100 / max(batch.total_rows, 1)))
        if position % 100 == 0:
            db.commit()
            db.refresh(batch)
        if batch.cancellation_requested:
            if pending:
                db.bulk_save_objects(_prepare_import_chunk(pending))
                pending.clear()
            batch.successful_rows = db.query(Material).filter(
                Material.import_batch_id == batch.id
            ).count()
            batch.status = "CANCELLED"
            batch.current_stage = "CANCELLED"
            write_audit(db, "IMPORT_CANCELLED", "ImportBatch", batch.id, actor_id, commit=False)
            db.commit()
            return batch
        if row_number in failed_rows:
            continue

        row = canonicalize_row(raw.to_dict())
        code = str(row["material_code"]).strip().upper()
        desc = str(row["description"]).strip()
        if code in current_batch_codes:
            continue
        if code in existing_codes:
            failed_rows.add(row_number)
            db.add(ImportRowError(
                batch_id=batch.id,
                row_number=row_number,
                field_name="material_code",
                raw_value=str(row["material_code"]),
                error_code="DUPLICATE_MATERIAL_CODE",
                error_message="Material code already exists for this CPSE",
                severity="ERROR",
            ))
            continue
        existing_codes.add(code)
        current_batch_codes.add(code)

        pending.append((batch.cpse_id, batch.id, code, desc, row))
        if len(pending) >= chunk_size:
            db.bulk_save_objects(_prepare_import_chunk(pending))
            db.commit()
            pending.clear()
            db.refresh(batch)

    if pending:
        db.bulk_save_objects(_prepare_import_chunk(pending))

    batch.successful_rows = db.query(Material).filter(Material.import_batch_id == batch.id).count()
    batch.failed_rows = len(failed_rows)
    batch.status = "COMPLETED" if not failed_rows else "COMPLETED_WITH_ERRORS"
    batch.processed_rows = batch.total_rows
    batch.progress_percent = 100
    batch.current_stage = "COMPLETED"
    batch.confirmed_at = datetime.utcnow()
    write_audit(db, "IMPORT_COMPLETED", "ImportBatch", batch.id, actor_id, {
        "successful_rows": batch.successful_rows, "failed_rows": len(failed_rows), "status": batch.status,
    }, commit=False)
    db.commit(); db.refresh(batch)
    return batch

def queue_import(db, batch_id, idempotency_key, actor_id=None):
    if idempotency_key:
        existing = db.query(ImportBatch).filter(ImportBatch.idempotency_key == idempotency_key).first()
        if existing and existing.id != batch_id:
            return existing, False
    batch = db.query(ImportBatch).filter(
        ImportBatch.id == batch_id
    ).with_for_update().first()
    if not batch:
        raise HTTPException(404, "Import batch not found")
    if batch.status not in {"PREVIEW_READY", "FAILED", "CANCELLED", "COMPLETED_WITH_AI_ERROR"}:
        return batch, False
    retry_ai_only = batch.import_type == "MATERIAL" and batch.status == "COMPLETED_WITH_AI_ERROR"
    batch.idempotency_key = idempotency_key or f"import-{batch.id}"
    batch.requested_by = actor_id
    batch.status = "AI_QUEUED" if retry_ai_only else "QUEUED"
    batch.current_stage = "AI_QUEUED" if retry_ai_only else "QUEUED"
    batch.progress_percent = 100 if retry_ai_only else 0
    batch.cancellation_requested = False
    batch.error_message = None
    write_audit(
        db,
        "IMPORT_AI_RETRY_QUEUED" if retry_ai_only else "IMPORT_QUEUED",
        "ImportBatch",
        batch.id,
        actor_id,
        {"idempotency_key": batch.idempotency_key, "import_type": batch.import_type},
        commit=False,
    )
    db.commit(); db.refresh(batch)
    return batch, True

def run_import_job(batch_id, raise_errors=False):
    import asyncio
    from app.services.matching_service import run_matching

    db = SessionLocal()
    try:
        batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
        if batch and batch.status in {"QUEUED", "FAILED", "AI_QUEUED", "COMPLETED_WITH_AI_ERROR"}:
            if batch.import_type == "INVENTORY":
                return confirm_inventory_import(db, batch.id, batch.requested_by)
            if batch.status in {"QUEUED", "FAILED"}:
                batch = confirm_import(db, batch.id, batch.requested_by)
            batch.current_stage = "AI_CANDIDATES"
            db.commit()
            try:
                imported_ids = {
                    material_id for (material_id,) in db.query(Material.id).filter(
                        Material.import_batch_id == batch.id
                    ).all()
                }
                recommendations = asyncio.run(run_matching(db, imported_ids)) if imported_ids else []
                batch.status = "COMPLETED_WITH_ERRORS" if batch.failed_rows else "COMPLETED"
                batch.current_stage = "COMPLETED"
                batch.error_message = None
                write_audit(db, "IMPORT_AI_CANDIDATES_GENERATED", "ImportBatch", batch.id, batch.requested_by, {
                    "recommendations_created": len(recommendations),
                }, commit=False)
                db.commit()
            except Exception as ai_exc:
                db.rollback()
                batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
                batch.status = "COMPLETED_WITH_AI_ERROR"
                batch.current_stage = "AI_CANDIDATES_FAILED"
                batch.error_message = str(ai_exc)[:1000]
                write_audit(db, "IMPORT_AI_CANDIDATES_FAILED", "ImportBatch", batch.id, batch.requested_by, {
                    "error": str(ai_exc)[:500],
                }, commit=False)
                db.commit()
                if raise_errors:
                    raise
            return batch
    except Exception as exc:
        db.rollback()
        batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
        if batch and batch.current_stage != "AI_CANDIDATES_FAILED":
            batch.status = "FAILED"
            batch.current_stage = "FAILED"
            batch.error_message = str(exc)[:1000]
            write_audit(db, "IMPORT_FAILED", "ImportBatch", batch.id, batch.requested_by, {"error": str(exc)[:500]}, commit=False)
            db.commit()
        if raise_errors:
            raise
    finally:
        db.close()

def process_import_legacy(db, file, cpse_id, actor_id=None):
    preview = preview_import(db, file, cpse_id, actor_id)
    return confirm_import(db, preview["batch_id"], actor_id)
