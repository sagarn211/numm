from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Header, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.import_batch import ImportBatch
from app.models.import_error import ImportRowError
from app.models.import_dead_letter import ImportDeadLetter
from app.services.import_service import (
    confirm_import,
    confirm_inventory_import,
    preview_import,
    preview_inventory_import,
    process_import_legacy,
    queue_import,
    run_import_job,
)
from app.models.user import User
from app.utils.rbac import ensure_cpse_access, is_system_admin, require_permission
from app.config.settings import settings

router = APIRouter(tags=["Imports"])

@router.post("/api/import")
def legacy_import(
    file: UploadFile = File(...), cpse_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("import.manage")),
):
    ensure_cpse_access(current_user, cpse_id)
    batch = process_import_legacy(db, file, cpse_id, current_user.id)
    return {
        "batch_id": batch.id,
        "filename": batch.filename,
        "total_rows": batch.total_rows,
        "successful_rows": batch.successful_rows,
        "failed_rows": batch.failed_rows,
        "status": batch.status,
    }

@router.post("/api/imports/preview")
def preview(
    file: UploadFile = File(...), cpse_id: int = Form(...),
    import_type: str = Form("MATERIAL"),
    conflict_policy: str = Form("REJECT"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("import.manage")),
):
    ensure_cpse_access(current_user, cpse_id)
    if import_type.upper() == "INVENTORY":
        if (file.filename or "").lower().endswith(".zip"):
            raise HTTPException(400, "ZIP archives are supported only for material master imports")
        return preview_inventory_import(
            db, file, cpse_id, conflict_policy, current_user.id,
        )
    if import_type.upper() != "MATERIAL":
        raise HTTPException(400, "Import type must be MATERIAL or INVENTORY")
    return preview_import(db, file, cpse_id, current_user.id)

@router.post("/api/imports/{batch_id}/confirm")
def confirm(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("import.manage")),
):
    batch_record = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
    if not batch_record:
        raise HTTPException(404, "Import batch not found")
    ensure_cpse_access(current_user, batch_record.cpse_id)
    batch = (
        confirm_inventory_import(db, batch_id, current_user.id)
        if batch_record.import_type == "INVENTORY"
        else confirm_import(db, batch_id, current_user.id)
    )
    return {
        "batch_id": batch.id,
        "filename": batch.filename,
        "total_rows": batch.total_rows,
        "successful_rows": batch.successful_rows,
        "failed_rows": batch.failed_rows,
        "status": batch.status,
    }

@router.post("/api/imports/{batch_id}/queue")
def queue(
    batch_id: int,
    background_tasks: BackgroundTasks,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("import.manage")),
):
    record = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
    if not record:
        raise HTTPException(404, "Import batch not found")
    ensure_cpse_access(current_user, record.cpse_id)
    batch, should_enqueue = queue_import(db, batch_id, idempotency_key, current_user.id)
    if should_enqueue:
        if settings.IMPORT_QUEUE_MODE == "celery":
            from app.tasks import import_materials_task
            import_materials_task.delay(batch.id)
        else:
            background_tasks.add_task(run_import_job, batch.id)
    return batch

@router.get("/api/imports/{batch_id}/status")
def job_status(
    batch_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("import.manage")),
):
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(404, "Import batch not found")
    ensure_cpse_access(current_user, batch.cpse_id)
    return batch

@router.post("/api/imports/{batch_id}/cancel")
def cancel(
    batch_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("import.manage")),
):
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(404, "Import batch not found")
    ensure_cpse_access(current_user, batch.cpse_id)
    if batch.status in {"COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED", "CANCELLED"}:
        raise HTTPException(409, "Import batch already finished")
    batch.cancellation_requested = True
    db.commit(); db.refresh(batch)
    return batch

@router.get("/api/imports")
def history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("import.manage")),
):
    query = db.query(ImportBatch)
    if not is_system_admin(current_user):
        if current_user.cpse_id is None:
            return []
        query = query.filter(ImportBatch.cpse_id == current_user.cpse_id)
    return query.order_by(ImportBatch.id.desc()).all()

@router.get("/api/imports/{batch_id}/errors")
def errors(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("import.manage")),
):
    batch_record = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
    if not batch_record:
        raise HTTPException(404, "Import batch not found")
    ensure_cpse_access(current_user, batch_record.cpse_id)
    return db.query(ImportRowError).filter(ImportRowError.batch_id == batch_id).order_by(ImportRowError.row_number).all()


@router.get("/api/imports/{batch_id}/dead-letters")
def dead_letters(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("import.manage")),
):
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(404, "Import batch not found")
    ensure_cpse_access(current_user, batch.cpse_id)
    return db.query(ImportDeadLetter).filter(
        ImportDeadLetter.batch_id == batch_id
    ).order_by(ImportDeadLetter.id.desc()).all()
