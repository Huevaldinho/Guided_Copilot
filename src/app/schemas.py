from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    professor_id: UUID
    duration_hours: Optional[int] = None
    level: Optional[str] = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")

class CourseOut(CourseCreate):
    id: UUID

class EnrollmentCreate(BaseModel):
    student_email: str
