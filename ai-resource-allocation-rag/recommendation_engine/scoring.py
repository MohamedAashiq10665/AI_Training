from __future__ import annotations

from typing import Dict, List


WEIGHTS = {
    "skill_match": 0.40,
    "availability": 0.20,
    "certifications": 0.15,
    "experience": 0.15,
    "historical_performance": 0.10,
}


def _normalize(text: str) -> str:
    return text.strip().lower()


def compute_weighted_score(employee: Dict, project: Dict) -> Dict:
    required_skills = {_normalize(s) for s in project.get("required_skills", [])}
    employee_skills = {
        _normalize(employee.get("primary_skill", "")),
        _normalize(employee.get("secondary_skill", "")),
    }

    skill_hits = sorted(required_skills.intersection(employee_skills))
    missing_skills = sorted(required_skills.difference(employee_skills))
    skill_match = (len(skill_hits) / max(1, len(required_skills))) if required_skills else 0.0

    availability = 1.0 if employee.get("availability_status", "").lower() == "available" else 0.2

    preferred_certs = {_normalize(c) for c in project.get("preferred_certifications", [])}
    employee_certs = {
        _normalize(c)
        for c in str(employee.get("certifications", "")).split(";")
        if c.strip()
    }
    cert_match = (
        len(preferred_certs.intersection(employee_certs)) / max(1, len(preferred_certs))
        if preferred_certs
        else 0.0
    )

    min_exp = float(project.get("min_experience", 0))
    experience = min(1.0, float(employee.get("years_experience", 0)) / max(1.0, min_exp)) if min_exp else 1.0

    utilization = float(employee.get("current_utilization", 0.0))
    historical_performance = max(0.0, min(1.0, 1.0 - abs(0.75 - utilization)))

    score = (
        skill_match * WEIGHTS["skill_match"]
        + availability * WEIGHTS["availability"]
        + cert_match * WEIGHTS["certifications"]
        + experience * WEIGHTS["experience"]
        + historical_performance * WEIGHTS["historical_performance"]
    )

    upskilling = [f"Train on {s.title()}" for s in missing_skills]

    return {
        "match_score": round(score * 100, 2),
        "skills_matched": [s.title() for s in skill_hits],
        "missing_skills": [s.title() for s in missing_skills],
        "upskilling_suggestions": upskilling,
        "component_scores": {
            "skill_match": round(skill_match, 3),
            "availability": round(availability, 3),
            "certifications": round(cert_match, 3),
            "experience": round(experience, 3),
            "historical_performance": round(historical_performance, 3),
        },
    }
