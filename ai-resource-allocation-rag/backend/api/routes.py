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


SUPPORTED_CHAT_REASON = (
    "This chat recommendation is supported only for workforce staffing and allocation use cases "
    "(skills, experience, availability, utilization, bench, assignment/unassignment, and project allocation decisions). "
    "Other topics are not supported."
)


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


@router.post("/recommend", response_model=RecommendationResponse)
def recommend(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "manager"])),
) -> RecommendationResponse:
    recommendations = recommendation_service.recommend(db, request)
    return RecommendationResponse(project_name=request.project_name, recommendations=recommendations)


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
    ai_recommendations = recommendation_service.recommend(db, recommendation_request)

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

    return {
        "status": "unassigned",
        "project_id": project_id,
        "employee_id": employee_id,
        "allocation_month": employee_latest_month,
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

    try:
        answer = chat_service.llm.generate(prompt)
    except Exception:
        answer = "Top cross-project candidates are listed below. Prioritize higher skill overlap and lower utilization first."

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
