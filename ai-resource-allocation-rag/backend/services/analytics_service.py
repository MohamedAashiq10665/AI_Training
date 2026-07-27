from __future__ import annotations

from sqlalchemy.orm import Session

from backend.repositories.analytics_repository import AnalyticsRepository


class AnalyticsService:
    def get_overview(self, db: Session) -> dict:
        repo = AnalyticsRepository(db)
        total = repo.employee_count()
        available = repo.available_count()
        bench = repo.bench_count()
        utilization = repo.average_utilization()

        return {
            "total_employees": total,
            "available_employees": available,
            "bench_percentage": round((bench / max(1, total)) * 100, 2),
            "resource_utilization": round(utilization * 100, 2),
            "bench_by_skill": repo.bench_by_skill(),
            "skill_demand_trend": repo.skill_demand_trend(),
            "upcoming_project_demand": repo.upcoming_project_demand(),
        }

    def get_bench(self, db: Session) -> dict:
        repo = AnalyticsRepository(db)
        total = repo.employee_count()
        bench = repo.bench_count()
        return {
            "bench_count": bench,
            "bench_percentage": round((bench / max(1, total)) * 100, 2),
            "top_bench_skills": repo.bench_by_skill(),
        }

    def get_utilization(self, db: Session) -> dict:
        repo = AnalyticsRepository(db)
        return {
            "overall_utilization": round(repo.average_utilization() * 100, 2),
            "utilization_by_role": repo.utilization_by_role(),
            "historical_allocation_trend": repo.historical_allocation_trend(),
        }
