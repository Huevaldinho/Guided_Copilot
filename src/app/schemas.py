"""
Pydantic schemas for LMS application with complete type hints.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class CourseCreate(BaseModel):
    """Schema for creating a new course."""
    
    title: str = Field(..., min_length=1, max_length=255, description="Course title")
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Course description"
    )
    professor_id: UUID = Field(..., description="UUID of the professor")
    duration_hours: Optional[int] = Field(
        default=None,
        ge=1,
        le=1000,
        description="Course duration in hours"
    )
    level: str = Field(
        default="beginner",
        pattern="^(beginner|intermediate|advanced)$",
        description="Course difficulty level"
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate course title is not empty."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate level is one of allowed values."""
        if v not in ["beginner", "intermediate", "advanced"]:
            raise ValueError("Level must be beginner, intermediate, or advanced")
        return v


class CourseOut(CourseCreate):
    """Schema for course output with ID."""
    
    id: UUID = Field(..., description="Unique course identifier")
    created_at: datetime = Field(..., description="Course creation timestamp")


class CourseListResponse(BaseModel):
    """Schema for course list response."""
    
    courses: List[CourseOut] = Field(..., description="List of courses")
    total: int = Field(..., ge=0, description="Total number of courses")


class EnrollmentCreate(BaseModel):
    """Schema for creating an enrollment."""
    
    student_email: str = Field(..., description="Student email address")

    @field_validator("student_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if "@" not in v or not v.strip():
            raise ValueError("Invalid email format")
        return v.strip().lower()


class BulkEnrollmentReport(BaseModel):
    """Schema for bulk enrollment report."""
    
    total: int = Field(..., ge=0, description="Total enrollments processed")
    enrolled: int = Field(..., ge=0, description="Successfully enrolled")
    skipped: int = Field(..., ge=0, description="Skipped (e.g., max enrollments)")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Errors encountered")


class EnrollmentResponse(BaseModel):
    """Schema for enrollment response."""
    
    status: str = Field(..., description="Response status")
    detail: str = Field(..., description="Status detail message")


class HealthCheckResponse(BaseModel):
    """Schema for health check response."""
    
    status: str = Field(..., description="Health status: healthy or degraded")
    errors: Dict[str, Any] = Field(..., description="Error statistics")
    alerts: List[Dict[str, Any]] = Field(default_factory=list, description="Recent alerts")


class ErrorStatsResponse(BaseModel):
    """Schema for error statistics response."""
    
    stats: Dict[str, Any] = Field(..., description="Error statistics")
    recent_alerts: List[Dict[str, Any]] = Field(..., description="Recent alert list")


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    
    message: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Machine-readable error code")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")


class UserCreate(BaseModel):
    """Schema for creating a user."""
    
    email: str = Field(..., description="User email address")
    role: str = Field(default="student", description="User role")
    is_active: bool = Field(default=True, description="User active status")

    @field_validator("email")
    @classmethod
    def validate_email_user(cls, v: str) -> str:
        """Validate user email."""
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.strip().lower()


class UserResponse(UserCreate):
    """Schema for user response."""
    
    id: UUID = Field(..., description="User unique identifier")
    created_at: datetime = Field(..., description="User creation timestamp")


class EnrollmentDB(BaseModel):
    """Schema for enrollment database record."""
    
    id: UUID = Field(..., description="Enrollment unique identifier")
    student_email: str = Field(..., description="Student email address")
    course_id: UUID = Field(..., description="Course unique identifier")
    enrolled_at: datetime = Field(..., description="Enrollment timestamp")
    progress_percentage: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    completed: bool = Field(default=False, description="Completion status")
    completion_date: Optional[datetime] = Field(default=None, description="Completion date")
