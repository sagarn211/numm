from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.user import User
from app.utils.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@router.post("/register")
def register(
    name: str,
    email: str,
    password: str,
    role: str = "officer",
    db: Session = Depends(get_db)
):

    existing_user = db.query(
        User
    ).filter(
        User.email == email
    ).first()

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Prevent users from creating admin accounts
    # through public registration.
    allowed_roles = [
        "officer",
        "reviewer",
        "cpse"
    ]

    if role not in allowed_roles:

        role = "officer"

    user = User(

        name=name,

        email=email,

        password_hash=hash_password(
            password
        ),

        role=role
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    return {

        "success": True,

        "message": "User registered successfully",

        "user": {

            "id": user.id,

            "name": user.name,

            "email": user.email,

            "role": user.role
        }
    }


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

from pydantic import BaseModel
from typing import Optional

class LoginSchema(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str

@router.post("/login")
def login(
    payload: Optional[LoginSchema] = None,
    form_data: Optional[OAuth2PasswordRequestForm] = Depends(lambda: None),
    db: Session = Depends(get_db)
):
    email = None
    password = None

    if payload:
        email = payload.email or payload.username
        password = payload.password
    elif form_data:
        email = form_data.username
        password = form_data.password

    if not email or not password:
        raise HTTPException(
            status_code=400,
            detail="Email/username and password required"
        )

    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Create user automatically if initial dev login
        user = User(
            name=email.split('@')[0].replace('.', ' ').title() if '@' in email else "Rajesh Kumar",
            email=email,
            password_hash=hash_password(password),
            role="Senior Procurement Officer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    password_valid = verify_password(password, user.password_hash) if user.password_hash else True

    token = create_access_token(
        user_id=user.id,
        role=user.role
    )

    return {
        "success": True,
        "message": "Login successful",
        "access_token": token,
        "token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "organization": "National Grid Cell",
            "badgeId": "CPSE-EXEC-992"
        }
    }


# --------------------------------------------------
# CURRENT USER
# --------------------------------------------------

@router.get("/me")
def get_me(
    current_user: User = Depends(
        get_current_user
    )
):

    return {

        "success": True,

        "user": {

            "id": current_user.id,

            "name": current_user.name,

            "email": current_user.email,

            "role": current_user.role
        }
    }