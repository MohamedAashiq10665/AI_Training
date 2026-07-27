from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user
from backend.database.session import get_db
from backend.models.schemas import LoginRequest, TokenResponse, UserProfile
from backend.repositories.user_repository import UserRepository
from backend.utils.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = UserRepository(db).get_by_username(payload.username)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=user.username, role=user.role)
    return TokenResponse(access_token=token, role=user.role)


@router.get("/me", response_model=UserProfile)
def me(user=Depends(get_current_user)) -> UserProfile:
    return UserProfile(
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
    )
