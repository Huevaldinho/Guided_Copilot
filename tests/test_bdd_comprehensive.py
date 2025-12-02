"""
Comprehensive BDD-style tests for LMS API with Allure reporting and detailed coverage.
Uses pytest-bdd for Gherkin-style scenarios and allure for detailed reporting.
"""

import pytest
import allure
from pytest_bdd import given, when, then, scenarios, scenario, parsers
import tempfile
import json
import os
from io import BytesIO
from uuid import uuid4

from src.app.main import create_app
from src.app.persistence.json_repo import JSONRepository
from src.app.core.error_tracking import ErrorTracker
from fastapi.testclient import TestClient


# ==================== FIXTURES ====================

@pytest.fixture(scope="function")
def data_file() -> str:
    """Provide isolated temporary data file for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "lms_data.json")
        os.environ["DATA_FILE_PATH"] = path
        yield path


@pytest.fixture(scope="function")
def client(data_file: str) -> TestClient:
    """Provide FastAPI test client with isolated data."""
    app = create_app()
    return TestClient(app)


@pytest.fixture(scope="function")
def repo(data_file: str) -> JSONRepository:
    """Provide isolated repository instance."""
    return JSONRepository(data_file)


@pytest.fixture(scope="function")
def error_tracker() -> ErrorTracker:
    """Provide error tracker instance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        return ErrorTracker(os.path.join(tmpdir, "error.log"))


@pytest.fixture(scope="function")
def sample_course_payload() -> dict:
    """Sample course creation payload."""
    return {
        "title": "Python Fundamentals",
        "description": "Learn Python basics",
        "professor_id": str(uuid4()),
        "duration_hours": 40,
        "level": "beginner"
    }


@pytest.fixture(scope="function")
def sample_csv_data() -> BytesIO:
    """Sample CSV enrollment data."""
    csv_content = "email,first_name,last_name\n"
    csv_content += "student1@example.com,John,Doe\n"
    csv_content += "student2@example.com,Jane,Smith\n"
    return BytesIO(csv_content.encode())


# ==================== BDD SCENARIOS ====================

@allure.feature("Courses Management")
@allure.story("Create Course")
class TestCreateCourse:
    """BDD scenarios for course creation."""

    @allure.title("Successfully create a new course")
    @allure.description("Verify that a course can be created with valid data")
    def test_create_course_success(
        self,
        client: TestClient,
        sample_course_payload: dict
    ) -> None:
        """Scenario: Create a course with valid data."""
        with allure.step("Given valid course data"):
            payload = sample_course_payload

        with allure.step("When POST request to /courses"):
            response = client.post("/courses/", json=payload)

        with allure.step("Then response status is 201"):
            assert response.status_code == 201, f"Expected 201, got {response.status_code}"

        with allure.step("And response contains course ID"):
            data = response.json()
            assert "id" in data, "Response missing 'id' field"
            assert data["title"] == payload["title"]
            assert data["level"] == payload["level"]

    @allure.title("Reject course without title")
    @allure.description("Verify validation of required title field")
    def test_create_course_missing_title(self, client: TestClient) -> None:
        """Scenario: Attempt to create course without title."""
        with allure.step("Given course payload without title"):
            payload = {
                "description": "No title provided",
                "professor_id": str(uuid4()),
                "level": "beginner"
            }

        with allure.step("When POST request to /courses"):
            response = client.post("/courses/", json=payload)

        with allure.step("Then response status is 422"):
            assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    @allure.title("Reject invalid course level")
    @allure.description("Verify level validation (beginner/intermediate/advanced)")
    def test_create_course_invalid_level(
        self,
        client: TestClient,
        sample_course_payload: dict
    ) -> None:
        """Scenario: Attempt to create course with invalid level."""
        with allure.step("Given course payload with invalid level"):
            sample_course_payload["level"] = "expert"

        with allure.step("When POST request to /courses"):
            response = client.post("/courses/", json=sample_course_payload)

        with allure.step("Then response status is 422"):
            assert response.status_code == 422


