from app.models.audit_log import (
    AuditLog
)


def create_audit_log(
    db,
    action,
    entity_type=None,
    entity_id=None,
    user_id=None,
    details=None
):

    log = AuditLog(

        action=action,

        entity_type=entity_type,

        entity_id=entity_id,

        user_id=user_id,

        details=details
    )

    db.add(log)

    db.commit()

    db.refresh(log)

    return log