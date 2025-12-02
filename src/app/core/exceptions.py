"""
Custom exception classes for LMS application error handling.
"""


class LMSException(Exception):
    """Base exception for all LMS-specific errors."""

    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR", details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self):
        return {
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }


class DataPersistenceError(LMSException):
    """Raised when JSON file operations fail."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "DATA_PERSISTENCE_ERROR", details)


class FileLockError(LMSException):
    """Raised when file locking operations timeout or fail."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "FILE_LOCK_ERROR", details)


class ValidationError(LMSException):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class CourseNotFoundError(LMSException):
    """Raised when a course cannot be found."""

    def __init__(self, course_id: str):
        super().__init__(
            f"Course with id {course_id} not found",
            "COURSE_NOT_FOUND",
            {"course_id": course_id},
        )


class BulkEnrollmentError(LMSException):
    """Raised during bulk enrollment processing failures."""

    def __init__(self, message: str, row: int = None, details: dict = None):
        d = details or {}
        if row is not None:
            d["row"] = row
        super().__init__(message, "BULK_ENROLLMENT_ERROR", d)


class ConfigurationError(LMSException):
    """Raised when critical configuration is missing."""

    def __init__(self, config_key: str):
        super().__init__(
            f"Missing critical configuration: {config_key}",
            "CONFIGURATION_ERROR",
            {"config_key": config_key},
        )
