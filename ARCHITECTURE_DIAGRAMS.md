# System Architecture & Error Handling Flow

## Application Architecture with Error Handling

```
┌─────────────────────────────────────────────────────────────────┐
│                     HTTP CLIENT REQUESTS                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI APPLICATION                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Global Exception Handlers (main.py)                    │  │
│  │  ├─ @app.exception_handler(LMSException)               │  │
│  │  ├─ @app.exception_handler(Exception)                  │  │
│  │  └─ Logs to ErrorTracker & NotificationService         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│         ┌───────────────────┼───────────────────┐              │
│         ▼                   ▼                   ▼              │
│  ┌─────────────┐    ┌──────────────┐   ┌────────────┐        │
│  │ Routes      │    │ Health Chk   │   │ Errors     │        │
│  │ /courses    │    │ /health      │   │ /errors    │        │
│  │ /enrollments│    │              │   │            │        │
│  └──────┬──────┘    └──────┬───────┘   └──────┬─────┘        │
│         │                  │                   │              │
│         └──────────────────┼───────────────────┘              │
│                            ▼                                  │
│              ┌──────────────────────────┐                    │
│              │  Services Layer         │                    │
│              │ ├─ CourseService        │                    │
│              │ └─ EnrollmentService    │                    │
│              └───────────┬──────────────┘                    │
│                          ▼                                  │
│       ┌──────────────────────────────────────┐             │
│       │  Repository Layer                   │             │
│       │  JSONRepository                     │             │
│       │  ├─ _read_data() [with FileLock]   │             │
│       │  ├─ _write_data() [with FileLock]  │             │
│       │  └─ Timeout: 5 seconds             │             │
│       └──────────────┬───────────────────────┘             │
│                      │                                     │
│                      ▼ (try/except wrapper)              │
│       ┌──────────────────────────────────────┐             │
│       │  Error Tracking                     │             │
│       │  └─ log_error() → JSONL file        │             │
│       └──────────────┬───────────────────────┘             │
│                      │                                     │
│                      ▼                                     │
│       ┌──────────────────────────────────────┐             │
│       │  Notifications                      │             │
│       │  ├─ Write alert file                │             │
│       │  └─ Email (CRITICAL only)           │             │
│       └──────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
    ┌─────────┐         ┌─────────┐         ┌─────────┐
    │ Mounted │         │ Error   │         │ Alert   │
    │ Volume  │         │ Log     │         │ Files   │
    │ Data    │         │ JSONL   │         │ JSON    │
    │         │         │         │         │         │
    │ ./data/ │         │ error_  │         │ alert_  │
    │         │         │ log.    │         │ CODE_   │
    └─────────┘         │ jsonl   │         │ TIME.   │
                        │         │         │ json    │
                        └─────────┘         └─────────┘
```

## Error Handling Decision Tree

```
┌────────────────────────────────┐
│ Request received by FastAPI    │
└────────────┬───────────────────┘
             │
             ▼
    ┌────────────────────┐
    │ Route handler      │
    │ executes           │
    └──┬──────────────┬──┘
       │              │
       │ Success      │ Exception thrown
       │              │
       ▼              ▼
   Response    ┌──────────────────────────┐
   (200-201)   │ LMSException raised?     │
               └──┬─────────────────┬──────┘
                  │ Yes             │ No
                  ▼                 ▼
         ┌────────────────┐   ┌──────────────┐
         │ Catch handler  │   │ Generic      │
         └─┬──────────────┘   │ Exception    │
           │                  │ handler      │
           │                  └──┬───────────┘
           │                     │
           ▼                     ▼
    ┌──────────────────────────────────────┐
    │ error_tracker.log_error()            │
    │ ├─ Increment error_count             │
    │ ├─ Write to error_log.jsonl          │
    │ └─ Determine severity                │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────┐
    │ Status >= 500 or CRITICAL severity? │
    └──┬───────────────────────────┬──────┘
       │ Yes                       │ No
       ▼                           ▼
┌──────────────────────────┐  Return error response
│ notification_service     │  with appropriate status
│ .notify_error()          │
│ ├─ Write alert file      │
│ ├─ Send email (CRITICAL) │
│ └─ Log notification      │
└──┬───────────────────────┘
   │
   ▼
Return error response
(404/422/503/500 + JSON body)
```

## Docker Container Lifecycle with Health Checks

```
┌──────────────────────┐
│ docker compose up    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────┐
│ Build image & Start container│
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ App startup()                │
│ ├─ Initialize ErrorTracker   │
│ ├─ Initialize NotifyService  │
│ └─ Create data directory     │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Container running            │
│ (start_period: 10 seconds)   │
└──────────┬───────────────────┘
           │
           ├─ Health check every 30 seconds
           │  curl http://localhost:8000/health
           │
           ├─ Success (status: 200)
           │  └─ Container marked "healthy"
           │
           ├─ Failure (status: 500/timeout)
           │  └─ Retry counter++
           │     (until 3 failures)
           │
           │  3 failures reached?
           │  ├─ Yes → Container marked "unhealthy"
           │  │        Docker daemon can auto-restart
           │  │        (depends on restart policy)
           │  │
           │  └─ No → Continue monitoring
           │
           ▼
┌──────────────────────────────┐
│ Application crash or exit    │
│ (e.g., unhandled exception)  │
└──────────┬───────────────────┘
           │
    restart: always
    policy activates
           │
           ▼
┌──────────────────────────────┐
│ Docker restarts container    │
│ Repeat from "App startup()"  │
└──────────────────────────────┘
```

