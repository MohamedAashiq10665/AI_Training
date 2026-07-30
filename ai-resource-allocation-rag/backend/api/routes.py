import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4

from backend.api.deps import require_roles
from backend.database.models import Employee, HistoricalAllocation, Project
from backend.database.session import get_db
from backend.models.schemas import (
    ChatRequest,
    ChatResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from backend.services.analytics_service import AnalyticsService
from backend.services.chat_service import ChatService
from backend.services.recommendation_service import RecommendationService
from backend.repositories.employee_repository import EmployeeRepository

router = APIRouter()

recommendation_service = RecommendationService()
analytics_service = AnalyticsService()
chat_service = ChatService()
intent_assign_proposals: dict[str, dict] = {}


SUPPORTED_CHAT_REASON = (
    "This chat recommendation is supported only for workforce staffing and allocation use cases "
    "(skills, experience, availability, utilization, bench, assignment/unassignment, and project allocation decisions). "
    "Other topics are not supported."
)

SUPPORTED_RECOMMENDATION_REASON = (
    "AI staffing recommendations require skills input as either comma-separated skills "
    "(for example: Python, Azure, React) or a staffing sentence "
    "(for example: Suggest 2 Azure engineers with minimum 3 years experience)."
)

SKILL_TEXT_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9 .#+&/_-]{0,39}$"
INVALID_SKILL_TERMS = {
    "hi",
    "hello",
    "hey",
    "happy",
    "birthday",
    "thanks",
    "thank",
    "who",
    "what",
    "when",
    "where",
    "why",
    "how",
    "please",
    "find",
    "show",
    "give",
    "tell",
    "recommend",
    "suggest",
    "need",
    "want",
    "employee",
    "employees",
    "project",
    "projects",
    "allocation",
    "utilization",
    "bench",
    "staffing",
}

INTENT_SKILL_ALIASES = {
    "python": "Python",
    "azure": "Azure",
    "react": "React",
    "data engineering": "Data Engineering",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "java": "Java",
    "aws": "AWS",
    "gcp": "GCP",
    "sql": "SQL",
    "devops": "DevOps",
    "fastapi": "FastAPI",
    "kubernetes": "Kubernetes",
    "terraform": "Terraform",
    "spark": "Spark",
    "docker": "Docker",
    "spring": "Spring",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "power bi": "Power BI",
}

INTENT_LOCATIONS = {
    "remote": "Remote",
    "cairo": "Cairo",
    "dubai": "Dubai",
    "riyadh": "Riyadh",
    "london": "London",
    "bangalore": "Bangalore",
}

INTENT_DOMAINS = {
    "healthcare": "Healthcare",
    "finance": "Finance",
    "retail": "Retail",
    "public sector": "Public Sector",
    "telecom": "Telecom",
}


def _ensure_staffing_query(query: str | None) -> None:
    normalized = str(query or "").strip().lower()
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SUPPORTED_CHAT_REASON)

    staffing_keywords = {
        "employee",
        "employees",
        "resource",
        "resources",
        "staff",
        "staffing",
        "allocation",
        "allocate",
        "unassign",
        "assign",
        "project",
        "projects",
        "skill",
        "skills",
        "availability",
        "utilization",
        "bench",
        "candidate",
        "candidates",
        "role",
        "roles",
        "experience",
    }
    if not any(keyword in normalized for keyword in staffing_keywords):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SUPPORTED_CHAT_REASON)


def _parse_multi_value_text(value: str | None) -> list[str]:
    if not value:
        return []
    return [chunk.strip() for chunk in value.replace(",", ";").split(";") if chunk.strip()]


def _refresh_employee_rag_index(db: Session) -> None:
    employee_records = [
        {
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
        for employee in EmployeeRepository(db).all()
    ]
    recommendation_service.rag_pipeline.build_index_from_records(employee_records)


def _ensure_skill_list(skills: list[str] | None) -> None:
    normalized_skills = [str(skill or "").strip() for skill in skills or [] if str(skill or "").strip()]
    if not normalized_skills:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SUPPORTED_RECOMMENDATION_REASON)

    for skill in normalized_skills:
        skill_terms = [term for term in skill.lower().replace("/", " ").replace("-", " ").split() if term]
        if len(skill_terms) > 4:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SUPPORTED_RECOMMENDATION_REASON)
        if any(term in INVALID_SKILL_TERMS for term in skill_terms):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SUPPORTED_RECOMMENDATION_REASON)
        if not re.fullmatch(SKILL_TEXT_PATTERN, skill):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SUPPORTED_RECOMMENDATION_REASON)


