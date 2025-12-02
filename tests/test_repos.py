import tempfile
import json
from src.app.persistence.json_repo import JSONRepository
import os

def test_json_repo_create_course():
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

def test_json_repo_list_courses():
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

def test_json_repo_get_course():
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

def test_json_repo_atomic_write():
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

def test_json_repo_create_user_if_not_exists():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.json")
        repo = JSONRepository(path)
        user1 = repo.create_user_if_not_exists("test@example.com", "Test", "User")
        assert user1["email"] == "test@example.com"
        user2 = repo.create_user_if_not_exists("test@example.com", "Test", "User")
        assert user1["id"] == user2["id"]

def test_json_repo_count_active_enrollments():
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

def test_json_repo_bulk_enroll_max_5_enrollments():
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
