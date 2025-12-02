"""
Business logic services with complete type hints.
"""

from typing import List, Dict, Any, Optional
import logging
from ..persistence.json_repo import JSONRepository
from ..core.exceptions import CourseNotFoundError

logger = logging.getLogger(__name__)


class CourseService:
    """Service for managing course operations."""

    def __init__(self, repo: JSONRepository) -> None:
        """Initialize CourseService with repository.
        
        Args:
            repo: JSONRepository instance for data access
        """
        self.repo: JSONRepository = repo

    def create_course(self, course_in: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new course.
        
        Args:
            course_in: Course data dictionary
            
        Returns:
            Created course with ID and metadata
            
        Raises:
            DataPersistenceError: If save operation fails
        """
        created_course: Dict[str, Any] = self.repo.create_course(course_in)
        logger.info(f"Course created: {created_course['id']}")
        return created_course

    def list_courses(self) -> List[Dict[str, Any]]:
        """List all courses.
        
        Returns:
            List of all course records
        """
        courses: List[Dict[str, Any]] = self.repo.list_courses()
        logger.info(f"Retrieved {len(courses)} courses")
        return courses

    def get_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific course by ID.
        
        Args:
            course_id: Course UUID as string
            
        Returns:
            Course record or None if not found
        """
        course: Optional[Dict[str, Any]] = self.repo.get_course(course_id)
        if not course:
            logger.warning(f"Course not found: {course_id}")
            raise CourseNotFoundError(course_id)
        return course


class EnrollmentService:
    """Service for managing enrollment operations."""

    def __init__(self, repo: JSONRepository) -> None:
        """Initialize EnrollmentService with repository.
        
        Args:
            repo: JSONRepository instance for data access
        """
        self.repo: JSONRepository = repo

    def bulk_enroll(
        self,
        course_id: str,
        rows: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Process bulk enrollment from CSV data.
        
        Args:
            course_id: Target course UUID
            rows: List of enrollment records from CSV
            
        Returns:
            Enrollment report with statistics
            
        Raises:
            CourseNotFoundError: If course doesn't exist
        """
        # Verify course exists
        course: Optional[Dict[str, Any]] = self.repo.get_course(course_id)
        if not course:
            logger.warning(f"Bulk enrollment attempted for non-existent course: {course_id}")
            raise CourseNotFoundError(course_id)
        
        report: Dict[str, Any] = self.repo.bulk_enroll(course_id, rows)
        logger.info(
            f"Bulk enrollment completed: {report['enrolled']} enrolled, "
            f"{report['skipped']} skipped"
        )
        return report
