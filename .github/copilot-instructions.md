# Copilot Instructions for LMS JSON-Backed Microservice

## Project Overview
A FastAPI microservice implementing a Learning Management System with a JSON-backed data layer. The project is containerized with Docker and uses file-based persistence with atomic writes and file locking to ensure data consistency across concurrent requests. Features comprehensive error handling, monitoring, and notification systems.

## Architecture

### Layered Structure
- **Routes** (`src/app/routes/courses.py`): FastAPI routers handling HTTP endpoints
- **Services** (`src/app/application/services.py`): Business logic layer (CourseService, EnrollmentService)
- **Repository** (`src/app/persistence/json_repo.py`): Data access layer with file locking
- **Schemas** (`src/app/schemas.py`): Pydantic models for validation (CourseCreate, CourseOut, EnrollmentCreate)

### Data Persistence Pattern
- **Single JSON file**: `/data/lms_data.json` (host: `./data/`) contains all data (users, courses, enrollments, etc.)
- **File locking**: Uses `filelock` to prevent concurrent write conflicts with 5-second timeout
- **Atomic writes**: Writes to temporary file then replaces original (never partial writes)
- **Default structure**: JSONRepository initializes with empty collections if file doesn't exist

### Key Data Flow
```
HTTP Request → Route (Depends → get_repo) → Service → JSONRepository 
→ Read/Write JSON with FileLock → HTTP Response
```

## Error Handling & Monitoring

### Exception Hierarchy
- `LMSException` (base): All custom exceptions inherit from this with `error_code` and `details`
- `DataPersistenceError`: JSON read/write failures
- `FileLockError`: File lock timeouts (5-second timeout configured)
- `CourseNotFoundError`: Course lookup failures (404 response)
- `ValidationError`: Input validation failures (422 response)
- `BulkEnrollmentError`: Bulk enrollment failures
- `ConfigurationError`: Missing critical config

### Error Tracking (`src/app/core/error_tracking.py`)
- `ErrorTracker` logs all errors to `/data/error_log.jsonl` (JSON Lines format)
- Tracks error count and marks sessions as "critical failure" if >5 errors occur
- Determines severity: CRITICAL (file/persistence), WARNING (validation), INFO (other)
- Provides `/errors` endpoint to retrieve statistics and recent alerts

### Notifications (`src/app/core/notifications.py`)
- `NotificationService` writes critical error alerts to `/data/alerts/` directory
- Environment variable `ALERT_EMAIL` enables email notifications (placeholder for production SMTP/SES integration)
- Alerts written as JSON files: `alert_{ERROR_CODE}_{TIMESTAMP}.json`
- Route `/errors` exposes recent alerts for monitoring dashboards

### Global Exception Handlers (in `main.py`)
- `LMSException`: Returns appropriate HTTP status (404 for not found, 422 for validation, 503 for service unavailable)
- `Exception` (generic): Logs unhandled exceptions, notifies, returns 500
- Both trigger alerts through notification service for severity >= CRITICAL

## Crash Recovery & Restart

### Docker Restart Policy
- `restart: always` in docker-compose ensures container auto-restarts on crash
- Health check (`GET /health`) runs every 30s with 3 retries before marking unhealthy
- Unhealthy container triggers automatic restart by Docker daemon
- Logs preserved: JSON logging driver with max 10MB per file, 3 files rotation

### Health Check Endpoint
- `GET /health`: Returns `{"status": "healthy"|"degraded", "errors": {...}, "alerts": [...]}`
- Status = "degraded" if error_count > 5 (triggers restart consideration)
- Returns recent 3 alerts and error statistics
- Used by Docker and external monitoring systems

### Data Durability
- All data persisted to `/data/lms_data.json` (mounted volume, survives restarts)
- Error logs: `/data/error_log.jsonl` (JSONL format for log ingestion)
- Alert files: `/data/alerts/` directory

## Critical Developer Workflows

### Running Tests
```powershell
# Requires 85% coverage minimum
pytest --cov=src --cov-fail-under=85

# Run specific test file
pytest tests/test_error_handling.py -v

# Run with detailed output
pytest --cov=src --cov-report=html --cov-fail-under=85
```

Test categories:
- `test_courses_api.py`: HTTP endpoint tests
- `test_repos.py`: JSON repository persistence tests
- `test_error_handling.py`: Exception, error tracking, notification, recovery tests

### Running Locally (Development)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATA_FILE_PATH = "$PWD\data\lms_data.json"
$env:ALERT_EMAIL = "admin@example.com"  # Optional
$env:ALERTS_DIR = "$PWD\data\alerts"
uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running with Docker
```powershell
# Build and run
docker compose up --build

# Run with custom alert email
$env:ALERT_EMAIL = "admin@example.com"; docker compose up --build

# View logs
docker compose logs -f backend

# Run tests in container
docker compose exec backend pytest --cov=src --cov-fail-under=85
```

## Project-Specific Patterns

### Dependency Injection for Repository
Routes use FastAPI's `Depends()` with `get_repo()` function to create fresh JSONRepository instances per request. This ensures each request reads current file state.

### Bulk Enrollment with Background Tasks
- Endpoint accepts CSV file upload via multipart form
- Returns immediately with `{"status": "accepted"}`
- Background task `background_bulk_enroll()` parses CSV and processes enrollments
- Generates report JSON file named `bulk_enroll_report_{course_id}_{timestamp}.json` in data directory
- Enforces constraint: student cannot enroll in >5 active courses
- Errors logged and notified via alert system

### UUID Handling
- All IDs (`id`, `professor_id`, `student_id`) are UUID strings in JSON
- Pydantic models use `uuid.UUID` type for validation; converted to strings on persistence
- Example: `professor_id: UUID` in schema becomes `"professor_id": "00000000-0000..."` in JSON

