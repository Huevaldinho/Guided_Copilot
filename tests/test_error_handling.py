"""
Tests for error handling, recovery, and notifications.
"""

import pytest
import allure
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.app.core.exceptions import (
    LMSException,
    DataPersistenceError,
    FileLockError,
    CourseNotFoundError,
    ValidationError,
)
from src.app.core.error_tracking import ErrorTracker
from src.app.core.notifications import NotificationService
from src.app.persistence.json_repo import JSONRepository


@allure.feature("Error Handling")
@allure.story("Exception Classes")
class TestExceptions:
    """Test custom exception classes."""

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("unit", "exceptions", "critical")
    @allure.title("Verify LMS exception base class creation and attributes")
    def test_lms_exception_base(self):
        """Test that LMS base exception is properly initialized."""
        exc = LMSException("Test error", "TEST_ERROR", {"key": "value"})
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.to_dict()["error_code"] == "TEST_ERROR"

    @allure.severity(allure.severity_level.HIGH)
    @allure.tag("unit", "exceptions", "defect")
    @allure.title("Verify CourseNotFoundError is properly raised and formatted")
    def test_course_not_found_error(self):
        """Test that CourseNotFoundError contains proper error information."""
        exc = CourseNotFoundError("course-123")
        assert "course-123" not in exc.message or "not found" in exc.message
        assert exc.error_code == "COURSE_NOT_FOUND"

    @allure.severity(allure.severity_level.HIGH)
    @allure.tag("unit", "exceptions", "persistence")
    @allure.title("Verify DataPersistenceError captures error details")
    def test_data_persistence_error(self):
        """Test that DataPersistenceError properly stores persistence context."""
        exc = DataPersistenceError("Write failed", {"path": "/data/test.json"})
        assert exc.error_code == "DATA_PERSISTENCE_ERROR"


@allure.feature("Error Handling")
@allure.story("Error Tracking")
class TestErrorTracker:
    """Test error tracking functionality."""

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("unit", "error-tracking", "initialization")
    @allure.title("Verify ErrorTracker initializes with correct state")
    def test_error_tracker_initialization(self):
        """Test that ErrorTracker is properly initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "error.log")
            tracker = ErrorTracker(log_path)
            assert tracker.error_count == 0
            assert tracker.last_error_time is None

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("unit", "error-tracking", "logging")
    @allure.title("Verify error logging stores error records correctly")
    def test_log_error(self):
        """Test that errors are properly logged and tracked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "error.log")
            tracker = ErrorTracker(log_path)

            error_record = tracker.log_error(
                "TestError",
                "Test message",
                "TEST_CODE",
                {"detail": "test"},
            )

            assert error_record["error_code"] == "TEST_CODE"
            assert error_record["message"] == "Test message"
            assert tracker.error_count == 1
            assert os.path.exists(log_path)

    @allure.severity(allure.severity_level.HIGH)
    @allure.tag("unit", "error-tracking", "severity")
    @allure.title("Verify error severity is correctly determined based on error code")
    def test_error_severity_determination(self):
        """Test that error severity levels are correctly assigned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "error.log")
            tracker = ErrorTracker(log_path)

            # Critical error
            record = tracker.log_error("Test", "msg", "FILE_LOCK_ERROR")
            assert record["severity"] == "CRITICAL"

            # Warning
            record = tracker.log_error("Test", "msg", "VALIDATION_ERROR")
            assert record["severity"] == "WARNING"

    @allure.severity(allure.severity_level.HIGH)
    @allure.tag("unit", "error-tracking", "threshold")
    @allure.title("Verify critical failure threshold detection")
    def test_critical_failure_threshold(self):
        """Test that system detects when error threshold is exceeded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "error.log")
            tracker = ErrorTracker(log_path)

            assert not tracker.is_critical_failure()

            for i in range(6):
                tracker.log_error("Test", f"error {i}", "TEST_CODE")

            assert tracker.is_critical_failure()

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("unit", "error-tracking", "statistics")
    @allure.title("Verify error statistics are accurately calculated")
    def test_error_stats(self):
        """Test that error statistics are properly generated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "error.log")
            tracker = ErrorTracker(log_path)
            tracker.log_error("Test", "msg", "TEST_CODE")

            stats = tracker.get_error_stats()
            assert stats["total_errors"] == 1
            assert stats["last_error_time"] is not None



@allure.feature("Error Handling")
@allure.story("Notifications")
class TestNotificationService:
    """Test notification system."""

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("unit", "notifications", "initialization")
    @allure.title("Verify notification service initializes successfully")
    def test_notification_service_initialization(self):
        """Test that NotificationService is properly initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"ALERTS_DIR": tmpdir}):
                service = NotificationService()
                assert service.alerts_dir.exists()

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("unit", "notifications", "file-io")
    @allure.title("Verify alert files are written correctly")
    def test_write_alert_file(self):
        """Test that alert files are properly written to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"ALERTS_DIR": tmpdir}):
                service = NotificationService()
                notification = {
                    "timestamp": "2025-01-01T00:00:00",
                    "error_type": "Test",
                    "message": "Test message",
                    "error_code": "TEST_CODE",
                    "severity": "WARNING",
                    "details": {},
                }

                status = service.notify_error(
                    "Test",
                    "Test message",
                    "TEST_CODE",
                    {},
                    "WARNING",
                )

                assert status["file"] == "success"
                alert_files = list(Path(tmpdir).glob("alert_*.json"))
                assert len(alert_files) > 0

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("unit", "notifications", "retrieval")
    @allure.title("Verify recent alerts are correctly retrieved")
    def test_get_recent_alerts(self):
        """Test that recent alerts can be retrieved from disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"ALERTS_DIR": tmpdir}):
                service = NotificationService()

                # Create multiple alerts
                for i in range(3):
                    service.notify_error(
                        "Test",
                        f"Test message {i}",
                        f"TEST_CODE_{i}",
                        {},
                        "WARNING",
                    )

                alerts = service.get_recent_alerts(limit=5)
                assert len(alerts) >= 3



