from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> User | None:
        return self.db.scalar(select(User).where(User.username == username))