### Course Level Validation
Level field restricted to enum: `beginner`, `intermediate`, `advanced` (enforced in schema with regex pattern).

### Error Response Format
All errors follow consistent format:
```json
{
  "message": "Human-readable message",
  "error_code": "MACHINE_READABLE_CODE",
  "details": { "context": "additional info" }
}
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `src/app/main.py` | App factory; startup/shutdown hooks; exception handlers; health/errors endpoints |
| `src/app/core/exceptions.py` | Custom exception classes with error codes and details |
| `src/app/core/error_tracking.py` | ErrorTracker for logging errors to JSONL, severity determination, statistics |
| `src/app/core/notifications.py` | NotificationService for alert files and email (placeholder) |
| `src/app/persistence/json_repo.py` | Core data access with FileLock; read/write all JSON operations |
| `src/app/routes/courses.py` | HTTP endpoints; validates courses exist before enrollment |
| `src/app/tasks.py` | Parse CSV and background bulk enrollment with error handling |
| `requirements.txt` | Dependencies: FastAPI, Pydantic, filelock, python-multipart, pytest, structlog, python-json-logger |
| `tests/conftest.py` | Fixtures: `client` (TestClient) and `data_file` (tmp_path) |
| `tests/test_error_handling.py` | Exception, tracking, notification, recovery, and concurrent access tests |
| `docker-compose.yml` | Service config with restart policy, health check, volume mounts, logging |
| `Dockerfile` | Build: Python 3.11, installs deps, exposes port 8000 |

## Infrastructure & Deployment

### Docker Compose Configuration
- **Container name**: `lms-backend`
- **Restart policy**: `always` (auto-restart on crash)
- **Health check**: Runs `curl http://localhost:8000/health` every 30s; 3 retries, 10s timeout
- **Volumes**: `./data:/data` persists JSON, logs, alerts; `./src:/app/src` for live code reload in development
- **Logging**: JSON driver, max 10MB per file, 3 files rotation
- **Environment**:
  - `DATA_FILE_PATH=/data/lms_data.json`
  - `ALERT_EMAIL` (optional, enables email alerts)
  - `ALERTS_DIR=/data/alerts`

### Terraform Infrastructure (GCP)
- **Google Cloud Storage bucket** for LMS materials
- **GCS bucket for Terraform state** (for remote state management)
- Configure via variables: `gcp_project`, `gcp_region`, `gcs_bucket_name`, `tf_state_bucket_name`

### Monitoring
- Health check exposes error statistics via `/health` and `/errors` endpoints
- Error logs: `/data/error_log.jsonl` (can be ingested into CloudLogging, DataDog, etc.)
- Alert files: `/data/alerts/` (can be polled or streamed)
- Docker daemon monitors container health; unhealthy containers trigger restart

## Testing

### Test Structure
1. **Unit tests** (`test_repos.py`): JSON repository operations, atomicity, concurrency
2. **Integration tests** (`test_courses_api.py`): HTTP endpoints, Pydantic validation, business logic
3. **Error handling tests** (`test_error_handling.py`):
   - Exception classes and hierarchy
   - Error tracking and statistics
   - Notifications and alert files
   - Recovery from JSON corruption
   - File lock timeout handling
   - Concurrent access patterns

### Test Fixtures (from `conftest.py`)
- `data_file`: Temporary file per test (monkeypatched `DATA_FILE_PATH`)
- `client`: FastAPI TestClient with isolated data file

### Coverage Requirements
Minimum 85% coverage enforced by CI; use `--cov-report=html` for detailed reports.

## Common Tasks

### Adding a New Endpoint
1. Define schema in `schemas.py` (Pydantic model)
2. Add method to service class (`CourseService` or `EnrollmentService`)
3. Add repository method to `JSONRepository` with file locking; wrap with error handling
4. Create route in `routes/courses.py` using `Depends(get_repo)` for repo injection
5. Add tests to `test_courses_api.py`
6. If critical data operations, add error handling tests to `test_error_handling.py`

### Modifying JSON Structure
Edit `DEFAULT_STRUCTURE` in `json_repo.py`. Existing instances auto-initialize missing keys via `setdefault()`.

### Testing
Use `client` fixture from conftest; monkeypatched `DATA_FILE_PATH` provides isolation. No cleanup needed (tmp_path auto-deleted).

### Debugging Errors
1. Check `/data/error_log.jsonl` for detailed error records with timestamps and severity
2. Check `/data/alerts/` for critical alerts
3. Call `GET /errors` endpoint to view recent alerts and statistics
4. Use `docker compose logs backend` to see application logs
5. Use `docker compose exec backend pytest test_error_handling.py -v -s` to run tests with output

## External Dependencies & Configuration

- **Environment variables**:
  - `DATA_FILE_PATH`: Path to JSON data file (default: `/data/lms_data.json`)
  - `ALERT_EMAIL`: Email for alerts (optional, placeholder for SMTP setup)
  - `ALERTS_DIR`: Directory for alert files (default: `/data/alerts`)
- **Dependencies**: filelock (concurrency), python-multipart (file uploads), pytest-cov (testing), structlog, python-json-logger (logging)
- **Container**: Docker Compose mounts `./data` volume for persistence

## Integration Points

- **CSV bulk enrollment** expects columns: `email`, `first_name` (optional), `last_name` (optional)
- **Health check endpoint**: `GET /health` returns status, errors, and recent alerts
- **Errors endpoint**: `GET /errors` returns full stats and recent alerts
- **All endpoints** return JSON; validation errors return 422 (Pydantic validation)
- **Missing course** returns 404 for bulk enrollment endpoints
- **Service unavailable** returns 503 if file lock timeout or persistence error
- **Critical errors** trigger alert files and notification attempts