def _extract_intent_skills(text: str) -> list[str]:
    normalized = " ".join(str(text or "").lower().split())
    found: list[str] = []
    for alias, canonical in INTENT_SKILL_ALIASES.items():
        if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", normalized) and canonical not in found:
            found.append(canonical)
    return found


def _parse_recommendation_intent(request: RecommendationRequest) -> RecommendationRequest:
    raw_prompt = ""
    if len(request.required_skills) == 1:
        raw_prompt = str(request.required_skills[0] or "").strip()

    if not raw_prompt:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SUPPORTED_RECOMMENDATION_REASON)

    normalized = " ".join(raw_prompt.lower().split())
    skills = _extract_intent_skills(normalized)
    if not skills:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SUPPORTED_RECOMMENDATION_REASON)

    def _extract_first_int(match: re.Match[str] | None) -> int | None:
        if not match:
            return None
        number_match = re.search(r"\d{1,2}", match.group(0))
        if not number_match:
            return None
        return int(number_match.group(0))

    requested_count = request.required_count
    count_match = re.search(r"\b(assign|allocate|need|require|staff|find|recommend|suggest)\s+(\d{1,2})\b", normalized)
    if not count_match:
        count_match = re.search(r"\b(\d{1,2})\s+(engineers?|developers?|resources?|people|staff|candidates?)\b", normalized)
    if not count_match:
        count_match = re.search(
            r"\b(\d{1,2})\s+(?:[a-z0-9.+#&/_-]+\s+){0,4}(engineers?|developers?|resources?|people|staff|candidates?)\b",
            normalized,
        )
    parsed_count = _extract_first_int(count_match)
    if parsed_count is not None:
        requested_count = max(1, parsed_count)

    min_experience = request.min_experience
    experience_match = re.search(r"\b(min(?:imum)?|at least)\s+(\d{1,2})\s*(years?|yrs?)\b", normalized)
    if not experience_match:
        experience_match = re.search(r"\b(\d{1,2})\+?\s*(years?|yrs?)\s+(experience|exp)\b", normalized)
    parsed_experience = _extract_first_int(experience_match)
    if parsed_experience is not None:
        min_experience = max(0, min(40, parsed_experience))

    location = request.location
    for token, canonical in INTENT_LOCATIONS.items():
        if re.search(rf"(?<!\w){re.escape(token)}(?!\w)", normalized):
            location = canonical
            break

    domain = request.domain
    for token, canonical in INTENT_DOMAINS.items():
        if re.search(rf"(?<!\w){re.escape(token)}(?!\w)", normalized):
            domain = canonical
            break

    project_name = request.project_name or "Intent Driven Staffing Request"
    return RecommendationRequest(
        project_name=project_name,
        required_skills=skills,
        preferred_certifications=request.preferred_certifications,
        min_experience=min_experience,
        required_count=requested_count,
        location=location,
        domain=domain,
    )


def _is_truthy_confirmation(value) -> bool:
    normalized = str(value or "").strip().lower()
    return normalized in {"1", "true", "yes", "y", "ok", "confirm", "approved"}


