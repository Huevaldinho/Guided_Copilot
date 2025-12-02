import json
import os
import tempfile
import uuid
from typing import Any, Dict, List, Optional
from filelock import FileLock
from datetime import datetime

DEFAULT_STRUCTURE = {
    "users": [],
    "profiles": [],
    "courses": [],
    "classes": [],
    "enrollments": []
}

class JSONRepository:
    def __init__(self, path: str):
        self.path = path
        self.lock_path = f"{self.path}.lock"
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self._write_data(DEFAULT_STRUCTURE)

    def _read_data(self) -> Dict[str, Any]:
        lock = FileLock(self.lock_path)
        with lock:
            if not os.path.exists(self.path):
                return json.loads(json.dumps(DEFAULT_STRUCTURE))
            with open(self.path, "r", encoding="utf-8") as fh:
                try:
                    data = json.load(fh)
                except json.JSONDecodeError:
                    return json.loads(json.dumps(DEFAULT_STRUCTURE))
        return data

    def _write_data(self, data: Dict[str, Any]) -> None:
        lock = FileLock(self.lock_path)
        with lock:
            dir_name = os.path.dirname(self.path)
            with tempfile.NamedTemporaryFile("w", delete=False, dir=dir_name, encoding="utf-8") as tf:
                json.dump(data, tf, ensure_ascii=False, indent=2, default=str)
                tmpname = tf.name
            os.replace(tmpname, self.path)

    # Course operations
    def list_courses(self) -> List[Dict[str, Any]]:
        data = self._read_data()
        return data.get("courses", [])

    def create_course(self, course_in: Dict[str, Any]) -> Dict[str, Any]:
        data = self._read_data()
        course = {
            "id": str(uuid.uuid4()),
            "title": course_in.get("title"),
            "description": course_in.get("description"),
            "professor_id": str(course_in.get("professor_id")),
            "duration_hours": course_in.get("duration_hours"),
            "level": course_in.get("level"),
            "created_at": datetime.utcnow().isoformat()
        }
        data.setdefault("courses", []).append(course)
        self._write_data(data)
        return course

    def get_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        courses = self.list_courses()
        for c in courses:
            if c["id"] == course_id:
                return c
        return None

    # Enrollment helpers (simple)
    def create_user_if_not_exists(self, email: str, first_name: str = "", last_name: str = "") -> Dict[str, Any]:
        data = self._read_data()
        users = data.setdefault("users", [])
        for u in users:
            if u.get("email") == email:
                return u
        user = {"id": str(uuid.uuid4()), "email": email, "role": "student", "is_active": True, "created_at": datetime.utcnow().isoformat()}
        users.append(user)
        data["users"] = users
        self._write_data(data)
        return user

    def count_active_enrollments_for_student(self, user_email: str) -> int:
        data = self._read_data()
        enrollments = data.get("enrollments", [])
        student_enrollments = [e for e in enrollments if e.get("student_email") == user_email and not e.get("completed", False)]
        return len(student_enrollments)

    def create_enrollment(self, student_email: str, course_id: str) -> Dict[str, Any]:
        data = self._read_data()
        enrollment = {
            "id": str(uuid.uuid4()),
            "student_email": student_email,
            "course_id": course_id,
            "enrolled_at": datetime.utcnow().isoformat(),
            "progress_percentage": 0,
            "completed": False,
            "completion_date": None
        }
        data.setdefault("enrollments", []).append(enrollment)
        self._write_data(data)
        return enrollment

    def bulk_enroll(self, course_id: str, rows: List[Dict[str, str]]) -> Dict[str, Any]:
        report = {"total": len(rows), "enrolled": 0, "skipped": 0, "errors": []}
        for idx, row in enumerate(rows, start=1):
            try:
                email = (row.get("email") or "").strip()
                if not email:
                    raise ValueError("missing email")
                active_count = self.count_active_enrollments_for_student(email)
                if active_count >= 5:
                    report["skipped"] += 1
                    continue
                self.create_user_if_not_exists(email, row.get("first_name", ""), row.get("last_name", ""))
                self.create_enrollment(email, course_id)
                report["enrolled"] += 1
            except Exception as exc:
                report["errors"].append({"row": idx, "error": str(exc)})
        return report
