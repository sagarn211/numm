from celery import Celery

from app.config.settings import settings

celery_app = Celery("numm", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
)


@celery_app.task(bind=True, name="numm.import_materials", max_retries=settings.IMPORT_MAX_RETRIES)
def import_materials_task(self, batch_id: int):
    from app.services.import_service import run_import_job
    try:
        run_import_job(batch_id, raise_errors=True)
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=min(60, 2 ** (self.request.retries + 1)))

        from app.config.database import SessionLocal
        from app.models.import_dead_letter import ImportDeadLetter
        from app.services.audit_service import write_audit

        db = SessionLocal()
        try:
            task_id = getattr(self.request, "id", None)
            existing = db.query(ImportDeadLetter).filter(
                ImportDeadLetter.batch_id == batch_id,
                ImportDeadLetter.task_id == task_id,
            ).first()
            if not existing:
                dead_letter = ImportDeadLetter(
                    batch_id=batch_id,
                    task_id=task_id,
                    attempts=self.request.retries + 1,
                    error_message=str(exc)[:4000],
                )
                db.add(dead_letter); db.flush()
                write_audit(db, "IMPORT_DEAD_LETTERED", "ImportBatch", batch_id, details={
                    "task_id": task_id, "attempts": dead_letter.attempts,
                    "error": str(exc)[:500],
                }, commit=False)
                db.commit()
        finally:
            db.close()
        raise
