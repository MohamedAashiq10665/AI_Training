from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from backend.models.schemas import RecommendationRequest
from backend.repositories.employee_repository import EmployeeRepository
from recommendation_engine.scoring import compute_weighted_score
from rag.pipelines.employee_rag_pipeline import EmployeeRAGPipeline


class RecommendationService:
    def __init__(self):
        self.rag_pipeline = EmployeeRAGPipeline()

    @staticmethod
    def _employee_to_dict(employee) -> dict:
        return {
            "employee_id": employee.employee_id,
            "name": employee.name,
            "primary_skill": employee.primary_skill,
            "secondary_skill": employee.secondary_skill,
            "years_experience": employee.years_experience,
            "certifications": employee.certifications,
            "availability_status": employee.availability_status,
            "current_utilization": employee.current_utilization,
            "location": employee.location,
            "role": employee.role,
            "resume_text": employee.resume_text,
        }

    def recommend(self, db: Session, request: RecommendationRequest) -> list[dict]:
        employees = EmployeeRepository(db).all()
        employee_records = [self._employee_to_dict(e) for e in employees]

        if not Path("data/employees.index").exists() or not Path("data/employees_meta.json").exists():
            self.rag_pipeline.build_index_from_records(employee_records)

        candidates = self.rag_pipeline.retrieve_candidates(
            query=f"{request.project_name} requiring {' '.join(request.required_skills)}",
            top_k=max(15, request.required_count * 5),
            availability_only=True,
        )

        employee_lookup = {str(row["employee_id"]): row for row in employee_records}
        scored = []
        for candidate in candidates:
            employee_id = str(candidate["metadata"].get("employee_id"))
            if employee_id not in employee_lookup:
                continue
            employee = employee_lookup[employee_id]
            result = compute_weighted_score(employee, request.model_dump())
            scored.append(
                {
                    "employee_id": employee_id,
                    "employee_name": employee["name"],
                    "match_score": result["match_score"],
                    "recommendation_reason": (
                        f"Strong fit with {', '.join(result['skills_matched']) or 'core project needs'} "
                        f"and utilization {employee['current_utilization']:.0%}."
                    ),
                    "skills_matched": result["skills_matched"],
                    "missing_skills": result["missing_skills"],
                    "availability": employee["availability_status"],
                    "upskilling_suggestions": result["upskilling_suggestions"],
                }
            )

        scored.sort(key=lambda x: x["match_score"], reverse=True)
        return scored[: request.required_count]
