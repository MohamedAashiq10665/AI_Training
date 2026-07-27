from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

from backend.utils.config import settings


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return base64.b64encode(salt + key).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    decoded = base64.b64decode(password_hash.encode("utf-8"))
    salt = decoded[:16]
    expected = decoded[16:]
    current = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return hmac.compare_digest(expected, current)


def create_access_token(subject: str, role: str, expires_minutes: int | None = None) -> str:
    exp_minutes = expires_minutes or settings.access_token_expire_minutes
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=exp_minutes)
    payload = {"sub": subject, "role": role, "exp": expire_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