@router.post("/recommend", response_model=RecommendationResponse)
def recommend(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "manager"])),
) -> RecommendationResponse:
    normalized_request = request
    try:
        _ensure_skill_list(request.required_skills)
    except HTTPException:
        normalized_request = _parse_recommendation_intent(request)

    recommendations = recommendation_service.recommend(
        db,
        normalized_request,
        use_llm_reasons=True,
        use_llm_rerank=True,
    )

    recommendation_ids = [str(item.get("employee_id", "")).strip() for item in recommendations if item.get("employee_id")]
    employee_rows = db.query(Employee).filter(Employee.employee_id.in_(recommendation_ids)).all() if recommendation_ids else []
    employee_map = {str(row.employee_id): row for row in employee_rows}

    latest_alloc_subquery = (
        db.query(
            HistoricalAllocation.employee_id.label("employee_id"),
            func.max(HistoricalAllocation.allocation_month).label("latest_month"),
        )
        .group_by(HistoricalAllocation.employee_id)
        .subquery()
    )
    latest_alloc_rows = (
        db.query(
            HistoricalAllocation.employee_id,
            Project.project_name,
            Project.domain,
        )
        .join(
            latest_alloc_subquery,
            (HistoricalAllocation.employee_id == latest_alloc_subquery.c.employee_id)
            & (HistoricalAllocation.allocation_month == latest_alloc_subquery.c.latest_month),
        )
        .join(Project, Project.project_id == HistoricalAllocation.project_id)
        .filter(HistoricalAllocation.employee_id.in_(recommendation_ids))
        .all()
        if recommendation_ids
        else []
    )
    latest_project_by_employee = {
        str(row.employee_id): {
            "latest_project_name": row.project_name,
            "latest_project_domain": row.domain,
        }
        for row in latest_alloc_rows
    }

    for item in recommendations:
        employee_id = str(item.get("employee_id", "")).strip()
        employee = employee_map.get(employee_id)
        if not employee:
            continue
        item["role"] = employee.role
        item["primary_skill"] = employee.primary_skill
        item["secondary_skill"] = employee.secondary_skill
        item["years_experience"] = int(employee.years_experience or 0)
        item["certifications"] = employee.certifications
        item["latest_project_name"] = latest_project_by_employee.get(employee_id, {}).get("latest_project_name")
        item["latest_project_domain"] = latest_project_by_employee.get(employee_id, {}).get("latest_project_domain")

    requested_count = int(normalized_request.required_count or 0)
    returned_count = len(recommendations)
    retrieval_notice = None
    if requested_count > 0 and returned_count < requested_count:
        retrieval_notice = (
            f"Only {returned_count} recommendation(s) were retrieved. "
            f"We could not find enough candidates to satisfy the requested {requested_count}."
        )

    return RecommendationResponse(
        project_name=normalized_request.project_name,
        recommendations=recommendations,
        requested_count=requested_count,
        returned_count=returned_count,
        retrieval_notice=retrieval_notice,
    )


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "manager", "viewer"])),
) -> ChatResponse:
    _ensure_staffing_query(request.query)
    result = chat_service.answer(db, request.query, top_k=request.top_k)
    return ChatResponse(**result)


@router.get("/employees")
def get_employees(
    limit: int = 500,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "manager", "viewer"])),
):
    employees = EmployeeRepository(db).list(limit=limit)

    latest_alloc_subquery = (
        db.query(
            HistoricalAllocation.employee_id.label("employee_id"),
            func.max(HistoricalAllocation.allocation_month).label("latest_month"),
        )
        .group_by(HistoricalAllocation.employee_id)
        .subquery()
    )

    latest_alloc_rows = (
        db.query(
            HistoricalAllocation.employee_id,
            Project.project_name,
            Project.domain,
        )
        .join(
            latest_alloc_subquery,
            (HistoricalAllocation.employee_id == latest_alloc_subquery.c.employee_id)
            & (HistoricalAllocation.allocation_month == latest_alloc_subquery.c.latest_month),
        )
        .join(Project, Project.project_id == HistoricalAllocation.project_id)
        .all()
    )

    latest_project_by_employee = {
        str(row.employee_id): {
            "latest_project_name": row.project_name,
            "latest_project_domain": row.domain,
        }
        for row in latest_alloc_rows
    }

    return [
        {
            "employee_id": e.employee_id,
            "name": e.name,
            "primary_skill": e.primary_skill,
            "secondary_skill": e.secondary_skill,
            "years_experience": e.years_experience,
            "certifications": e.certifications,
            "availability_status": e.availability_status,
            "current_utilization": e.current_utilization,
            "location": e.location,
            "role": e.role,
            "resume_text": e.resume_text,
            "latest_project_name": latest_project_by_employee.get(str(e.employee_id), {}).get("latest_project_name"),
            "latest_project_domain": latest_project_by_employee.get(str(e.employee_id), {}).get("latest_project_domain"),
        }
        for e in employees
    ]