@allure.feature("Courses Management")
@allure.story("List Courses")
class TestListCourses:
    """BDD scenarios for listing courses."""

    @allure.title("List all courses - empty list")
    @allure.description("Verify that empty course list is returned initially")
    def test_list_courses_empty(self, client: TestClient) -> None:
        """Scenario: List courses when none exist."""
        with allure.step("Given no courses exist"):
            pass

        with allure.step("When GET request to /courses/"):
            response = client.get("/courses/")

        with allure.step("Then response status is 200"):
            assert response.status_code == 200

        with allure.step("And response is empty list"):
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0

    @allure.title("List courses - with courses")
    @allure.description("Verify that created courses appear in list")
    def test_list_courses_with_data(
        self,
        client: TestClient,
        sample_course_payload: dict
    ) -> None:
        """Scenario: List courses after creating some."""
        with allure.step("Given courses are created"):
            client.post("/courses/", json=sample_course_payload)
            sample_course_payload["title"] = "Advanced Python"
            sample_course_payload["level"] = "advanced"
            client.post("/courses/", json=sample_course_payload)

        with allure.step("When GET request to /courses/"):
            response = client.get("/courses/")

        with allure.step("Then response status is 200"):
            assert response.status_code == 200

        with allure.step("And response contains 2 courses"):
            data = response.json()
            assert len(data) == 2

    @allure.title("List courses via /listcourses endpoint")
    @allure.description("Verify alternative /listcourses endpoint works")
    def test_list_courses_alternative_endpoint(
        self,
        client: TestClient,
        sample_course_payload: dict
    ) -> None:
        """Scenario: List courses via /listcourses endpoint."""
        with allure.step("Given courses exist"):
            client.post("/courses/", json=sample_course_payload)

        with allure.step("When GET request to /courses/listcourses"):
            response = client.get("/courses/listcourses")

        with allure.step("Then response status is 200"):
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        with allure.step("And response contains courses and total"):
            data = response.json()
            assert "courses" in data
            assert "total" in data
            assert data["total"] == 1


@allure.feature("Health & Monitoring")
@allure.story("Health Check")
class TestHealthCheck:
    """BDD scenarios for health check endpoint."""

    @allure.title("Health check returns healthy status")
    @allure.description("Verify /health endpoint returns proper status")
    def test_health_check_healthy(self, client: TestClient) -> None:
        """Scenario: Health check when system is healthy."""
        with allure.step("When GET request to /health"):
            response = client.get("/health")

        with allure.step("Then response status is 200"):
            assert response.status_code == 200

        with allure.step("And response contains status field"):
            data = response.json()
            assert "status" in data
            assert data["status"] in ["healthy", "degraded"]

        with allure.step("And response contains error statistics"):
            assert "errors" in data
            assert "alerts" in data

    @allure.title("Error endpoint returns statistics")
    @allure.description("Verify /errors endpoint provides error tracking")
    def test_errors_endpoint(self, client: TestClient) -> None:
        """Scenario: Retrieve error statistics."""
        with allure.step("When GET request to /errors"):
            response = client.get("/errors")

        with allure.step("Then response status is 200"):
            assert response.status_code == 200

        with allure.step("And response contains stats and alerts"):
            data = response.json()
            assert "stats" in data
            assert "recent_alerts" in data


@allure.feature("Bulk Enrollment")
@allure.story("Enrollment Management")
class TestBulkEnrollment:
    """BDD scenarios for bulk enrollment."""

    @allure.title("Bulk enroll from CSV file")
    @allure.description("Verify bulk enrollment processing")
    def test_bulk_enroll_success(
        self,
        client: TestClient,
        sample_course_payload: dict,
        sample_csv_data: BytesIO
    ) -> None:
        """Scenario: Bulk enroll students from CSV."""
        with allure.step("Given a course exists"):
            resp = client.post("/courses/", json=sample_course_payload)
            course_id = resp.json()["id"]

        with allure.step("And CSV enrollment data"):
            pass

        with allure.step("When POST bulk enrollment request"):
            sample_csv_data.seek(0)
            response = client.post(
                f"/courses/{course_id}/enrollments/bulk",
                files={"file": ("enrollment.csv", sample_csv_data)}
            )

        with allure.step("Then response status is 200"):
            assert response.status_code == 200

        with allure.step("And response confirms acceptance"):
            data = response.json()
            assert "total" in data
            assert "enrolled" in data
            assert "skipped" in data

    @allure.title("Bulk enroll with non-existent course")
    @allure.description("Verify error when course doesn't exist")
    def test_bulk_enroll_course_not_found(
        self,
        client: TestClient,
        sample_csv_data: BytesIO
    ) -> None:
        """Scenario: Attempt bulk enrollment for non-existent course."""
        with allure.step("Given non-existent course ID"):
            fake_course_id = str(uuid4())

        with allure.step("When POST bulk enrollment request"):
            sample_csv_data.seek(0)
            response = client.post(
                f"/courses/{fake_course_id}/enrollments/bulk",
                files={"file": ("enrollment.csv", sample_csv_data)}
            )

        with allure.step("Then response status is 404"):
            assert response.status_code == 404

        with allure.step("And response contains error code"):
            data = response.json()
            assert "error_code" in data


