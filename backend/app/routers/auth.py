from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.user import User
from app.models.cpse import CPSE
from app.schemas.auth import RegisterRequest, LoginJSONRequest
from app.utils.security import hash_password, verify_password, create_access_token, get_current_user
from app.utils.rbac import PENDING_USER, canonical_role, permissions_for, public_role

router = APIRouter(prefix="/api/auth", tags=["Auth"])

def normalize_role(role):
    aliases = {
        "OFFICER": PENDING_USER,
        "CPSE": "CPSE_DATA_MANAGER",
    }
    return public_role(aliases.get((role or "").upper(), role))

def token_response(user):
    token = create_access_token(user.id, user.role)
    return {
        "access_token": token,
        "token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": canonical_role(user.role),
            "cpse_id": user.cpse_id,
            "account_status": user.account_status,
            "permissions": permissions_for(user),
        },
    }

@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    # Public registration creates an unscoped pending identity. An administrator
    # must verify the requested organization and assign a working role/CPSE.
    if payload.cpse_id is None:
        raise HTTPException(400, "A CPSE assignment is required")
    if not db.query(CPSE).filter(CPSE.id == payload.cpse_id).first():
        raise HTTPException(400, "Unknown CPSE")
    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=PENDING_USER,
        cpse_id=None,
        account_status="PENDING",
        requested_role="REQUESTING_OFFICER",
        requested_cpse_id=payload.cpse_id,
    )
    db.add(user); db.commit(); db.refresh(user)
    return {
        "id": user.id,
        "message": "Registration submitted. A system administrator must approve your account before you can sign in.",
        "account_status": user.account_status,
    }


@router.get("/registration-cpses")
def registration_cpses(db: Session = Depends(get_db)):
    """Public, minimal CPSE directory used only by the account-request form."""
    return [{"id": cpse.id, "code": cpse.code, "name": cpse.name} for cpse in db.query(CPSE).order_by(CPSE.name).all()]


def ensure_account_is_approved(user: User) -> None:
    if user.account_status == "PENDING":
        raise HTTPException(403, "Your registration is awaiting administrator approval")
    if user.account_status == "REJECTED":
        raise HTTPException(403, "Your account request was not approved. Contact a system administrator.")
    if user.account_status != "APPROVED":
        raise HTTPException(403, "This account is no longer active. Contact a system administrator.")

@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username.lower()).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    ensure_account_is_approved(user)
    return token_response(user)

@router.post("/login-json")
def login_json(payload: LoginJSONRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    ensure_account_is_approved(user)
    return token_response(user)

@router.get("/me")
def me(user: User = Depends(get_current_user)):
    ensure_account_is_approved(user)
    return {
        "id": user.id, "name": user.name, "email": user.email,
        "role": canonical_role(user.role), "cpse_id": user.cpse_id,
        "permissions": permissions_for(user), "account_status": user.account_status,
    }