@router.get("/project-teams")
def get_project_teams(
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "manager", "viewer"])),
):
    latest_month = db.query(func.max(HistoricalAllocation.allocation_month)).scalar()
    if not latest_month:
        return []

    rows = (
        db.query(
            Project.project_id,
            Project.project_name,
            Project.domain,
            Project.location,
            Employee.employee_id,
            Employee.name,
            Employee.primary_skill,
            Employee.role,
            HistoricalAllocation.allocation_percentage,
        )
        .join(HistoricalAllocation, HistoricalAllocation.project_id == Project.project_id)
        .join(Employee, Employee.employee_id == HistoricalAllocation.employee_id)
        .filter(HistoricalAllocation.allocation_month == latest_month)
        .order_by(Project.project_name.asc(), Employee.name.asc())
        .all()
    )

    project_map = {}
    for row in rows:
        project_key = str(row.project_id)
        if project_key not in project_map:
            project_map[project_key] = {
                "project_id": str(row.project_id),
                "project_name": row.project_name,
                "domain": row.domain,
                "location": row.location,
                "allocation_month": latest_month,
                "members": [],
            }

        project_map[project_key]["members"].append(
            {
                "employee_id": str(row.employee_id),
                "name": row.name,
                "primary_skill": row.primary_skill,
                "role": row.role,
                "allocation_percentage": row.allocation_percentage,
            }
        )

    return list(project_map.values())


@router.get("/projects")
def get_projects(
    limit: int = 500,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "manager", "viewer"])),
):
    projects = db.query(Project).order_by(Project.project_name.asc()).limit(limit).all()

    latest_month = db.query(func.max(HistoricalAllocation.allocation_month)).scalar()
    allocation_counts: dict[str, int] = {}
    if latest_month:
        rows = (
            db.query(HistoricalAllocation.project_id, func.count(HistoricalAllocation.employee_id))
            .filter(HistoricalAllocation.allocation_month == latest_month)
            .group_by(HistoricalAllocation.project_id)
            .all()
        )
        allocation_counts = {str(project_id): int(count) for project_id, count in rows}

    return [
        {
            "project_id": p.project_id,
            "project_name": p.project_name,
            "required_skills": _parse_multi_value_text(p.required_skills),
            "preferred_certifications": _parse_multi_value_text(p.preferred_certifications),
            "min_experience": p.min_experience,
            "required_headcount": p.required_headcount,
            "location": p.location,
            "domain": p.domain,
            "allocated_count": allocation_counts.get(str(p.project_id), 0),
            "allocation_month": latest_month,
        }
        for p in projects
    ]


@router.get("/projects/{project_id}/details")
def get_project_details(
    project_id: str,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "manager", "viewer"])),
):
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        return {"detail": "Project not found"}

    latest_month = db.query(func.max(HistoricalAllocation.allocation_month)).scalar()

    allocated_rows = []
    allocated_employee_ids: set[str] = set()
    if latest_month:
        allocated_rows = (
            db.query(
                Employee.employee_id,
                Employee.name,
                Employee.primary_skill,
                Employee.secondary_skill,
                Employee.years_experience,
                Employee.role,
                Employee.current_utilization,
                HistoricalAllocation.allocation_percentage,
            )
            .join(HistoricalAllocation, HistoricalAllocation.employee_id == Employee.employee_id)
            .filter(
                HistoricalAllocation.project_id == project_id,
                HistoricalAllocation.allocation_month == latest_month,
            )
            .order_by(Employee.name.asc())
            .all()
        )
        allocated_employee_ids = {str(row.employee_id) for row in allocated_rows}

    required_skills = {skill.lower() for skill in _parse_multi_value_text(project.required_skills)}
    min_experience = int(project.min_experience or 0)

    recommendation_request = RecommendationRequest(
        project_name=project.project_name,
        required_skills=sorted(required_skills),
        preferred_certifications=_parse_multi_value_text(project.preferred_certifications),
        min_experience=min_experience,
        required_count=max(10, int(project.required_headcount or 1) * 3),
        location=project.location,
        domain=project.domain,
    )
    ai_recommendations = recommendation_service.recommend(db, recommendation_request, use_llm_reasons=False)

    candidate_ids = [str(item.get("employee_id")) for item in ai_recommendations if item.get("employee_id")]
    candidate_rows = db.query(Employee).filter(Employee.employee_id.in_(candidate_ids)).all() if candidate_ids else []
    employee_map = {str(employee.employee_id): employee for employee in candidate_rows}

    fit_candidates = []
    for item in ai_recommendations:
        employee_id = str(item.get("employee_id", "")).strip()
        if not employee_id or employee_id in allocated_employee_ids:
            continue
        employee = employee_map.get(employee_id)
        if not employee:
            continue

        fit_candidates.append(
            {
                "employee_id": employee.employee_id,
                "name": employee.name,
                "primary_skill": employee.primary_skill,
                "secondary_skill": employee.secondary_skill,
                "years_experience": employee.years_experience,
                "current_utilization": employee.current_utilization,
                "role": employee.role,
                "matched_skills": item.get("skills_matched", []),
                "match_score": item.get("match_score"),
                "recommendation_reason": item.get("recommendation_reason"),
                "missing_skills": item.get("missing_skills", []),
            }
        )

    return {
        "project": {
            "project_id": project.project_id,
            "project_name": project.project_name,
            "required_skills": sorted(required_skills),
            "preferred_certifications": _parse_multi_value_text(project.preferred_certifications),
            "min_experience": project.min_experience,
            "required_headcount": project.required_headcount,
            "location": project.location,
            "domain": project.domain,
            "allocation_month": latest_month,
        },
        "allocated_members": [
            {
                "employee_id": row.employee_id,
                "name": row.name,
                "primary_skill": row.primary_skill,
                "secondary_skill": row.secondary_skill,
                "years_experience": row.years_experience,
                "role": row.role,
                "current_utilization": row.current_utilization,
                "allocation_percentage": row.allocation_percentage,
            }
            for row in allocated_rows
        ],
        "fit_candidates": fit_candidates,
    }


