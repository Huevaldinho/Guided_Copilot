# Error Handling & Monitoring Implementation Summary

## Overview
Implemented a comprehensive error handling, monitoring, and recovery system for the LMS microservice. The system ensures automatic recovery from crashes, detailed error tracking, and notifications for critical issues.

## What Was Implemented

### 1. **Custom Exception Hierarchy** (`src/app/core/exceptions.py`)
- `LMSException`: Base exception with error_code and details
- Specific exceptions: `DataPersistenceError`, `FileLockError`, `CourseNotFoundError`, `ValidationError`, `BulkEnrollmentError`, `ConfigurationError`
- All return consistent JSON error format with HTTP status codes

### 2. **Error Tracking System** (`src/app/core/error_tracking.py`)
- `ErrorTracker` logs all errors to `/data/error_log.jsonl` (JSON Lines format)
- Tracks:
  - Error count, timestamps, severity levels
  - Error types, codes, and contextual details
  - Marks "critical failure" state if >5 errors occur in a session
- Provides:
  - `log_error()`: Records errors to file and determines severity
  - `get_error_stats()`: Returns current error statistics
  - `is_critical_failure()`: Checks if threshold exceeded

### 3. **Notification Service** (`src/app/core/notifications.py`)
- `NotificationService` handles multi-channel alerts
- **Alert files**: Writes critical errors to `/data/alerts/alert_{CODE}_{TIMESTAMP}.json`
- **Email alerts**: Placeholder for SMTP/SendGrid integration (triggered on CRITICAL severity)
- `get_recent_alerts()`: Returns last N alert files for dashboard integration

### 4. **Global Exception Handlers** (updated `src/app/main.py`)
- `@app.exception_handler(LMSException)`: Catches all custom exceptions
  - Returns appropriate HTTP status (404, 422, 503, 500)
  - Triggers notifications for critical errors
- `@app.exception_handler(Exception)`: Catches unhandled exceptions
  - Logs unexpected errors
  - Returns 500 with error details
- **Startup/Shutdown hooks**: Log initialization and final error statistics

### 5. **Enhanced Endpoints**
- **`GET /health`**: 
  - Returns `{"status": "healthy"|"degraded", "errors": {...}, "alerts": [...]}`
  - Status = "degraded" if error_count > 5
  - Used by Docker health checks
- **`GET /errors`**: 
  - Returns full error statistics and recent alerts
  - Useful for monitoring dashboards

### 6. **Docker Auto-Recovery** (updated `docker-compose.yml`)
- **`restart: always`**: Container automatically restarts on crash or exit
- **Health check**: Runs every 30 seconds, marks unhealthy after 3 failures
- **JSON logging**: Max 10MB per file, 3 files rotation (for audit trail)
- **Environment variables**:
  - `ALERT_EMAIL` (optional): Email for critical alerts
  - `ALERTS_DIR`: Directory for alert files
  - `DATA_FILE_PATH`: Location of JSON data file

### 7. **Robust Data Access** (updated `src/app/persistence/json_repo.py`)
- **File lock timeout**: 5-second timeout (prevents deadlocks)
- **Timeout handling**: Throws `FileLockError` on timeout
- **JSON corruption recovery**: Returns default structure on parse errors, logs issue
- **Atomic writes**: Still using temp file + replace pattern
- **Error logging**: All read/write failures logged with details

### 8. **Enhanced Background Tasks** (updated `src/app/tasks.py`)
- **Error logging**: Catches and logs bulk enrollment failures
- **Partial success reporting**: Still generates report even with errors
- **Critical alerts**: Notifies on task failure
- **Graceful degradation**: Doesn't crash on individual row errors

### 9. **Comprehensive Test Suite** (`tests/test_error_handling.py`)
- Tests for all exception types
- ErrorTracker: logging, severity, statistics, critical failure threshold
- NotificationService: alert file creation, email placeholder, recent alerts
- Recovery scenarios: JSON corruption, file lock timeouts, concurrent writes
- 15+ test cases covering error paths

### 10. **Enhanced Dependencies** (`requirements.txt`)
Added:
- `structlog>=23.2.0`: Structured logging
- `python-json-logger>=2.0.7`: JSON log formatting

