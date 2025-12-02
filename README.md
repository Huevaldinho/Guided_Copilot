# LMS Exercise - Milestone 1 (JSON data layer)

This project is a FastAPI microservice implementing a JSON-backed Milestone 1.

## Key points
- Data file: `/data/lms_data.json` inside the container. Host folder `./data` is mounted.
- Atomic writes + file locking via `filelock`.
- Endpoints: `POST /courses/` to create courses; `POST /courses/{course_id}/enrollments/bulk` accepts CSV file upload and processes it in a background task.
- Tests: `pytest --cov=src --cov-fail-under=85`.

## Quickstart (PowerShell)

1. Install dependencies locally:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run locally:
```powershell
$env:DATA_FILE_PATH = "$PWD\data\lms_data.json"
uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
```

3. Run with Docker Compose:
```powershell
docker compose up --build
```

4. Verify:
```powershell
curl -X POST "http://localhost:8000/courses" -H "Content-Type: application/json" -d "{\"title\":\"Intro\",\"description\":\"desc\",\"professor_id\":\"00000000-0000-0000-0000-000000000000\",\"duration_hours\":10,\"level\":\"beginner\"}"
```