@router.post("/projects/{project_id}/assign")
def assign_employee_to_project(
    project_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "manager"])),
):
    employee_id = str(payload.get("employee_id", "")).strip()
    allocation_percentage = int(payload.get("allocation_percentage", 100))
    if not employee_id:
        return {"detail": "employee_id is required"}

    project = db.query(Project).filter(Project.project_id == project_id).first()
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not project or not employee:
        return {"detail": "Project or employee not found"}

    allocation_month = db.query(func.max(HistoricalAllocation.allocation_month)).scalar()
    if not allocation_month:
        allocation_month = datetime.utcnow().strftime("%Y-%m")

    existing = (
        db.query(HistoricalAllocation)
        .filter(
            HistoricalAllocation.project_id == project_id,
            HistoricalAllocation.employee_id == employee_id,
            HistoricalAllocation.allocation_month == allocation_month,
        )
        .first()
    )
    if existing:
        return {"status": "exists", "detail": "Employee is already allocated to this project"}

    allocation = HistoricalAllocation(
        allocation_id=f"AL{uuid4().hex[:10].upper()}",
        employee_id=employee_id,
        project_id=project_id,
        allocation_month=allocation_month,
        allocation_percentage=max(1, min(allocation_percentage, 100)),
        performance_rating=3.5,
    )
    db.add(allocation)

    employee.availability_status = "Allocated"
    employee.current_utilization = max(
        float(employee.current_utilization or 0.0),
        round(max(1, min(allocation_percentage, 100)) / 100, 2),
    )

    db.commit()
    _refresh_employee_rag_index(db)

    return {
        "status": "assigned",
        "project_id": project_id,
        "employee_id": employee_id,
        "allocation_month": allocation_month,
        "allocation_percentage": max(1, min(allocation_percentage, 100)),
    }