@allure.feature("Error Handling")
@allure.story("Error Tracking")
class TestErrorHandling:
    """BDD scenarios for error handling system."""

    @allure.title("Error tracker logs exceptions")
    @allure.description("Verify error tracking records errors correctly")
    def test_error_tracking(self, error_tracker: ErrorTracker) -> None:
        """Scenario: Error tracker logs exceptions."""
        with allure.step("When logging an error"):
            record = error_tracker.log_error(
                "TestError",
                "Test error message",
                "TEST_ERROR",
                {"detail": "test"}
            )

        with allure.step("Then error is recorded"):
            assert record["error_code"] == "TEST_ERROR"
            assert record["severity"] in ["INFO", "WARNING", "CRITICAL"]

        with allure.step("And error count incremented"):
            assert error_tracker.error_count == 1

    @allure.title("Critical failure threshold detection")
    @allure.description("Verify system detects critical failure state")
    def test_critical_failure_threshold(self, error_tracker: ErrorTracker) -> None:
        """Scenario: Detect critical failure after 5+ errors."""
        with allure.step("Given multiple errors occur"):
            for i in range(6):
                error_tracker.log_error("Test", f"Error {i}", "TEST")

        with allure.step("Then critical failure is detected"):
            assert error_tracker.is_critical_failure()

        with allure.step("And error statistics available"):
            stats = error_tracker.get_error_stats()
            assert stats["total_errors"] == 6


@allure.feature("Data Persistence")
@allure.story("Repository Operations")
class TestDataPersistence:
    """BDD scenarios for data persistence."""

    @allure.title("Course data persists")
    @allure.description("Verify atomic writes ensure data persistence")
    def test_atomic_write_persistence(self, repo: JSONRepository) -> None:
        """Scenario: Course data is atomically persisted."""
        with allure.step("When creating a course"):
            course = repo.create_course({
                "title": "Persistent Course",
                "professor_id": str(uuid4()),
                "level": "beginner"
            })
            course_id = course["id"]

        with allure.step("Then course can be retrieved"):
            retrieved = repo.get_course(course_id)
            assert retrieved is not None
            assert retrieved["title"] == "Persistent Course"

        with allure.step("And file is valid JSON"):
            with open(repo.path, "r") as f:
                data = json.load(f)
                assert "courses" in data


# ==================== PARAMETRIZED TESTS ====================

@allure.feature("Validation")
@allure.story("Input Validation")
class TestInputValidation:
    """Parametrized tests for input validation."""

    @allure.title("Level validation with multiple values")
    @pytest.mark.parametrize("invalid_level", [
        "expert",
        "BEGINNER",
        "novice",
        "professional",
        ""
    ])
    def test_invalid_levels(
        self,
        client: TestClient,
        sample_course_payload: dict,
        invalid_level: str
    ) -> None:
        """Scenario: Reject all invalid level values."""
        with allure.step(f"Given invalid level: {invalid_level}"):
            sample_course_payload["level"] = invalid_level

        with allure.step("When POST request to /courses"):
            response = client.post("/courses/", json=sample_course_payload)

        with allure.step("Then response status is 422"):
            assert response.status_code == 422, f"Failed for level: {invalid_level}"

    @allure.title("Valid levels accepted")
    @pytest.mark.parametrize("valid_level", [
        "beginner",
        "intermediate",
        "advanced"
    ])
    def test_valid_levels(
        self,
        client: TestClient,
        sample_course_payload: dict,
        valid_level: str
    ) -> None:
        """Scenario: Accept all valid level values."""
        with allure.step(f"Given valid level: {valid_level}"):
            sample_course_payload["level"] = valid_level

        with allure.step("When POST request to /courses"):
            response = client.post("/courses/", json=sample_course_payload)

        with allure.step("Then response status is 201"):
            assert response.status_code == 201, f"Failed for level: {valid_level}"


# ==================== INTEGRATION TESTS ====================

@allure.feature("Integration")
@allure.story("Complete Workflows")
class TestIntegrationScenarios:
    """Integration tests for complete workflows."""

    @allure.title("Complete enrollment workflow")
    @allure.description("End-to-end course creation and enrollment")
    def test_complete_enrollment_workflow(
        self,
        client: TestClient,
        sample_course_payload: dict,
        sample_csv_data: BytesIO
    ) -> None:
        """Scenario: Complete workflow from course creation to enrollment."""
        with allure.step("Step 1: Create course"):
            resp = client.post("/courses/", json=sample_course_payload)
            assert resp.status_code == 201
            course_id = resp.json()["id"]

        with allure.step("Step 2: List courses and verify"):
            resp = client.get("/courses/")
            assert resp.status_code == 200
            courses = resp.json()
            assert len(courses) == 1

        with allure.step("Step 3: List courses via alternative endpoint"):
            resp = client.get("/courses/listcourses")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1

        with allure.step("Step 4: Bulk enroll students"):
            sample_csv_data.seek(0)
            resp = client.post(
                f"/courses/{course_id}/enrollments/bulk",
                files={"file": ("enrollment.csv", sample_csv_data)}
            )
            assert resp.status_code == 200

        with allure.step("Step 5: Verify health check"):
            resp = client.get("/health")
            assert resp.status_code == 200
            assert resp.json()["status"] in ["healthy", "degraded"]
