Develop a scalable FastAPI microservice for an Online Learning Management System (LMS) managing Professors, Students, Courses, and Classes with enrollment, progress tracking, and role-based access. Professors create/manage courses and classes; students enroll, view progress; admins oversee all. Enforces SOLID principles, async architecture, 95% test coverage, Docker deployment, and GitHub Actions CI/CD.​​

Domain Models & Relationships
Core entities with Pydantic/SQLAlchemy schemas:

User (id, email, role: professor/student/admin, is_active)

Profile (user_id, first_name, last_name, bio)

Course (id, title, description, professor_id, duration_hours, level: beginner/intermediate/advanced)

Class (id, title, course_id, order_sequence, video_url, materials_url, duration_minutes)

Enrollment (id, student_id, course_id, enrolled_at, progress_percentage, completed: bool, completion_date)​
Business rules: Max 5 active enrollments/student, auto-update progress on class completion, courses expire after 1 year inactive.​

Business Logic & Services
CourseService: CRUD courses/classes (professor-only), compute enrollment stats (e.g., completion rate per course), validate professor load (<10 courses).
EnrollmentService: Student self-enroll (if seats available), track progress (progress = completed_classes/total_classes * 100), generate certificates on 100% completion via domain events.
ProfessorService: Assign TA roles, bulk-enroll students from CSV, generate class analytics (avg completion time). Domain events: ClassCompletedEvent triggers progress update + email notification.​​

API Endpoints by Role
Public/Student:

POST /auth/register/ (student self-register)

POST /auth/login/ → JWT

GET /courses/?level=intermediate&search=python (public course catalog)

POST /enrollments/ (self-enroll course_id)

GET /student/courses/ (my courses with progress)

GET /courses/{course_id}/progress​

Professor:

POST /professor/courses/ (create course)

POST /courses/{course_id}/classes/ (add class)

POST /courses/{course_id}/enrollments/bulk (add students)

GET /professor/courses/{course_id}/analytics (completion stats)​

Admin: Full CRUD + GET /admin/dashboard/ (system metrics). All secured by RBAC middleware.​

Layered Architecture & Project Structure
text
lms-app/
├── app/
│   ├── core/          # Config, security, events, dependencies
│   ├── domain/        # Entities (User, Course), value objects, domain services
│   ├── application/   # Use cases (CourseService, EnrollmentService)
│   ├── infrastructure/# AsyncSQLAlchemy repos (PostgreSQL dev/SQL Server prod), email/S3
│   ├── presentation/  # APIRouters (auth, courses, enrollments), Pydantic schemas
│   └── main.py        # Lifespan (DB pool, Redis), CORS, middleware
├── tests/             # pytest (unit: mock services; integration: TestClient + Docker Postgres)
├── docker-compose.yml # FastAPI, Postgres, Redis (progress cache), MinIO (materials)
├── Dockerfile         # Multi-stage, Gunicorn+Uvicorn (4 workers)
└── .github/workflows/ # ci.yml (lint/test/build/push), cd.yml (deploy on tag)
Repository factory per env; protocols enforce DIP. Import-linter prevents circular deps.​

Testing, Security & Deployment
Tests: 95% coverage – unit (business rules), integration (end-to-end enroll+progress), security (RBAC 403s), load (Locust: 500 concurrent enrollments).​

Security: JWT (OAuth2PasswordBearer), rate-limit enrollments, CORS (trusted domains), HTTPS enforced. Structured logging w/ correlation IDs.​

Deployment: Healthchecks (/health, /ready), connection pooling (pool_pre_ping), Redis for caching enrollments, GitHub Actions deploys to staging/prod with approvals.​