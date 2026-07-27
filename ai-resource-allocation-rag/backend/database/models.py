from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(30), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Employee(Base):
    __tablename__ = "employees"

    employee_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    primary_skill: Mapped[str] = mapped_column(String(100), index=True)
    secondary_skill: Mapped[str] = mapped_column(String(100), default="")
    years_experience: Mapped[int] = mapped_column(Integer, default=0)
    certifications: Mapped[str] = mapped_column(Text, default="")
    availability_status: Mapped[str] = mapped_column(String(50), index=True)
    current_utilization: Mapped[float] = mapped_column(Float, default=0.0)
    location: Mapped[str] = mapped_column(String(100), default="")
    role: Mapped[str] = mapped_column(String(100), default="")
    resume_text: Mapped[str] = mapped_column(Text, default="")

    allocations: Mapped[list[HistoricalAllocation]] = relationship(back_populates="employee")


class Project(Base):
    __tablename__ = "projects"

    project_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    required_skills: Mapped[str] = mapped_column(Text, default="")
    preferred_certifications: Mapped[str] = mapped_column(Text, default="")
    min_experience: Mapped[int] = mapped_column(Integer, default=0)
    required_headcount: Mapped[int] = mapped_column(Integer, default=1)
    location: Mapped[str] = mapped_column(String(100), default="")
    domain: Mapped[str] = mapped_column(String(100), default="")

    allocations: Mapped[list[HistoricalAllocation]] = relationship(back_populates="project")


class HistoricalAllocation(Base):
    __tablename__ = "historical_allocations"

    allocation_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.employee_id"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.project_id"), index=True)
    allocation_month: Mapped[str] = mapped_column(String(7), index=True)
    allocation_percentage: Mapped[int] = mapped_column(Integer, default=100)
    performance_rating: Mapped[float] = mapped_column(Float, default=3.0)

    employee: Mapped[Employee] = relationship(back_populates="allocations")
    project: Mapped[Project] = relationship(back_populates="allocations")
