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
    )
    db.add(user); db.commit(); db.refresh(user)
    return token_response(user)

@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username.lower()).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return token_response(user)

@router.post("/login-json")
def login_json(payload: LoginJSONRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return token_response(user)

@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id, "name": user.name, "email": user.email,
        "role": canonical_role(user.role), "cpse_id": user.cpse_id,
        "permissions": permissions_for(user),
    }
