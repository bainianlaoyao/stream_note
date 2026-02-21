import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.ai_provider_setting import AIProviderSetting
from app.models.block import Block
from app.models.database import get_db
from app.models.document import Document
from app.models.silent_analysis_job import SilentAnalysisJob
from app.models.task import TaskCache
from app.models.user import User

router = APIRouter()
USERNAME_PATTERN = re.compile(r"^[a-z0-9_.-]{3,32}$")


class UserCredentials(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        username = value.strip().lower()
        if not USERNAME_PATTERN.fullmatch(username):
            raise ValueError(
                "Username must be 3-32 chars: lowercase letters, numbers, dot, underscore, or hyphen."
            )
        return username

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        password = value.strip()
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters.")
        return password


class UserResponse(BaseModel):
    id: str
    username: str
    created_at: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        username=user.username,
        created_at=user.created_at.isoformat(),
    )


def _claim_orphan_data(db: Session, user_id: str) -> None:
    db.query(Document).filter(Document.user_id.is_(None)).update(
        {Document.user_id: user_id},
        synchronize_session=False,
    )
    db.query(Block).filter(Block.user_id.is_(None)).update(
        {Block.user_id: user_id},
        synchronize_session=False,
    )
    db.query(TaskCache).filter(TaskCache.user_id.is_(None)).update(
        {TaskCache.user_id: user_id},
        synchronize_session=False,
    )
    db.query(AIProviderSetting).filter(AIProviderSetting.user_id.is_(None)).update(
        {AIProviderSetting.user_id: user_id},
        synchronize_session=False,
    )
    db.query(SilentAnalysisJob).filter(SilentAnalysisJob.user_id.is_(None)).update(
        {SilentAnalysisJob.user_id: user_id},
        synchronize_session=False,
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(credentials: UserCredentials, db: Session = Depends(get_db)) -> AuthResponse:
    existing = db.query(User).filter(User.username == credentials.username).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Username already exists")

    user_count = db.query(func.count(User.id)).scalar() or 0
    is_first_user = int(user_count) == 0

    user = User(
        username=credentials.username,
        password_hash=hash_password(credentials.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if is_first_user:
        _claim_orphan_data(db=db, user_id=str(user.id))
        db.commit()

    token = create_access_token(subject=str(user.id))
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=_to_user_response(user),
    )


@router.post("/login", response_model=AuthResponse)
def login(credentials: UserCredentials, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(User).filter(User.username == credentials.username).first()
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(subject=str(user.id))
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=_to_user_response(user),
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return _to_user_response(current_user)
