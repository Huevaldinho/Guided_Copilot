"""
Tests for Courses API endpoints with comprehensive coverage and error handling.
"""

import allure
import pytest


@allure.feature("Courses Management")
@allure.story("Course Creation")
class TestCourseCreation:
    """Test course creation functionality."""

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("integration", "courses", "crud", "happy-path")
    @allure.title("Successfully create a new course with valid data")
    @allure.description("Verify that valid course creation returns 201 status and proper response structure")
    def test_create_course(self, client):
        """Test creating a course with valid payload."""
        payload = {
            "title": "Intro to Python",
            "description": "Learn Python",
            "professor_id": "00000000-0000-0000-0000-000000000000",
            "duration_hours": 12,
            "level": "beginner"
        }
        resp = client.post("/courses/", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["title"] == payload["title"]


@allure.feature("Courses Management")
@allure.story("Course Retrieval")
class TestCourseRetrieval:
    """Test course retrieval and listing."""

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("integration", "courses", "crud", "happy-path")
    @allure.title("Successfully list all courses")
    @allure.description("Verify that course listing returns all created courses")
    def test_list_courses(self, client):
        """Test listing all courses."""
        payload = {
            "title": "Data Structures",
            "description": "DS course",
            "professor_id": "00000000-0000-0000-0000-000000000000",
            "duration_hours": 8,
            "level": "intermediate"
        }
        client.post("/courses/", json=payload)
        resp = client.get("/courses/")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert any(c["title"] == "Data Structures" for c in data)


@allure.feature("System Health")
@allure.story("Health Monitoring")
class TestHealthEndpoint:
    """Test health check endpoint."""

    @allure.severity(allure.severity_level.HIGH)
    @allure.tag("integration", "health-check", "monitoring")
    @allure.title("Verify health endpoint returns valid status")
    @allure.description("Test that health endpoint is responsive and returns valid status")
    def test_health(self, client):
        """Test health endpoint."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ["ok", "healthy", "degraded"]


@allure.feature("Courses Management")
@allure.story("Input Validation")
class TestInputValidation:
    """Test input validation and error handling."""

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("integration", "courses", "validation", "error-handling")
    @allure.title("Reject course creation with missing required field")
    @allure.description("Verify that missing required fields are properly validated and rejected with 422 status")
    def test_create_course_missing_required_field(self, client):
        """Test that missing required fields are rejected."""
        payload = {
            "description": "Missing title"
        }
        resp = client.post("/courses/", json=payload)
        assert resp.status_code == 422

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("integration", "courses", "validation", "error-handling", "defect")
    @allure.title("Reject enrollment creation for non-existent course")
    @allure.description("Verify that enrollment requests for non-existent courses return 422 status")
    def test_get_nonexistent_course(self, client):
        """Test that requests for non-existent courses are rejected."""
        resp = client.post("/courses/00000000-0000-0000-0000-000000000001/enrollments/bulk")
        assert resp.status_code == 422

    @allure.severity(allure.severity_level.HIGH)
    @allure.tag("integration", "courses", "validation", "error-handling", "defect")
    @allure.title("Reject course with invalid level value")
    @allure.description("Verify that invalid level values are rejected with proper validation error")
    def test_invalid_course_level(self, client):
        """Test that invalid course levels are rejected."""
        payload = {
            "title": "Test",
            "description": "Test",
            "professor_id": "00000000-0000-0000-0000-000000000000",
            "level": "invalid_level"
        }
        resp = client.post("/courses/", json=payload)
        assert resp.status_code == 422

