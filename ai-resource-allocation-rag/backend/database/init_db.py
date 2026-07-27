from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from backend.database.models import Employee, HistoricalAllocation, Project, User
from backend.database.session import Base, SessionLocal, engine
from backend.utils.security import hash_password


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


def _seed_users(db: Session) -> None:
    if db.query(User).count() > 0:
        return

    users = [
        User(username="admin", full_name="System Admin", role="admin", password_hash=hash_password("admin123")),
        User(username="manager", full_name="Resource Manager", role="manager", password_hash=hash_password("manager123")),
        User(username="viewer", full_name="Workforce Viewer", role="viewer", password_hash=hash_password("viewer123")),
    ]
    db.add_all(users)


def _seed_employees(db: Session, csv_path: str) -> None:
    if db.query(Employee).count() > 0 or not Path(csv_path).exists():
        return

    df = pd.read_csv(csv_path)
    employees = [
        Employee(
            employee_id=str(row.employee_id),
            name=str(row.name),
            primary_skill=str(row.primary_skill),
            secondary_skill=str(row.secondary_skill),
            years_experience=int(row.years_experience),
            certifications=str(row.certifications),
            availability_status=str(row.availability_status),
            current_utilization=float(row.current_utilization),
            location=str(row.location),
            role=str(row.role),
            resume_text=str(row.resume_text),
        )
        for row in df.itertuples(index=False)
    ]
    db.add_all(employees)


def _seed_projects(db: Session, csv_path: str) -> None:
    if db.query(Project).count() > 0 or not Path(csv_path).exists():
        return

    df = pd.read_csv(csv_path)
    projects = [
        Project(
            project_id=str(row.project_id),
            project_name=str(row.project_name),
            required_skills=str(row.required_skills),
            preferred_certifications=str(row.preferred_certifications),
            min_experience=int(row.min_experience),
            required_headcount=int(row.required_headcount),
            location=str(row.location),
            domain=str(row.domain),
        )
        for row in df.itertuples(index=False)
    ]
    db.add_all(projects)


def _seed_allocations(db: Session, csv_path: str) -> None:
    if db.query(HistoricalAllocation).count() > 0 or not Path(csv_path).exists():
        return

    df = pd.read_csv(csv_path)
    allocations = [
        HistoricalAllocation(
            allocation_id=str(row.allocation_id),
            employee_id=str(row.employee_id),
            project_id=str(row.project_id),
            allocation_month=str(row.allocation_month),
            allocation_percentage=int(row.allocation_percentage),
            performance_rating=float(row.performance_rating),
        )
        for row in df.itertuples(index=False)
    ]
    db.add_all(allocations)


def init_db(seed: bool = True) -> None:
    Base.metadata.create_all(bind=engine)
    if not seed:
        return

    db = SessionLocal()
    try:
        _seed_users(db)
        _seed_employees(db, str(DATA_DIR / "employees.csv"))
        _seed_projects(db, str(DATA_DIR / "projects.csv"))
        _seed_allocations(db, str(DATA_DIR / "historical_allocations.csv"))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    init_db(seed=True)
    print("Database initialized and seeded")