@router.post("/projects/{project_id}/unassign")
def unassign_employee_from_project(
    project_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "manager"])),
):
    employee_id = str(payload.get("employee_id", "")).strip()
    if not employee_id:
        return {"detail": "employee_id is required"}

    project = db.query(Project).filter(Project.project_id == project_id).first()
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not project or not employee:
        return {"detail": "Project or employee not found"}

    employee_latest_month = (
        db.query(func.max(HistoricalAllocation.allocation_month))
        .filter(
            HistoricalAllocation.project_id == project_id,
            HistoricalAllocation.employee_id == employee_id,
        )
        .scalar()
    )
    if not employee_latest_month:
        return {
            "status": "not_allocated",
            "detail": "Employee is not currently allocated to this project",
            "project_id": project_id,
            "employee_id": employee_id,
        }

    allocation = (
        db.query(HistoricalAllocation)
        .filter(
            HistoricalAllocation.project_id == project_id,
            HistoricalAllocation.employee_id == employee_id,
            HistoricalAllocation.allocation_month == employee_latest_month,
        )
        .first()
    )
    if not allocation:
        return {
            "status": "not_allocated",
            "detail": "Employee is not currently allocated to this project",
            "project_id": project_id,
            "employee_id": employee_id,
        }

    db.delete(allocation)

    global_latest_month = db.query(func.max(HistoricalAllocation.allocation_month)).scalar()
    remaining_rows = []
    if global_latest_month:
        remaining_rows = (
            db.query(HistoricalAllocation.allocation_percentage)
            .filter(
                HistoricalAllocation.employee_id == employee_id,
                HistoricalAllocation.allocation_month == global_latest_month,
            )
            .all()
        )

    if remaining_rows:
        total_utilization = min(1.0, sum(int(row[0] or 0) for row in remaining_rows) / 100)
        employee.availability_status = "Allocated"
        employee.current_utilization = round(total_utilization, 2)
    else:
        employee.availability_status = "Available"
        employee.current_utilization = 0.0

    db.commit()
    _refresh_employee_rag_index(db)

    return {
        "status": "unassigned",
        "project_id": project_id,
        "employee_id": employee_id,
        "allocation_month": employee_latest_month,
    }


@router.post("/projects/{project_id}/intent-driver/propose")
def propose_intent_assignment(
    project_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "manager"])),
):
    prompt = str(payload.get("query", "")).strip()
    if not prompt:
        return {"detail": "query is required"}
    _ensure_staffing_query(prompt)

    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        return {"detail": "Project not found"}

    latest_month = db.query(func.max(HistoricalAllocation.allocation_month)).scalar()
    allocated_count = 0
    if latest_month:
        allocated_count = int(
            db.query(func.count(HistoricalAllocation.employee_id))
            .filter(
                HistoricalAllocation.project_id == project_id,
                HistoricalAllocation.allocation_month == latest_month,
            )
            .scalar()
            or 0
        )

    project_required_skills = _parse_multi_value_text(project.required_skills)
    project_required_skills_lower = {skill.lower() for skill in project_required_skills}
    preferred_certs = _parse_multi_value_text(project.preferred_certifications)
    min_experience = int(project.min_experience or 0)
    required_headcount = int(project.required_headcount or 1)
    open_slots = max(0, required_headcount - allocated_count)
    default_count = max(1, open_slots or required_headcount)

    parsed_intent = None
    try:
        parsed_intent = _parse_recommendation_intent(
            RecommendationRequest(
                project_name=project.project_name,
                required_skills=[prompt],
                preferred_certifications=preferred_certs,
                min_experience=min_experience,
                required_count=default_count,
                location=project.location,
                domain=project.domain,
            )
        )
    except HTTPException:
        parsed_intent = None

    merged_skills = list(project_required_skills)
    if parsed_intent:
        for skill in parsed_intent.required_skills:
            if skill.lower() not in project_required_skills_lower:
                merged_skills.append(skill)

    if not merged_skills:
        return {"detail": "No project skills found and no parseable skills in prompt."}

    effective_min_experience = max(min_experience, int(parsed_intent.min_experience or 0) if parsed_intent else 0)
    effective_required_count = int(parsed_intent.required_count or default_count) if parsed_intent else default_count
    effective_required_count = max(1, min(20, effective_required_count))
    if open_slots > 0:
        effective_required_count = min(effective_required_count, open_slots)

    recommendation_request = RecommendationRequest(
        project_name=project.project_name,
        required_skills=merged_skills,
        preferred_certifications=preferred_certs,
        min_experience=effective_min_experience,
        required_count=effective_required_count,
        location=project.location,
        domain=project.domain,
    )
    suggestions = recommendation_service.recommend(db, recommendation_request, use_llm_reasons=True)

    skill_matched_count = len([item for item in suggestions if len(item.get("missing_skills", [])) == 0])
    experience_matched_count = len([item for item in suggestions if float(item.get("component_scores", {}).get("experience", 0)) >= 1.0])
    cert_matched_count = len([item for item in suggestions if float(item.get("component_scores", {}).get("certifications", 0)) > 0])
    availability_matched_count = len([item for item in suggestions if float(item.get("component_scores", {}).get("availability", 0)) >= 1.0])

    proposal_id = f"IPR-{uuid4().hex[:10].upper()}"
    allocation_percentage = int(payload.get("allocation_percentage", 100) or 100)
    allocation_percentage = max(1, min(100, allocation_percentage))
    intent_assign_proposals[proposal_id] = {
        "project_id": project_id,
        "employee_ids": [str(item.get("employee_id")) for item in suggestions if item.get("employee_id")],
        "allocation_percentage": allocation_percentage,
        "created_at": datetime.utcnow().isoformat(),
        "query": prompt,
        "criteria": {
            "required_skills": merged_skills,
            "min_experience": effective_min_experience,
            "required_count": effective_required_count,
            "location": project.location,
            "domain": project.domain,
        },
    }

    return {
        "proposal_id": proposal_id,
        "message": "Intent proposal created. Review suggested employees and confirm to assign.",
        "project": {
            "project_id": project.project_id,
            "project_name": project.project_name,
            "required_headcount": required_headcount,
            "allocated_count": allocated_count,
            "open_slots": open_slots,
        },
        "normalized_criteria": intent_assign_proposals[proposal_id]["criteria"],
        "validation_summary": {
            "suggested_count": len(suggestions),
            "skill_matched_count": skill_matched_count,
            "experience_matched_count": experience_matched_count,
            "certification_matched_count": cert_matched_count,
            "availability_matched_count": availability_matched_count,
        },
        "suggestions": suggestions,
    }


