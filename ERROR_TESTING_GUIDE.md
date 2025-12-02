# Error Handling Quick Reference & Testing Guide

## How to Trigger Errors for Testing

### 1. **Trigger Data Persistence Error**
```powershell
# Make data directory read-only
chmod 555 ./data   # Linux/WSL
icacls ".\data" /grant:r Everyone:F; icacls ".\data" /deny Everyone:W  # Windows

# Try to create a course
curl -X POST "http://localhost:8000/courses" `
  -H "Content-Type: application/json" `
  -d '{"title":"Test","professor_id":"00000000-0000-0000-0000-000000000000"}'

# Should return 503: Service Unavailable
# Error logged to ./data/error_log.jsonl
# Alert created in ./data/alerts/

# Restore permissions
chmod 755 ./data
```

### 2. **Trigger File Lock Timeout**
```powershell
# Lock the JSON file (simulating another process)
# Linux/WSL:
# flock -x ./data/lms_data.json -c 'sleep 30' &

# While locked, try operations:
curl -X POST "http://localhost:8000/courses" `
  -H "Content-Type: application/json" `
  -d '{"title":"Test","professor_id":"00000000-0000-0000-0000-000000000000"}'

# After 5 seconds (lock timeout): 503 Service Unavailable
```

### 3. **Trigger JSON Corruption Recovery**
```powershell
# Corrupt the data file
echo "{invalid json" > ./data/lms_data.json

# Try operation (should recover with default structure)
curl http://localhost:8000/courses

# Check error log
cat ./data/error_log.jsonl

# Application recovers with empty course list
```

### 4. **Trigger Validation Error**
```powershell
# Invalid level (not beginner/intermediate/advanced)
curl -X POST "http://localhost:8000/courses" `
  -H "Content-Type: application/json" `
  -d '{"title":"Test","professor_id":"00000000-0000-0000-0000-000000000000","level":"invalid"}'

# Returns 422: Unprocessable Entity
```

### 5. **Trigger Course Not Found Error**
```powershell
# Try to enroll in non-existent course
curl -X POST "http://localhost:8000/courses/fake-course-id/enrollments/bulk" `
  -F "file=@enrollment.csv"

# Returns 404: Not Found
# Alert created for this critical error
```

### 6. **Trigger Bulk Enrollment Error**
```powershell
# Create CSV with invalid/missing email
echo "email,first_name,last_name" > enrollment.csv
echo ",John,Doe" >> enrollment.csv
echo "invalid@example.com,Jane,Smith" >> enrollment.csv

# Create course first
$courseId = (curl -X POST "http://localhost:8000/courses" `
  -H "Content-Type: application/json" `
  -d '{"title":"Test","professor_id":"00000000-0000-0000-0000-000000000000"}' | ConvertFrom-Json).id

# Bulk enroll (will skip first row, enroll second)
curl -X POST "http://localhost:8000/courses/$courseId/enrollments/bulk" `
  -F "file=@enrollment.csv"

# Check bulk enrollment report
ls ./data/bulk_enroll_report_*.json
cat ./data/bulk_enroll_report_*.json
```

### 7. **Trigger Critical Failure (>5 errors)**
```powershell
# Run multiple failing operations to exceed error threshold
for ($i=1; $i -le 6; $i++) {
  curl -X POST "http://localhost:8000/courses" `
    -H "Content-Type: application/json" `
    -d '{"title":"Test","level":"invalid"}' | ConvertFrom-Json
}

# Check health endpoint - should show degraded
curl http://localhost:8000/health | ConvertFrom-Json
```

## Monitoring Error States

### **Real-time Error Log Monitoring**
```powershell
# Watch error log as it grows
Get-Content -Path "./data/error_log.jsonl" -Wait

# Or on Linux/WSL:
tail -f ./data/error_log.jsonl
```

### **Check Health Status**
```powershell
# Get current health and error stats
curl http://localhost:8000/health | ConvertFrom-Json | ConvertTo-Json -Depth 5

# Response format:
# {
#   "status": "healthy" or "degraded",
#   "errors": {
#     "total_errors": 5,
#     "last_error_time": "2025-01-01T12:00:00.000000",
#     "log_file": "/data/error_log.jsonl"
#   },
#   "alerts": [...]
# }
```

### **View Recent Alerts**
```powershell
# Get recent critical alerts
curl http://localhost:8000/errors | ConvertFrom-Json | ConvertTo-Json -Depth 10

# Or check alert files directly
dir ./data/alerts/

# View specific alert
cat ./data/alerts/alert_FILE_LOCK_ERROR_20250101120000.json
```

## Log File Formats

