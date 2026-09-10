from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.cpse import CPSE
from app.models.user import User
from app.schemas.user_admin import UserRoleUpdate
from app.services.audit_service import write_audit
from app.utils.rbac import (
    CPSE_DATA_MANAGER,
    REQUESTING_OFFICER,
    SYSTEM_ADMIN,
    canonical_role,
    permissions_for,
    public_role,
    require_permission,
)


router = APIRouter(prefix="/api/users", tags=["User Administration"])


def user_data(user: User):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": canonical_role(user.role),
        "cpse_id": user.cpse_id,
        "permissions": permissions_for(user),
        "created_at": user.created_at,
    }


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.manage")),
):
    return [user_data(user) for user in db.query(User).order_by(User.id).all()]


@router.patch("/{user_id}/role")
def update_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.manage")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    role = public_role(payload.role)
    if role in {CPSE_DATA_MANAGER, REQUESTING_OFFICER, "CPSE_OFFICER"}:
        if payload.cpse_id is None:
            raise HTTPException(400, "This role requires a CPSE assignment")
        if not db.query(CPSE).filter(CPSE.id == payload.cpse_id).first():
            raise HTTPException(400, "CPSE not found")

    if canonical_role(user.role) == SYSTEM_ADMIN and role != SYSTEM_ADMIN:
        admin_count = db.query(User).filter(User.role.in_(["ADMIN", SYSTEM_ADMIN])).count()
        if admin_count <= 1:
            raise HTTPException(400, "The final system administrator cannot be demoted")

    previous_role = canonical_role(user.role)
    previous_cpse = user.cpse_id
    user.role = role
    if role not in {CPSE_DATA_MANAGER, REQUESTING_OFFICER, "CPSE_OFFICER"}:
        user.cpse_id = None
    elif "cpse_id" in payload.model_fields_set:
        user.cpse_id = payload.cpse_id
    db.commit()
    db.refresh(user)
    write_audit(
        db, "USER_ROLE_UPDATED", "User", user.id, current_user.id,
        {
            "previous_role": previous_role,
            "new_role": role,
            "previous_cpse_id": previous_cpse,
            "new_cpse_id": user.cpse_id,
        },
    )
    return user_data(user)