@router.post("/projects/{project_id}/intent-driver/confirm")
def confirm_intent_assignment(
    project_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "manager"])),
):
    proposal_id = str(payload.get("proposal_id", "")).strip()
    if not proposal_id:
        return {"detail": "proposal_id is required"}

    proposal = intent_assign_proposals.get(proposal_id)
    if not proposal:
        return {"detail": "Proposal not found or expired"}
    if str(proposal.get("project_id")) != str(project_id):
        return {"detail": "Proposal does not belong to this project"}

    decision = payload.get("confirm", payload.get("decision", ""))
    if not _is_truthy_confirmation(decision):
        intent_assign_proposals.pop(proposal_id, None)
        return {
            "status": "cancelled",
            "project_id": project_id,
            "proposal_id": proposal_id,
            "detail": "Assignment cancelled by user decision.",
        }

    assigned = []
    already_allocated = []
    failed = []

    for employee_id in proposal.get("employee_ids", []):
        try:
            result = assign_employee_to_project(
                project_id=project_id,
                payload={
                    "employee_id": employee_id,
                    "allocation_percentage": proposal.get("allocation_percentage", 100),
                },
                db=db,
                user=user,
            )
            if result.get("status") == "assigned":
                assigned.append(employee_id)
            elif result.get("status") == "exists":
                already_allocated.append(employee_id)
            else:
                failed.append({"employee_id": employee_id, "detail": result.get("detail", "Unknown status")})
        except Exception as exc:
            failed.append({"employee_id": employee_id, "detail": str(exc)})

    intent_assign_proposals.pop(proposal_id, None)

    return {
        "status": "completed",
        "project_id": project_id,
        "proposal_id": proposal_id,
        "assigned_count": len(assigned),
        "already_allocated_count": len(already_allocated),
        "failed_count": len(failed),
        "assigned_employee_ids": assigned,
        "already_allocated_employee_ids": already_allocated,
        "failed": failed,
    }


