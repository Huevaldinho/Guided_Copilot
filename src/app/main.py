from fastapi import FastAPI
from .routes import courses
from .core.config import get_data_file_path
import os

def create_app():
    app = FastAPI(title="LMS Exercise (JSON-backed)")
    app.include_router(courses.router)
    @app.on_event("startup")
    def startup():
        data_path = get_data_file_path()
        dirp = os.path.dirname(data_path)
        if not os.path.exists(dirp):
            os.makedirs(dirp, exist_ok=True)
    @app.get("/health")
    def health():
        return {"status": "ok"}
    return app

app = create_app()
