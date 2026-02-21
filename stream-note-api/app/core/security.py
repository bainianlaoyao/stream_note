from datetime import UTC, datetime, timedelta
from typing import Any, Dict
import os

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.env import load_env_file

load_env_file()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-dev-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    expire_at = datetime.now(UTC) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload: Dict[str, Any] = {
        "sub": subject,
        "exp": expire_at,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as error:
        raise ValueError("Invalid access token") from error
