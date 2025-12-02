"""
Course routes with complete type hints and error handling.
"""

from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks
from typing import List, Dict, Any
import logging

from ..schemas import (
    CourseCreate,
    CourseOut,
    CourseListResponse,
    BulkEnrollmentReport,
    EnrollmentResponse,
    ErrorResponse
)
from ..persistence.json_repo import JSONRepository
from ..application.services import CourseService, EnrollmentService
from ..core.config import get_data_file_path
from ..core.exceptions import CourseNotFoundError, DataPersistenceError
from ..tasks import background_bulk_enroll

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/courses", tags=["courses"])


def get_repo() -> JSONRepository:
    """Dependency to get JSONRepository instance.
    
    Returns:
        JSONRepository: Configured repository instance
    """
    return JSONRepository(get_data_file_path())


@router.post("/", response_model=CourseOut, status_code=201)
def create_course(
    payload: CourseCreate,
    repo: JSONRepository = Depends(get_repo)
) -> CourseOut:
    """Create a new course.
    
    Args:
        payload: Course creation data
        repo: Repository dependency
        
    Returns:
        Created course with ID
        
    Raises:
        DataPersistenceError: If save operation fails
    """
    service: CourseService = CourseService(repo)
    course: Dict[str, Any] = service.create_course(payload.dict())
    logger.info(f"Course created: {course['id']} - {course['title']}")
    return CourseOut(**course)


@router.get("/", response_model=List[CourseOut])
def list_courses(repo: JSONRepository = Depends(get_repo)) -> List[CourseOut]:
    """List all courses.
    
    Args:
        repo: Repository dependency
        
    Returns:
        List of all courses
    """
    service: CourseService = CourseService(repo)
    courses: List[Dict[str, Any]] = service.list_courses()
    logger.info(f"Retrieved {len(courses)} courses")
    return [CourseOut(**course) for course in courses]


@router.get("/listcourses", response_model=CourseListResponse)
def list_courses_detailed(repo: JSONRepository = Depends(get_repo)) -> CourseListResponse:
    """List all courses with metadata (alternative endpoint).
    
    Args:
        repo: Repository dependency
        
    Returns:
        CourseListResponse with courses and total count
    """
    service: CourseService = CourseService(repo)
    courses: List[Dict[str, Any]] = service.list_courses()
    logger.info(f"Retrieved {len(courses)} courses via /listcourses")
    return CourseListResponse(
        courses=[CourseOut(**course) for course in courses],
        total=len(courses)
    )


@router.post("/{course_id}/enrollments/bulk", response_model=BulkEnrollmentReport)
def bulk_enroll(
    course_id: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    repo: JSONRepository = Depends(get_repo),
) -> BulkEnrollmentReport:
    """Initiate bulk enrollment from CSV file.
    
    Args:
        course_id: Target course UUID
        file: CSV file with enrollment data
        background_tasks: FastAPI background tasks
        repo: Repository dependency
        
    Returns:
        Enrollment initiation report
        
    Raises:
        CourseNotFoundError: If course doesn't exist
    """
    # Verify course exists
    course: Dict[str, Any] | None = repo.get_course(course_id)
    if course is None:
        logger.warning(f"Bulk enrollment attempted for non-existent course: {course_id}")
        raise CourseNotFoundError(course_id)
    
    logger.info(f"Bulk enrollment initiated for course {course_id}")
    background_tasks.add_task(background_bulk_enroll, file.file, course_id)
    return BulkEnrollmentReport(total=0, enrolled=0, skipped=0)
