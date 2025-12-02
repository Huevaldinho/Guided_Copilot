"""
Tests for JSON Repository persistence layer.
"""

import allure
import tempfile
import json
from src.app.persistence.json_repo import JSONRepository
import os


@allure.feature("Data Persistence")
@allure.story("Course Repository")
class TestJSONRepositoryCourses:
    """Test course repository operations."""

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("unit", "persistence", "crud", "happy-path")
    @allure.title("Create course in repository")
    @allure.description("Verify that courses are properly created and persisted")
    def test_json_repo_create_course(self):
        """Test course creation in JSON repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            repo = JSONRepository(path)
            course_in = {
                "title": "Python 101",
                "description": "Learn Python",
                "professor_id": "prof-1",
                "duration_hours": 10,
                "level": "beginner"
            }
            course = repo.create_course(course_in)
            assert course["title"] == "Python 101"
            assert "id" in course
            assert os.path.exists(path)

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("unit", "persistence", "crud", "retrieval")
    @allure.title("List all courses from repository")
    @allure.description("Verify that multiple courses can be listed")
    def test_json_repo_list_courses(self):
        """Test listing courses from repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            repo = JSONRepository(path)
            course1 = repo.create_course({
                "title": "Course 1",
                "description": "Desc",
                "professor_id": "prof-1",
                "level": "beginner"
            })
            course2 = repo.create_course({
                "title": "Course 2",
                "description": "Desc",
                "professor_id": "prof-2",
                "level": "advanced"
            })
            courses = repo.list_courses()
            assert len(courses) == 2
            assert any(c["id"] == course1["id"] for c in courses)

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("unit", "persistence", "crud", "retrieval")
    @allure.title("Get individual course by ID")
    @allure.description("Verify that courses can be retrieved by ID")
    def test_json_repo_get_course(self):
        """Test retrieving a specific course."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            repo = JSONRepository(path)
            created = repo.create_course({
                "title": "Find Me",
                "professor_id": "prof-1",
                "level": "beginner"
            })
            found = repo.get_course(created["id"])
            assert found is not None
            assert found["title"] == "Find Me"


@allure.feature("Data Persistence")
@allure.story("Atomic Write Operations")
class TestAtomicWrite:
    """Test atomic write operations."""

    @allure.severity(allure.severity_level.HIGH)
    @allure.tag("unit", "persistence", "data-integrity", "file-io")
    @allure.title("Verify atomic write to JSON file")
    @allure.description("Test that data is written atomically to maintain JSON integrity")
    def test_json_repo_atomic_write(self):
        """Test that writes are atomic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            repo = JSONRepository(path)
            repo.create_course({
                "title": "Course 1",
                "professor_id": "prof-1",
                "level": "beginner"
            })
            with open(path, "r") as fh:
                data = json.load(fh)
            assert "courses" in data
            assert len(data["courses"]) == 1


@allure.feature("User Management")
@allure.story("User Repository")
class TestJSONRepositoryUsers:
    """Test user repository operations."""

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("unit", "persistence", "crud", "users")
    @allure.title("Create or get existing user")
    @allure.description("Verify idempotent user creation")
    def test_json_repo_create_user_if_not_exists(self):
        """Test idempotent user creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            repo = JSONRepository(path)
            user1 = repo.create_user_if_not_exists("test@example.com", "Test", "User")
            assert user1["email"] == "test@example.com"
            user2 = repo.create_user_if_not_exists("test@example.com", "Test", "User")
            assert user1["id"] == user2["id"]


@allure.feature("Enrollment Management")
@allure.story("Enrollment Operations")
class TestJSONRepositoryEnrollments:
    """Test enrollment repository operations."""

    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("unit", "persistence", "crud", "enrollments")
    @allure.title("Count active enrollments for student")
    @allure.description("Verify enrollment counting works correctly")
    def test_json_repo_count_active_enrollments(self):
        """Test counting active enrollments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            repo = JSONRepository(path)
            course = repo.create_course({
                "title": "Course",
                "professor_id": "prof-1",
                "level": "beginner"
            })
            repo.create_user_if_not_exists("student@example.com")
            repo.create_enrollment("student@example.com", course["id"])
            count = repo.count_active_enrollments_for_student("student@example.com")
            assert count == 1

    @allure.severity(allure.severity_level.HIGH)
    @allure.tag("integration", "persistence", "enrollment-limit", "defect")
    @allure.title("Enforce maximum enrollment limit per student")
    @allure.description("Verify that students cannot exceed 5 active courses")
    def test_json_repo_bulk_enroll_max_5_enrollments(self):
        """Test maximum enrollment limit enforcement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.json")
            repo = JSONRepository(path)
            courses = [repo.create_course({
                "title": f"Course {i}",
                "professor_id": "prof-1",
                "level": "beginner"
            }) for i in range(6)]
            for course in courses:
                repo.create_user_if_not_exists("student@example.com")
                repo.create_enrollment("student@example.com", course["id"])
            rows = [{"email": "student@example.com", "first_name": "New", "last_name": "Enroll"}]
            report = repo.bulk_enroll(courses[0]["id"], rows)
            assert report["skipped"] >= 1
