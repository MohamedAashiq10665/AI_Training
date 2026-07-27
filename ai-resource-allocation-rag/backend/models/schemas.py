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


class RecommendationItem(BaseModel):
    employee_id: str
    employee_name: str
    match_score: float
    recommendation_reason: str
    skills_matched: List[str]
    missing_skills: List[str]
    availability: str
    upskilling_suggestions: List[str]


class RecommendationResponse(BaseModel):
    project_name: str
    recommendations: List[RecommendationItem]


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
