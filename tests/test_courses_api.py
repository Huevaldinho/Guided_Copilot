def test_create_course(client):
    payload = {
        "title": "Intro to Python",
        "description": "Learn Python",
        "professor_id": "00000000-0000-0000-0000-000000000000",
        "duration_hours": 12,
        "level": "beginner"
    }
    resp = client.post("/courses/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["title"] == payload["title"]

def test_list_courses(client):
    payload = {
        "title": "Data Structures",
        "description": "DS course",
        "professor_id": "00000000-0000-0000-0000-000000000000",
        "duration_hours": 8,
        "level": "intermediate"
    }
    client.post("/courses/", json=payload)
    resp = client.get("/courses/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(c["title"] == "Data Structures" for c in data)

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

def test_create_course_missing_required_field(client):
    payload = {
        "description": "Missing title"
    }
    resp = client.post("/courses/", json=payload)
    assert resp.status_code == 422

def test_get_nonexistent_course(client):
    resp = client.post("/courses/00000000-0000-0000-0000-000000000001/enrollments/bulk")
    assert resp.status_code == 422

def test_invalid_course_level(client):
    payload = {
        "title": "Test",
        "description": "Test",
        "professor_id": "00000000-0000-0000-0000-000000000000",
        "level": "invalid_level"
    }
    resp = client.post("/courses/", json=payload)
    assert resp.status_code == 422