@router.post("/projects/{project_id}/ai-recommend-chat")
def project_ai_recommend_chat(
    project_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "manager", "viewer"])),
):
    top_k = int(payload.get("top_k", 5) or 5)
    top_k = max(1, min(top_k, 10))
    query = str(payload.get("query", "")).strip()
    if query:
        _ensure_staffing_query(query)

    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        return {"detail": "Project not found"}

    latest_month = db.query(func.max(HistoricalAllocation.allocation_month)).scalar()
    if not latest_month:
        return {
            "answer": "No allocation history found to suggest cross-project employees.",
            "sources": [],
            "suggestions": [],
        }

    source_rows = (
        db.query(
            Employee.employee_id,
            Employee.name,
            Employee.primary_skill,
            Employee.secondary_skill,
            Employee.years_experience,
            Employee.current_utilization,
            Employee.role,
            HistoricalAllocation.project_id,
            HistoricalAllocation.allocation_percentage,
            Project.project_name,
            Project.domain,
        )
        .join(HistoricalAllocation, HistoricalAllocation.employee_id == Employee.employee_id)
        .join(Project, Project.project_id == HistoricalAllocation.project_id)
        .filter(
            HistoricalAllocation.allocation_month == latest_month,
            HistoricalAllocation.project_id != project_id,
        )
        .all()
    )

    required_skills = {skill.lower() for skill in _parse_multi_value_text(project.required_skills)}
    min_experience = int(project.min_experience or 0)

    ranked = []
    for row in source_rows:
        employee_skills = {
            str(row.primary_skill or "").strip().lower(),
            str(row.secondary_skill or "").strip().lower(),
        }
        matched_skills = sorted(required_skills.intersection(employee_skills))
        if not matched_skills:
            continue
        if int(row.years_experience or 0) < min_experience:
            continue

        ranked.append(
            {
                "employee_id": row.employee_id,
                "name": row.name,
                "primary_skill": row.primary_skill,
                "secondary_skill": row.secondary_skill,
                "years_experience": row.years_experience,
                "current_utilization": row.current_utilization,
                "role": row.role,
                "source_project_id": row.project_id,
                "source_project_name": row.project_name,
                "source_project_domain": row.domain,
                "source_allocation_percentage": row.allocation_percentage,
                "matched_skills": matched_skills,
                "skill_match_count": len(matched_skills),
            }
        )

    ranked.sort(
        key=lambda item: (
            -item["skill_match_count"],
            float(item["current_utilization"] or 0.0),
            -int(item["years_experience"] or 0),
        )
    )
    suggestions = ranked[:top_k]

    if not suggestions:
        return {
            "answer": "No strong cross-project candidates found based on required skills and experience.",
            "sources": [],
            "suggestions": [],
        }

    suggestion_lines = "\n".join(
        [
            (
                f"- {candidate['name']} ({candidate['employee_id']}), "
                f"role: {candidate['role']}, skills: {candidate['primary_skill']}/{candidate['secondary_skill']}, "
                f"exp: {candidate['years_experience']}y, util: {candidate['current_utilization']}, "
                f"source: {candidate['source_project_name']} ({candidate['source_project_id']}), "
                f"allocation: {candidate['source_allocation_percentage']}%, "
                f"matched: {', '.join(candidate['matched_skills'])}"
            )
            for candidate in suggestions
        ]
    )
    prompt_query = query or "Suggest which cross-project employees should be moved first and why."
    prompt = (
        "You are a staffing advisor. Recommend employees from other projects for the target project. "
        "Use only the supplied candidates and provide concise rationale plus move-order priority."
        f"\nTarget project: {project.project_name} ({project.project_id})"
        f"\nRequired skills: {', '.join(sorted(required_skills)) or 'None provided'}"
        f"\nMinimum experience: {min_experience}"
        f"\nUser question: {prompt_query}"
        f"\nCandidates:\n{suggestion_lines}"
    )

    fallback_answer = (
        "Top cross-project candidates are listed below. "
        "Prioritize employees with higher skill overlap, lower utilization, and adequate experience."
    )

    use_llm = str(payload.get("use_llm", "false")).strip().lower() in {"1", "true", "yes", "y", "on"}

    if not use_llm:
        return {
            "answer": fallback_answer,
            "sources": [candidate["employee_id"] for candidate in suggestions],
            "suggestions": suggestions,
        }

    try:
        answer = chat_service.llm.generate(prompt, timeout_seconds=8.0)
    except Exception:
        answer = fallback_answer

    return {
        "answer": answer,
        "sources": [candidate["employee_id"] for candidate in suggestions],
        "suggestions": suggestions,
    }


@router.get("/analytics")
def analytics(
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "manager", "viewer"])),
):
    return analytics_service.get_overview(db)


@router.get("/bench")
def bench(
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "manager"])),
):
    return analytics_service.get_bench(db)


@router.get("/utilization")
def utilization(
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "manager", "viewer"])),
):
    return analytics_service.get_utilization(db)
