from fastapi import Depends, HTTPException

from app.models.user import User
from app.utils.security import get_current_user


SYSTEM_ADMIN = "SYSTEM_ADMIN"
CPSE_DATA_MANAGER = "CPSE_DATA_MANAGER"
REQUESTING_OFFICER = "REQUESTING_OFFICER"
PROCUREMENT_OFFICER = "PROCUREMENT_OFFICER"
AUDITOR = "AUDITOR"
PENDING_USER = "PENDING_USER"

ROLE_ALIASES = {
    "ADMIN": SYSTEM_ADMIN,
    "REVIEWER": PROCUREMENT_OFFICER,
    "OFFICER": "CPSE_OFFICER",
}

ROLE_PERMISSIONS = {
    PENDING_USER: set(),
    SYSTEM_ADMIN: {"*"},
    CPSE_DATA_MANAGER: {
        "dashboard.read", "cpse.read", "material.read", "material.write", "import.manage",
        "inventory.read", "inventory.write", "national.read", "matching.search",
        "matching.submit", "data_quality.read", "integration.read", "integration.manage",
        "demand.read", "demand.write", "export.read",
    },
    REQUESTING_OFFICER: {
        "dashboard.read", "cpse.read", "material.read", "inventory.read", "national.read",
        "matching.search", "matching.submit", "request.read", "request.create",
        "request.edit", "request.submit", "demand.read", "export.read",
    },
    PROCUREMENT_OFFICER: {
        "dashboard.read", "cpse.read", "material.read", "inventory.read", "national.read",
        "matching.search", "matching.submit", "approval.read", "approval.review",
        "request.read_all", "request.approve", "request.fulfill", "audit.read",
        "data_quality.read", "national.write", "demand.read", "export.read",
    },
    AUDITOR: {
        "dashboard.read", "cpse.read", "material.read", "inventory.read", "national.read",
        "approval.read", "request.read_all", "audit.read", "data_quality.read",
        "demand.read", "export.read",
    },
    # Backward-compatible combined CPSE role. Maker-checker rules still prevent
    # an officer from approving a request they created themselves.
    "CPSE_OFFICER": {
        "dashboard.read", "cpse.read", "material.read", "material.write", "import.manage",
        "inventory.read", "inventory.write", "national.read", "matching.search",
        "matching.submit", "approval.read", "approval.review", "request.read",
        "request.read_all", "request.create", "request.edit", "request.submit",
        "request.approve", "request.fulfill", "data_quality.read", "integration.read",
        "integration.manage", "demand.read", "demand.write", "export.read",
    },
}


def canonical_role(role: str | None) -> str:
    value = (role or "").strip().upper()
    return ROLE_ALIASES.get(value, value)


def has_permission(user: User, permission: str) -> bool:
    permissions = ROLE_PERMISSIONS.get(canonical_role(user.role), set())
    return "*" in permissions or permission in permissions


def permissions_for(user: User) -> list[str]:
    return sorted(ROLE_PERMISSIONS.get(canonical_role(user.role), set()))


def require_permission(*permissions: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if not any(has_permission(user, permission) for permission in permissions):
            raise HTTPException(403, "You do not have permission to perform this action")
        return user

    return dependency


def is_system_admin(user: User) -> bool:
    return canonical_role(user.role) == SYSTEM_ADMIN


def ensure_cpse_access(user: User, cpse_id: int) -> None:
    if is_system_admin(user):
        return
    if user.cpse_id is None:
        raise HTTPException(403, "Your account must be assigned to a CPSE")
    if int(user.cpse_id) != int(cpse_id):
        raise HTTPException(403, "You can only manage data for your assigned CPSE")


def public_role(role: str | None) -> str:
    value = canonical_role(role)
    allowed = {
        SYSTEM_ADMIN,
        CPSE_DATA_MANAGER,
        REQUESTING_OFFICER,
        PROCUREMENT_OFFICER,
        AUDITOR,
        PENDING_USER,
        "CPSE_OFFICER",
    }
    if value not in allowed:
        raise HTTPException(400, "Invalid role")
    return value
