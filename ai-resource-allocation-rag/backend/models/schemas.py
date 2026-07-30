from typing import List, Optional

from pydantic import BaseModel, Field


class Employee(BaseModel):
    employee_id: str
    name: str
    primary_skill: str
    secondary_skill: str
    years_experience: int
    certifications: str
    availability_status: str
    current_utilization: float
    location: str
    role: str
    resume_text: str


class RecommendationRequest(BaseModel):
    project_name: str
    required_skills: List[str]
    preferred_certifications: List[str] = Field(default_factory=list)
    min_experience: int = 0
    required_count: int = 3
    location: Optional[str] = None
    domain: Optional[str] = None


class RecommendationComponentScores(BaseModel):
    skill_match: float
    availability: float
    certifications: float
    experience: float
    historical_performance: float


class RecommendationItem(BaseModel):
    employee_id: str
    employee_name: str
    match_score: float
    base_match_score: Optional[float] = None
    llm_score: Optional[float] = None
    final_score: Optional[float] = None
    role: Optional[str] = None
    primary_skill: Optional[str] = None
    secondary_skill: Optional[str] = None
    years_experience: Optional[int] = None
    certifications: Optional[str] = None
    latest_project_name: Optional[str] = None
    latest_project_domain: Optional[str] = None
    recommendation_reason: str
    skills_matched: List[str]
    missing_skills: List[str]
    availability: str
    upskilling_suggestions: List[str]
    component_scores: RecommendationComponentScores


class RecommendationResponse(BaseModel):
    project_name: str
    recommendations: List[RecommendationItem]
    requested_count: int = 0
    returned_count: int = 0
    retrieval_notice: Optional[str] = None


class ChatRequest(BaseModel):
    query: str
    top_k: int = 5


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserProfile(BaseModel):
    username: str
    full_name: str
    role: str
    is_active: bool
