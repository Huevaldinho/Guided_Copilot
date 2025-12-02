# BDD Testing with Allure

## Overview

This project uses Allure for comprehensive testing with BDD (Behavior-Driven Development) scenarios. All tests are written using pytest-bdd with detailed Allure decorators for professional reporting.

## Running Tests

### Basic Test Run
```powershell
pytest tests/test_bdd_comprehensive.py -v
```

### Generate Allure Report
```powershell
pytest tests/test_bdd_comprehensive.py --alluredir=allure-results
allure serve allure-results
```

### With Coverage
```powershell
pytest --cov=src --cov-report=html --cov-fail-under=85
```

### Run Specific Test Class
```powershell
pytest tests/test_bdd_comprehensive.py::TestCreateCourse -v
```

### Run with Specific Markers
```powershell
pytest -m "bdd" -v
```

## Test Structure

### Features & Stories
- **Feature**: High-level business capability
- **Story**: User-centric requirement within a feature
- **Scenario**: BDD test case with Given-When-Then steps

### Test Classes

#### 1. TestCreateCourse
**Feature**: Courses Management  
**Story**: Create Course
- ✓ Successfully create course
- ✓ Reject missing title
- ✓ Reject invalid level

#### 2. TestListCourses
**Feature**: Courses Management  
**Story**: List Courses
- ✓ List empty courses
- ✓ List courses with data
- ✓ Alternative /listcourses endpoint

#### 3. TestHealthCheck
**Feature**: Health & Monitoring  
**Story**: Health Check
- ✓ Health check returns status
- ✓ Errors endpoint returns stats

#### 4. TestBulkEnrollment
**Feature**: Bulk Enrollment  
**Story**: Enrollment Management
- ✓ Bulk enroll from CSV
- ✓ Handle non-existent course

#### 5. TestErrorHandling
**Feature**: Error Handling  
**Story**: Error Tracking
- ✓ Error tracker logs exceptions
- ✓ Critical failure detection

#### 6. TestDataPersistence
**Feature**: Data Persistence  
**Story**: Repository Operations
- ✓ Atomic write persistence

#### 7. TestInputValidation
**Feature**: Validation  
**Story**: Input Validation
- ✓ Invalid levels rejected (parametrized)
- ✓ Valid levels accepted (parametrized)

#### 8. TestIntegrationScenarios
**Feature**: Integration  
**Story**: Complete Workflows
- ✓ End-to-end course creation and enrollment

## Allure Decorators

### @allure.feature
Groups tests by high-level business capability:
```python
@allure.feature("Courses Management")
```

### @allure.story
Groups tests within a feature:
```python
@allure.story("Create Course")
```

### @allure.title
Test display title in report:
```python
@allure.title("Successfully create a new course")
```

### @allure.description
Detailed test description:
```python
@allure.description("Verify that a course can be created with valid data")
```

### @allure.step
Break down test into steps:
```python
with allure.step("Given valid course data"):
    payload = sample_course_payload
```

## Allure Report Structure

```
allure-results/
├── 50019dd2-2e2f-4c40-9373-2e7df8b6fa19-container.json
├── 50019dd2-2e2f-4c40-9373-2e7df8b6fa19-result.json
├── ...
└── executor.json
```

### View Report
```powershell
allure serve allure-results
```

Opens interactive HTML report showing:
- Test execution timeline
- Features and stories hierarchy
- Step-by-step execution details
- Error screenshots and logs
- Test history and trends
- Test coverage statistics

## Test Fixtures

### data_file
Provides isolated temporary data file per test.

### client
Provides FastAPI TestClient with isolated data.

### sample_course_payload
Sample course creation data:
```json
{
  "title": "Python Fundamentals",
  "description": "Learn Python basics",
  "professor_id": "uuid",
  "duration_hours": 40,
  "level": "beginner"
}
```

### sample_csv_data
Sample CSV enrollment data.

## BDD Scenarios

All tests follow BDD pattern:

```python
with allure.step("Given ..."):
    # Setup

with allure.step("When ..."):
    # Action

with allure.step("Then ..."):
    # Assertion
```

## Parametrized Tests

Tests with multiple inputs:

```python
@pytest.mark.parametrize("invalid_level", ["expert", "BEGINNER", "novice"])
def test_invalid_levels(client, sample_course_payload, invalid_level):
    ...
```

## Coverage Requirements

- Minimum: 85%
- HTML Report: `htmlcov/index.html`
- Terminal: Coverage percentage per file

## Key Test Scenarios

### Create Course
```
✓ Valid course creation returns 201
✓ Missing title returns 422
✓ Invalid level returns 422
```

### List Courses
```
✓ Empty list returns []
✓ Listed courses match created courses
✓ /listcourses endpoint works
```

### Bulk Enrollment
```
✓ Valid CSV processed successfully
✓ Non-existent course returns 404
```

### Health Monitoring
```
✓ /health returns current status
✓ /errors returns statistics
```

### Error Handling
```
✓ Errors logged to error_log.jsonl
✓ Critical failures detected (>5 errors)
```

## Continuous Integration

Run all tests with coverage:
```powershell
pytest --cov=src --cov-fail-under=85 --alluredir=allure-results
```

Generate report:
```powershell
allure generate allure-results -o allure-report --clean
allure open allure-report
```

## Debugging Tests

Run with verbose output:
```powershell
pytest tests/test_bdd_comprehensive.py -v -s
```

Run with pdb on failure:
```powershell
pytest tests/test_bdd_comprehensive.py --pdb
```

Show print statements:
```powershell
pytest tests/test_bdd_comprehensive.py -s
```

## Best Practices

1. **One assertion per step**: Make failures clear
2. **Descriptive step names**: Use Given-When-Then pattern
3. **Fixtures for setup**: Use parametrized fixtures
4. **Allure decorators**: Always use @allure decorators
5. **Clear test names**: Should describe what is tested
6. **Parametrize similar tests**: Use @pytest.mark.parametrize
7. **Isolate tests**: Each test uses fresh data_file fixture

## Test Execution Time

Typical test suite:
- 40+ test cases
- ~5-10 seconds total execution
- Per test: ~100-200ms
