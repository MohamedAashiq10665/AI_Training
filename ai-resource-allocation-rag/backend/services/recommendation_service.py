from __future__ import annotations

import json
import re
from pathlib import Path

from sqlalchemy.orm import Session

from backend.models.schemas import RecommendationRequest
from backend.repositories.employee_repository import EmployeeRepository
from backend.utils.config import settings
from recommendation_engine.scoring import compute_weighted_score
from rag.llm.ollama_client import OllamaClient
from rag.pipelines.employee_rag_pipeline import EmployeeRAGPipeline


class RecommendationService:
    def __init__(self):
        self.rag_pipeline = EmployeeRAGPipeline()
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
    def _fallback_reason(employee: dict, result: dict) -> str:
        return (
            f"Strong fit with {', '.join(result['skills_matched']) or 'core project needs'} "
            f"and utilization {float(employee['current_utilization'] or 0.0):.0%}."
        )

    @staticmethod
    def _normalize_strategy(value: str | None) -> str:
        normalized = str(value or "").strip().lower()
        if normalized in {"zero-shot", "zeroshot", "zero_shot"}:
            return "zero_shot"
        if normalized in {"few-shot", "fewshot", "few_shot"}:
            return "few_shot"
        if normalized in {"chain-of-thought", "cot", "chain_of_thought"}:
            return "chain_of_thought"
        if normalized == "auto":
            return "auto"
        return "few_shot"

    def _build_reason_prompt(
        self,
        request: RecommendationRequest,
        employee: dict,
        result: dict,
        strategy: str,
    ) -> str:
        base_context = (
            f"Project: {request.project_name}"
            f"\nRequired skills: {', '.join(request.required_skills) or 'None'}"
            f"\nPreferred certifications: {', '.join(request.preferred_certifications) or 'None'}"
            f"\nMinimum experience: {request.min_experience}"
            f"\nCandidate: {employee['name']} ({employee['employee_id']})"
            f"\nCandidate primary skill: {employee['primary_skill']}"
            f"\nCandidate secondary skill: {employee['secondary_skill']}"
            f"\nCandidate certifications: {employee['certifications'] or 'None'}"
            f"\nCandidate experience: {employee['years_experience']}"
            f"\nCandidate utilization: {float(employee['current_utilization'] or 0.0):.2f}"
            f"\nMatched skills: {', '.join(result['skills_matched']) or 'None'}"
            f"\nMissing skills: {', '.join(result['missing_skills']) or 'None'}"
        )

        if strategy == "zero_shot":
            return (
                "You are a staffing recommendation assistant. "
                "Write one concise recommendation sentence for this candidate. "
                "Mention skill fit, experience alignment, certification alignment, and utilization readiness. "
                "Do not invent skills or certifications. Keep response under 40 words."
                f"\n{base_context}"
            )

        if strategy == "few_shot":
            return (
                "You are a staffing recommendation assistant. Generate exactly one recommendation sentence. "
                "Keep it factual and under 40 words."
                "\nExample 1"
                "\nInput: Matched skills: Python, Azure | Candidate experience: 9 | Minimum experience: 5 | "
                "Candidate certifications: AWS-SA;Azure-AZ900 | Candidate utilization: 0.22"
                "\nOutput: Strong match for Python/Azure, exceeds the 5-year experience threshold, holds Azure-AZ900, "
                "and is lightly utilized at 22% for near-term allocation."
                "\nExample 2"
                "\nInput: Matched skills: React | Missing skills: Node.js | Candidate experience: 3 | Minimum experience: 4 | "
                "Candidate certifications: ScrumMaster | Candidate utilization: 0.78"
                "\nOutput: Good React alignment but below the 4-year experience target and missing Node.js; "
                "utilization at 78% suggests moderate ramp-up risk."
                f"\nNow generate output for:\n{base_context}"
            )

        return (
            "You are a staffing recommendation assistant. "
            "Think step-by-step internally using this checklist: skills, experience, certifications, utilization. "
            "Do not output the reasoning steps. Output only one final sentence under 40 words."
            f"\n{base_context}"
        )

    @staticmethod
    def _score_reason_quality(reason: str, employee: dict, request: RecommendationRequest, result: dict) -> int:
        text = str(reason or "").lower()
        score = 0
        if any(skill.lower() in text for skill in result.get("skills_matched", [])):
            score += 1
        if "experience" in text or str(employee.get("years_experience", "")) in text:
            score += 1
        if "utilization" in text or "%" in text:
            score += 1
        preferred = [c.lower() for c in request.preferred_certifications if c]
        if not preferred or any(cert in text for cert in preferred):
            score += 1
        return score

    def _llm_reason(self, request: RecommendationRequest, employee: dict, result: dict) -> str:
        strategy = self._normalize_strategy(settings.recommendation_prompt_strategy)
        strategies = [strategy] if strategy != "auto" else ["zero_shot", "few_shot", "chain_of_thought"]

        best_reason = ""
        best_score = -1
        for item in strategies:
            prompt = self._build_reason_prompt(request, employee, result, item)
            reason = self.llm.generate(prompt, timeout_seconds=15.0).strip()
            if not reason:
                continue
            quality = self._score_reason_quality(reason, employee, request, result)
            if quality > best_score:
                best_score = quality
                best_reason = reason

        if not best_reason:
            return self._fallback_reason(employee, result)
        return best_reason

    @staticmethod
    def _safe_float(value, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _parse_llm_rerank_response(raw_response: str) -> dict[str, float]:
        text = str(raw_response or "").strip()
        if not text:
            return {}

        # Prefer the first JSON array in case the model adds prose around it.
        match = re.search(r"\[[\s\S]*\]", text)
        json_text = match.group(0) if match else text
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError:
            return {}

        if not isinstance(payload, list):
            return {}

        scores: dict[str, float] = {}
        for item in payload:
            if not isinstance(item, dict):
                continue
            employee_id = str(item.get("employee_id", "")).strip()
            if not employee_id:
                continue
            llm_score = RecommendationService._safe_float(item.get("llm_score"), default=-1.0)
            if llm_score < 0:
                continue
            scores[employee_id] = max(0.0, min(100.0, llm_score))
        return scores

    def _llm_rerank_candidates(self, request: RecommendationRequest, candidates: list[dict]) -> dict[str, float]:
        if not candidates:
            return {}

        candidate_lines = []
        for idx, item in enumerate(candidates, start=1):
            candidate_lines.append(
                (
                    f"{idx}. employee_id={item['employee_id']}; "
                    f"name={item['employee_name']}; "
                    f"base_match_score={item['match_score']}; "
                    f"skills_matched={', '.join(item.get('skills_matched', [])) or 'None'}; "
                    f"missing_skills={', '.join(item.get('missing_skills', [])) or 'None'}; "
                    f"availability={item.get('availability', 'Unknown')}; "
                    f"experience_fit={self._safe_float(item.get('component_scores', {}).get('experience')):.3f}; "
                    f"certification_fit={self._safe_float(item.get('component_scores', {}).get('certifications')):.3f}"
                )
            )

        prompt = (
            "You are a staffing ranking model. Score each candidate from 0 to 100 for this request. "
            "Higher means better fit for allocation priority. Use only provided facts. "
            "Return ONLY a JSON array. No markdown, no commentary. "
            "Each JSON item must be: {\"employee_id\": \"...\", \"llm_score\": number}."
            f"\nProject: {request.project_name}"
            f"\nRequired skills: {', '.join(request.required_skills) or 'None'}"
            f"\nPreferred certifications: {', '.join(request.preferred_certifications) or 'None'}"
            f"\nMinimum experience: {request.min_experience}"
            "\nCandidates:"
            f"\n{chr(10).join(candidate_lines)}"
        )

        raw_response = self.llm.generate(prompt, timeout_seconds=20.0)
        return self._parse_llm_rerank_response(raw_response)

    def recommend(
        self,
        db: Session,
        request: RecommendationRequest,
        use_llm_reasons: bool = True,
        use_llm_rerank: bool | None = None,
    ) -> list[dict]:
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

            recommendation_reason = self._fallback_reason(employee, result)
            if use_llm_reasons:
                try:
                    recommendation_reason = self._llm_reason(request, employee, result)
                except Exception:
                    recommendation_reason = self._fallback_reason(employee, result)

            scored.append(
                {
                    "employee_id": employee_id,
                    "employee_name": employee["name"],
                    "match_score": result["match_score"],
                    "base_match_score": result["match_score"],
                    "llm_score": None,
                    "final_score": result["match_score"],
                    "recommendation_reason": recommendation_reason,
                    "skills_matched": result["skills_matched"],
                    "missing_skills": result["missing_skills"],
                    "availability": employee["availability_status"],
                    "upskilling_suggestions": result["upskilling_suggestions"],
                    "component_scores": result["component_scores"],
                }
            )

        should_rerank = settings.recommendation_llm_rerank_enabled if use_llm_rerank is None else use_llm_rerank
        if should_rerank and scored:
            alpha = max(0.0, min(1.0, self._safe_float(settings.recommendation_llm_rerank_alpha, default=0.7)))
            rerank_top_n = max(1, int(settings.recommendation_llm_rerank_top_n or 20))
            preselected = sorted(scored, key=lambda x: x["match_score"], reverse=True)[: max(request.required_count, rerank_top_n)]
            try:
                llm_scores = self._llm_rerank_candidates(request, preselected)
                for item in scored:
                    employee_id = str(item.get("employee_id", ""))
                    if employee_id not in llm_scores:
                        continue
                    llm_score = round(self._safe_float(llm_scores[employee_id]), 2)
                    base_score = self._safe_float(item.get("base_match_score"), default=self._safe_float(item.get("match_score")))
                    final_score = round(alpha * base_score + (1.0 - alpha) * llm_score, 2)
                    item["llm_score"] = llm_score
                    item["final_score"] = final_score
                    item["match_score"] = final_score
            except Exception:
                pass

        scored.sort(key=lambda x: x["match_score"], reverse=True)
        return scored[: request.required_count]
