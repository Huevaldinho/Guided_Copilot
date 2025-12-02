from typing import List, Dict
from ..persistence.json_repo import JSONRepository

class CourseService:
    def __init__(self, repo: JSONRepository):
        self.repo = repo

    def create_course(self, course_in: Dict) -> Dict:
        return self.repo.create_course(course_in)

    def list_courses(self):
        return self.repo.list_courses()

class EnrollmentService:
    def __init__(self, repo: JSONRepository):
        self.repo = repo

    def bulk_enroll(self, course_id: str, rows: List[Dict[str, str]]):
        return self.repo.bulk_enroll(course_id, rows)
