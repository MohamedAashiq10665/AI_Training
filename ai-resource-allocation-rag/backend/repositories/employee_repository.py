from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import Employee


class EmployeeRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, limit: int = 50) -> list[Employee]:
        return list(self.db.scalars(select(Employee).limit(limit)).all())

    def all(self) -> list[Employee]:
        return list(self.db.scalars(select(Employee)).all())

    def by_ids(self, employee_ids: list[str]) -> list[Employee]:
        if not employee_ids:
            return []
        return list(self.db.scalars(select(Employee).where(Employee.employee_id.in_(employee_ids))).all())
