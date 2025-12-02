"""
Error tracking and logging module for monitoring application health.
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ErrorTracker:
    """Tracks errors and generates alerts for critical failures."""

    def __init__(self, error_log_path: str = "/data/error_log.jsonl"):
        self.error_log_path = Path(error_log_path)
        self.error_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.error_count = 0
        self.last_error_time = None

    def log_error(
        self,
        error_type: str,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ) -> Dict[str, Any]:
        """
        Log an error to file and track metrics.

        Args:
            error_type: Category of error (e.g., "DataPersistence", "Validation")
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional context as dictionary
            exception: Original exception object

        Returns:
            Error record dictionary
        """
        self.error_count += 1
        self.last_error_time = datetime.utcnow()

        error_record = {
            "timestamp": self.last_error_time.isoformat(),
            "error_count": self.error_count,
            "error_type": error_type,
            "message": message,
            "error_code": error_code,
            "details": details or {},
            "severity": self._determine_severity(error_code),
        }

        if exception:
            error_record["exception"] = str(exception)
            error_record["exc_type"] = type(exception).__name__

        # Write to log file (JSONL format)
        try:
            with open(self.error_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(error_record, default=str) + "\n")
        except Exception as e:
            logger.error(f"Failed to write error log: {e}")

        logger.error(
            f"[{error_code}] {message}",
            extra={"details": details, "severity": error_record["severity"]},
        )

        return error_record

    def get_error_stats(self) -> Dict[str, Any]:
        """Retrieve current error statistics."""
        return {
            "total_errors": self.error_count,
            "last_error_time": self.last_error_time.isoformat()
            if self.last_error_time
            else None,
            "log_file": str(self.error_log_path),
        }

    def is_critical_failure(self) -> bool:
        """Check if error rate indicates critical failure (>5 errors in session)."""
        return self.error_count > 5

    @staticmethod
    def _determine_severity(error_code: str) -> str:
        """Determine severity level based on error code."""
        critical = {"FILE_LOCK_ERROR", "DATA_PERSISTENCE_ERROR", "CONFIGURATION_ERROR"}
        warning = {"VALIDATION_ERROR", "BULK_ENROLLMENT_ERROR"}

        if error_code in critical:
            return "CRITICAL"
        elif error_code in warning:
            return "WARNING"
        return "INFO"


# Global error tracker instance
_error_tracker = None


def get_error_tracker(error_log_path: str = "/data/error_log.jsonl") -> ErrorTracker:
    """Get or create global error tracker."""
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker(error_log_path)
    return _error_tracker