### **Error Log** (`./data/error_log.jsonl`)
One JSON object per line:
```json
{
  "timestamp": "2025-01-01T12:00:00.123456",
  "error_count": 1,
  "error_type": "DataPersistence",
  "message": "Failed to read data: ...",
  "error_code": "DATA_READ_ERROR",
  "details": {"file_path": "/data/lms_data.json"},
  "severity": "CRITICAL",
  "exception": "PermissionError: ...",
  "exc_type": "PermissionError"
}
```

### **Alert Files** (`./data/alerts/alert_*.json`)
```json
{
  "timestamp": "2025-01-01T12:00:00.123456",
  "error_type": "DataPersistence",
  "message": "Failed to read data: ...",
  "error_code": "DATA_READ_ERROR",
  "severity": "CRITICAL",
  "details": {"file_path": "/data/lms_data.json"}
}
```

## Docker Container Restart Testing

### **Force Container Crash**
```powershell
# Get container ID
docker compose ps

# Kill container (simulates crash)
docker compose kill backend

# Container automatically restarts (watch logs)
docker compose logs -f backend
```

### **Watch Auto-Recovery**
```powershell
# Terminal 1: Watch logs
docker compose logs -f backend

# Terminal 2: Kill container
docker compose kill backend

# Observe: Container exits → Docker restarts → App initializes → Health check passes
```

### **Check Container Restart Count**
```powershell
# View restart stats
docker inspect lms-backend | Select-String "RestartCount"
```

## Health Check Validation

### **Container Health Status**
```powershell
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# Output shows: "Up X seconds (healthy)" or "Up X seconds (unhealthy)"
```

### **Simulate Unhealthy State**
```powershell
# Make many errors to trigger degraded status
for ($i=1; $i -le 10; $i++) {
  curl -X POST "http://localhost:8000/courses" `
    -H "Content-Type: application/json" `
    -d '{"title":"X","level":"x"}' 2>&1 | Out-Null
  Start-Sleep -Milliseconds 100
}

# Wait 30+ seconds for health check to run
Start-Sleep -Seconds 35

# Check status (should still be "healthy" as health check runs success test separately)
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## Email Alert Setup (Production)

### **Using SendGrid**
```powershell
# Set environment variable with SendGrid API key
$env:SENDGRID_API_KEY = "SG.xxxxxxxxxxxxx"

# Update environment in docker-compose.yml:
# environment:
#   - SENDGRID_API_KEY=${SENDGRID_API_KEY}
#   - ALERT_EMAIL=admin@example.com

# Or for local development:
docker compose up --build
```

### **Using SMTP**
Update `src/app/core/notifications.py` `_send_email_alert()` with:
```python
import smtplib
from email.mime.text import MIMEText

# Configure SMTP server
smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
smtp_port = int(os.getenv("SMTP_PORT", "587"))
sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")

# Send email logic...
```

## Debugging Workflow

1. **Check recent errors**: `cat ./data/error_log.jsonl | tail -20`
2. **Check recent alerts**: `ls -lt ./data/alerts/ | head -10`
3. **Check health**: `curl http://localhost:8000/health`
4. **Check error statistics**: `curl http://localhost:8000/errors`
5. **Check Docker logs**: `docker compose logs backend`
6. **Restart app**: `docker compose restart backend`
7. **Full restart**: `docker compose down && docker compose up --build`

## Test Coverage

```powershell
# Run all tests with coverage
pytest --cov=src --cov-fail-under=85

# Run only error handling tests
pytest tests/test_error_handling.py -v

# Generate HTML coverage report
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

## Key Files for Debugging

| File | Contains |
|------|----------|
| `./data/error_log.jsonl` | All errors (queryable) |
| `./data/alerts/` | Critical alerts (one per incident) |
| `./data/bulk_enroll_report_*.json` | Enrollment task reports |
| `./data/lms_data.json` | Application data |
| `docker-compose.yml` | Container configuration |
| `.github/copilot-instructions.md` | Comprehensive documentation |

## Common Error Codes Reference

| Code | Meaning | HTTP Status | Severity |
|------|---------|-------------|----------|
| `FILE_LOCK_ERROR` | File locking timeout | 503 | CRITICAL |
| `DATA_PERSISTENCE_ERROR` | JSON read/write failure | 503 | CRITICAL |
| `COURSE_NOT_FOUND` | Course lookup failed | 404 | INFO |
| `VALIDATION_ERROR` | Input validation failed | 422 | WARNING |
| `BULK_ENROLLMENT_ERROR` | Enrollment processing failed | 400 | WARNING |
| `CONFIGURATION_ERROR` | Missing config variable | 500 | CRITICAL |
| `UNHANDLED_EXCEPTION` | Unexpected error | 500 | CRITICAL |