## Crash Recovery Flow

```
Container crashes or exits
           ↓
Docker daemon detects (via health check or exit code)
           ↓
`restart: always` policy triggers
           ↓
New container starts
           ↓
`startup()` hook initializes error tracker & notifications
           ↓
Data persists from mounted volume (`./data`)
           ↓
Error logs and alerts available in `/data/error_log.jsonl` and `/data/alerts/`
```

## Notification Triggers

**CRITICAL severity** (triggers notification):
- File lock timeout
- Data persistence errors
- Configuration errors
- Unhandled exceptions

**WARNING severity** (logged, no email):
- Validation errors
- Bulk enrollment errors
- Partial failures

**INFO severity** (debug logging only):
- Normal operations

## File Locations

| Path | Purpose |
|------|---------|
| `/data/lms_data.json` | Persistent data file (survives restarts) |
| `/data/error_log.jsonl` | Error log (JSON Lines, one record per line) |
| `/data/alerts/` | Directory of alert JSON files |
| `./data/` | Host folder mounted to container |

## Usage Examples

### Check Application Health
```powershell
curl http://localhost:8000/health
```

### View Recent Errors & Alerts
```powershell
curl http://localhost:8000/errors
```

### Check Error Log
```powershell
tail -f ./data/error_log.jsonl
```

### View Alert Files
```powershell
ls ./data/alerts/
cat ./data/alerts/alert_CRITICAL_20250101120000.json
```

### Run with Email Alerts (Development)
```powershell
$env:ALERT_EMAIL = "admin@example.com"
docker compose up --build
```

### Test Error Recovery
```powershell
# Create invalid JSON to trigger recovery
echo "{invalid" > ./data/lms_data.json

# App recovers, logs error
curl http://localhost:8000/health

# Check error log
cat ./data/error_log.jsonl
```

## Production Considerations

1. **Email Integration**: Replace placeholder in `notifications.py` with SMTP/SendGrid
2. **Log Aggregation**: Ingest `/data/error_log.jsonl` into CloudLogging, DataDog, or ELK
3. **Alert Monitoring**: Poll `/data/alerts/` or expose via monitoring dashboard
4. **Database Migration**: Replace JSON with proper database for production scale
5. **Distributed Locking**: Use Redis for file locking if multi-instance deployment
6. **Health Checks**: Integrate `GET /health` with load balancers and orchestration platforms

## Key Metrics for Monitoring

- `error_count`: Total errors in session (reset on restart)
- `last_error_time`: ISO timestamp of last error
- `is_critical_failure`: Boolean (true if >5 errors)
- `recent_alerts`: List of recent critical alerts

## Testing

```powershell
# Run all tests with coverage
pytest --cov=src --cov-fail-under=85

# Run only error handling tests
pytest tests/test_error_handling.py -v

# Run with detailed output
pytest tests/test_error_handling.py -v -s

# Generate HTML coverage report
pytest --cov=src --cov-report=html
```

## Files Modified

1. `requirements.txt` - Added structlog, python-json-logger
2. `src/app/main.py` - Global exception handlers, health/errors endpoints
3. `src/app/core/exceptions.py` - NEW: Custom exception hierarchy
4. `src/app/core/error_tracking.py` - NEW: Error tracking and statistics
5. `src/app/core/notifications.py` - NEW: Alert notifications
6. `src/app/persistence/json_repo.py` - Added error handling, timeout
7. `src/app/routes/courses.py` - Enhanced logging, error raising
8. `src/app/tasks.py` - Added error handling, notifications
9. `docker-compose.yml` - Added restart, health check, logging
10. `.github/copilot-instructions.md` - Updated with comprehensive sections
11. `tests/test_error_handling.py` - NEW: 15+ error handling tests

## Next Steps (Optional)

1. Configure real email alerts (SMTP or SendGrid API key)
2. Set up log aggregation pipeline
3. Create monitoring dashboard for `/health` and `/errors` endpoints
4. Implement circuit breaker pattern for external service calls
5. Add metrics export (Prometheus format)
6. Add distributed tracing for request debugging
