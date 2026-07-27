from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps import require_roles
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
    result = chat_service.answer(db, request.query, top_k=request.top_k)
    return ChatResponse(**result)


@router.get("/employees")
def get_employees(
    limit: int = 500,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["admin", "manager", "viewer"])),
):
    employees = EmployeeRepository(db).list(limit=limit)
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
        }
        for e in employees
    ]


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
