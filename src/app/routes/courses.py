from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from typing import List
from ..schemas import CourseCreate
from ..persistence.json_repo import JSONRepository
from ..application.services import CourseService
from ..core.config import get_data_file_path
from ..tasks import background_bulk_enroll

router = APIRouter(prefix="/courses", tags=["courses"])

def get_repo():
    return JSONRepository(get_data_file_path())

@router.post("/", response_model=dict, status_code=201)
def create_course(payload: CourseCreate, repo: JSONRepository = Depends(get_repo)):
    service = CourseService(repo)
    course = service.create_course(payload.dict())
    return course

@router.get("/", response_model=List[dict])
def list_courses(repo: JSONRepository = Depends(get_repo)):
    service = CourseService(repo)
    return service.list_courses()

@router.post("/{course_id}/enrollments/bulk", response_model=dict)
def bulk_enroll(course_id: str, file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks(), repo: JSONRepository = Depends(get_repo)):
    if repo.get_course(course_id) is None:
        raise HTTPException(status_code=404, detail="Course not found")
    background_tasks.add_task(background_bulk_enroll, file.file, course_id)
    return {"status": "accepted", "detail": "bulk enroll started"}