## Data Flow: Handling a Course Creation Error

```
1. Client sends:
   POST /courses
   {"title": "Python 101", "level": "invalid"}

2. FastAPI Route Handler (courses.py):
   create_course() called
   ├─ Pydantic validates input
   └─ Level regex fails → raise ValidationError

3. Global Exception Handler (main.py):
   @app.exception_handler(LMSException)
   ├─ error_code = "VALIDATION_ERROR"
   ├─ http_status = 422
   └─ severity = "WARNING"

4. Error Tracker (error_tracking.py):
   log_error() called
   ├─ Increment error_count to 1
   ├─ Write to /data/error_log.jsonl:
   │  {
   │    "timestamp": "2025-01-01T12:00:00",
   │    "error_count": 1,
   │    "error_type": "ValidationError",
   │    "message": "...",
   │    "error_code": "VALIDATION_ERROR",
   │    "severity": "WARNING"
   │  }
   └─ Return error_record

5. Notification Service (notifications.py):
   notify_error() called
   ├─ Severity = "WARNING"
   │  └─ Don't send email (only CRITICAL sends)
   ├─ Write alert? No (only CRITICAL gets alerts)
   └─ Return {"file": "skipped", "email": "skipped"}

6. Return to Client:
   HTTP 422
   {
     "message": "...",
     "error_code": "VALIDATION_ERROR",
     "details": {...}
   }
```

## Data Flow: Handling a Data Persistence Error

```
1. Client sends:
   POST /courses
   {"title": "Python 101", ...}

2. FastAPI Route Handler calls Service → Repository

3. Repository._write_data() called:
   try:
     FileLock with 5-second timeout
   except Timeout:
     raise FileLockError()

4. Global Exception Handler catches FileLockError:
   ├─ error_code = "FILE_LOCK_ERROR"
   ├─ http_status = 503
   └─ severity = "CRITICAL"

5. Error Tracker:
   log_error() called
   ├─ error_count++
   ├─ Write to /data/error_log.jsonl
   └─ is_critical_failure() = true if error_count > 5

6. Notification Service:
   notify_error() called with severity="CRITICAL"
   ├─ Write alert file:
   │  /data/alerts/alert_FILE_LOCK_ERROR_20250101120000.json
   ├─ Trigger email (if ALERT_EMAIL configured)
   └─ Log "EMAIL ALERT" to console

7. Return to Client:
   HTTP 503
   {
     "message": "Failed to acquire file lock",
     "error_code": "FILE_LOCK_ERROR",
     "details": {"file_path": "/data/lms_data.json"}
   }

8. Monitoring:
   - curl /health → "status": "degraded" (if >5 errors)
   - curl /errors → shows recent alert
   - Docker health check → may trigger restart
```

## File Organization

```
./Guided_Copilot/
├── src/
│   └── app/
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py          ← Environment config
│       │   ├── exceptions.py       ← Custom exceptions [NEW]
│       │   ├── error_tracking.py   ← Error logging [NEW]
│       │   └── notifications.py    ← Alert system [NEW]
│       ├── persistence/
│       │   └── json_repo.py        ← ✓ Enhanced with error handling
│       ├── routes/
│       │   └── courses.py          ← ✓ Enhanced with logging
│       ├── application/
│       │   └── services.py
│       ├── main.py                 ← ✓ Exception handlers, endpoints
│       ├── schemas.py
│       └── tasks.py                ← ✓ Enhanced error handling
├── tests/
│   ├── conftest.py
│   ├── test_courses_api.py
│   ├── test_repos.py
│   └── test_error_handling.py      ← Comprehensive error tests [NEW]
├── data/                           ← Mounted volume
│   ├── lms_data.json               ← Application data
│   ├── error_log.jsonl             ← Error log [NEW]
│   ├── alerts/                     ← Alert files [NEW]
│   └── bulk_enroll_report_*.json
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── docker-compose.yml              ← ✓ Health check & restart
├── Dockerfile
├── requirements.txt                ← ✓ New dependencies
├── README.md
├── .github/
│   └── copilot-instructions.md     ← ✓ Comprehensive guide
├── ERROR_HANDLING_IMPLEMENTATION.md [NEW]
└── ERROR_TESTING_GUIDE.md          [NEW]
```

## Monitoring Dashboard Integration (Conceptual)

```
┌─────────────────────────────────────────┐
│      Monitoring Dashboard               │
├─────────────────────────────────────────┤
│                                         │
│  Health Status: ▢ Healthy ▢ Degraded  │
│  Error Count: 3 / 6 threshold          │
│  Last Error: 2025-01-01 12:00:00       │
│                                         │
│  Recent Alerts:                         │
│  ├─ [CRITICAL] FILE_LOCK_ERROR         │
│  │  File lock timeout @ 12:00:05       │
│  ├─ [WARNING] VALIDATION_ERROR         │
│  │  Invalid input @ 12:00:10           │
│  └─ [CRITICAL] DATA_PERSISTENCE_ERROR  │
│     Write failed @ 12:00:15             │
│                                         │
│  Container Status:                      │
│  └─ lms-backend: Running (Healthy)     │
│     Restarts: 0                         │
│                                         │
│  Quick Links:                           │
│  [View Full Error Log] [Export Stats]  │
│                                         │
└─────────────────────────────────────────┘
         ↑ Powered by:
         ├─ GET /health
         ├─ GET /errors
         ├─ Docker stats API
         └─ error_log.jsonl tail
```
