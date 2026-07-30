from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from backend.repositories.employee_repository import EmployeeRepository
from rag.llm.ollama_client import OllamaClient
from rag.pipelines.employee_rag_pipeline import EmployeeRAGPipeline


class ChatService:
    def __init__(self):
        self.pipeline = EmployeeRAGPipeline()
        self.llm = OllamaClient()

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

    @staticmethod
    def _fallback_answer(candidates: list[dict]) -> str:
        if not candidates:
            return "No strong staffing candidates found from current context."

        top = candidates[:3]
        bullets = []
        for item in top:
            metadata = item.get("metadata", {})
            employee_id = metadata.get("employee_id")
            snippet = str(item.get("text", "")).replace("\n", " ").strip()[:120]
            bullets.append(f"{employee_id}: {snippet}")
        return "Quick staffing summary (fallback): " + " | ".join(bullets)

    def answer(self, db: Session, query: str, top_k: int = 5) -> dict:
        if not Path("data/employees.index").exists() or not Path("data/employees_meta.json").exists():
            employees = EmployeeRepository(db).all()
            records = [self._employee_to_dict(e) for e in employees]
            self.pipeline.build_index_from_records(records)

        candidates = self.pipeline.retrieve_candidates(query=query, top_k=top_k, availability_only=False)
        context = "\n".join(
            [
                f"Employee {c['metadata'].get('employee_id')}: {c['text'][:200]}"
                for c in candidates
            ]
        )
        prompt = (
            "You are a staffing assistant. Use only the given context."
            f"\nQuery: {query}\nContext:\n{context}\n"
            "Return concise recommendations with reasoning and skill gaps."
        )
        try:
            answer = self.llm.generate(prompt, timeout_seconds=12.0)
        except Exception:
            answer = self._fallback_answer(candidates)
        return {
            "answer": answer,
            "sources": [str(c["metadata"].get("employee_id")) for c in candidates],
        }
