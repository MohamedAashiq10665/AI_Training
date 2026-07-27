from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database.models import Employee, HistoricalAllocation, Project


class AnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db

    def employee_count(self) -> int:
        return int(self.db.scalar(select(func.count()).select_from(Employee)) or 0)

    def available_count(self) -> int:
        return int(
            self.db.scalar(
                select(func.count()).select_from(Employee).where(func.lower(Employee.availability_status) == "available")
            )
            or 0
        )

    def average_utilization(self) -> float:
        return float(self.db.scalar(select(func.avg(Employee.current_utilization))) or 0.0)

    def bench_count(self, threshold: float = 0.2) -> int:
        return int(
            self.db.scalar(select(func.count()).select_from(Employee).where(Employee.current_utilization < threshold)) or 0
        )

    def bench_by_skill(self, threshold: float = 0.2, limit: int = 10) -> dict:
        rows = self.db.execute(
            select(Employee.primary_skill, func.count())
            .where(Employee.current_utilization < threshold)
            .group_by(Employee.primary_skill)
            .order_by(func.count().desc())
            .limit(limit)
        ).all()
        return {skill: int(count) for skill, count in rows}

    def utilization_by_role(self) -> dict:
        rows = self.db.execute(
            select(Employee.role, func.avg(Employee.current_utilization)).group_by(Employee.role)
        ).all()
        return {role: round(float(avg), 3) for role, avg in rows}

    def historical_allocation_trend(self) -> dict:
        rows = self.db.execute(
            select(HistoricalAllocation.allocation_month, func.count())
            .group_by(HistoricalAllocation.allocation_month)
            .order_by(HistoricalAllocation.allocation_month)
        ).all()
        return {month: int(count) for month, count in rows}

    def skill_demand_trend(self, limit: int = 10) -> dict:
        projects = self.db.scalars(select(Project.required_skills)).all()
        counts: dict[str, int] = {}
        for skills in projects:
            for skill in str(skills or "").split(";"):
                normalized = skill.strip()
                if not normalized:
                    continue
                counts[normalized] = counts.get(normalized, 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:limit])

    def upcoming_project_demand(self, limit: int = 10) -> dict:
        rows = self.db.execute(
            select(Project.domain, func.sum(Project.required_headcount))
            .group_by(Project.domain)
            .order_by(func.sum(Project.required_headcount).desc())
            .limit(limit)
        ).all()
        return {domain: int(total or 0) for domain, total in rows}
