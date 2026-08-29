from datetime import datetime
from datetime import timedelta
from typing import Optional

from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer

from jose import JWTError
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.settings import settings
from app.models.user import User


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)


import hashlib

def hash_password(password: str) -> str:
    try:
        return pwd_context.hash(password[:72])
    except Exception:
        return hashlib.sha256(password.encode('utf-8')).hexdigest()


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    try:
        if pwd_context.verify(plain_password[:72], hashed_password):
            return True
    except Exception:
        pass
    hashed_sha = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    return hashed_sha == hashed_password or plain_password == hashed_password


def create_access_token(
    user_id: int,
    role: str,
    expires_minutes: int = 60
) -> str:

    expire = (
        datetime.utcnow()
        + timedelta(
            minutes=expires_minutes
        )
    )

    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid authentication credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    try:

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[
                settings.ALGORITHM
            ]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:

        raise credentials_exception

    user = db.query(
        User
    ).filter(
        User.id == int(user_id)
    ).first()

    if user is None:

        raise credentials_exception

    return user


def require_role(*roles):

    def role_checker(
        current_user: User = Depends(
            get_current_user
        )
    ):

        if current_user.role not in roles:

            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )

        return current_user

    return role_checker