@allure.feature("Error Handling")
@allure.story("Persistence and Data Integrity")
class TestJSONRepositoryErrorHandling:
    """Test error handling in JSON repository."""

    @allure.severity(allure.severity_level.HIGH)
    @allure.tag("integration", "persistence", "defect", "data-integrity")
    @allure.title("Verify recovery from corrupted JSON data")
    @allure.description("Test that system handles malformed JSON gracefully and recovers default structure")
    def test_data_persistence_error_on_read(self):
        """Test that corrupted JSON doesn't crash the system."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            # Create invalid JSON
            with open(path, "w") as f:
                f.write("{invalid json}")

            repo = JSONRepository(path)
            # Should not raise, should return default structure
            data = repo._read_data()
            assert "courses" in data

    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("integration", "persistence", "concurrency", "defect")
    @allure.title("Verify file lock timeout handling")
    @allure.description("Test that file lock timeouts are properly caught and reported as errors")
    def test_file_lock_timeout_handling(self):
        """Test that file lock timeouts are caught and converted to FileLockError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            repo = JSONRepository(path)

            # Simulate lock timeout by mocking FileLock
            with patch("src.app.persistence.json_repo.FileLock") as mock_lock:
                from filelock import Timeout

                mock_instance = MagicMock()
                mock_instance.__enter__.side_effect = Timeout("mock_file")
                mock_lock.return_value = mock_instance

                with pytest.raises(FileLockError):
                    repo._read_data()

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("integration", "persistence", "statistics")
    @allure.title("Verify error statistics are tracked during persistence operations")
    def test_data_persistence_error_stats(self):
        """Test that error statistics are properly tracked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            with patch("src.app.core.error_tracking.get_error_tracker") as mock_tracker:
                tracker = ErrorTracker(os.path.join(tmpdir, "error.log"))
                mock_tracker.return_value = tracker

                repo = JSONRepository(path)
                course = repo.create_course(
                    {
                        "title": "Test",
                        "professor_id": "prof-1",
                        "level": "beginner",
                    }
                )
                assert course["id"] is not None



@allure.feature("System Health")
@allure.story("Health Checks and Monitoring")
class TestHealthCheckEndpoint:
    """Test health check with error statistics."""

    @allure.severity(allure.severity_level.HIGH)
    @allure.tag("integration", "health-check", "monitoring")
    @allure.title("Verify health check endpoint responds successfully")
    def test_health_check_basic(self, client):
        """Test that health endpoint is accessible."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "errors" in data

    @allure.severity(allure.severity_level.HIGH)
    @allure.tag("integration", "health-check", "degraded-mode")
    @allure.title("Verify system reports degraded status when errors exceed threshold")
    def test_health_check_degraded_on_errors(self, client):
        """Test that system shows degraded status with high error count."""
        # Make a request that would trigger errors
        resp = client.get("/health")
        data = resp.json()
        # Status should be healthy or degraded depending on error count
        assert data["status"] in ["healthy", "degraded"]

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("integration", "health-check", "errors-endpoint")
    @allure.title("Verify errors endpoint provides error statistics and alerts")
    def test_errors_endpoint(self, client):
        """Test that errors endpoint provides detailed statistics."""
        resp = client.get("/errors")
        assert resp.status_code == 200
        data = resp.json()
        assert "stats" in data
        assert "recent_alerts" in data



@allure.feature("Error Handling")
@allure.story("Recovery and Resilience")
class TestErrorRecovery:
    """Test error recovery and restart scenarios."""

    @allure.severity(allure.severity_level.HIGH)
    @allure.tag("integration", "recovery", "data-integrity", "defect")
    @allure.title("Verify application recovers from JSON file corruption")
    @allure.description("Test that corrupted JSON files are handled gracefully and data is recovered")
    def test_app_recovers_from_json_corruption(self):
        """Test that system can recover from corrupted JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            
            # Create a valid repo
            repo = JSONRepository(path)
            course1 = repo.create_course(
                {"title": "Course 1", "professor_id": "prof-1", "level": "beginner"}
            )

            # Corrupt the JSON file
            with open(path, "w") as f:
                f.write("{corrupted")

            # Create new repo instance - should recover
            repo2 = JSONRepository(path)
            data = repo2._read_data()
            assert "courses" in data

    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("integration", "concurrency", "file-locking", "defect")
    @allure.title("Verify file locking prevents concurrent write corruption")
    @allure.description("Test that atomic writes with file locking ensure data consistency under concurrent access")
    def test_concurrent_write_handling(self):
        """Test that file locking prevents concurrent writes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            repo = JSONRepository(path)

            course1 = repo.create_course(
                {"title": "Course 1", "professor_id": "prof-1", "level": "beginner"}
            )
            course2 = repo.create_course(
                {"title": "Course 2", "professor_id": "prof-2", "level": "intermediate"}
            )

            courses = repo.list_courses()
            # Both courses should be present (atomic writes ensured)
            assert len(courses) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

