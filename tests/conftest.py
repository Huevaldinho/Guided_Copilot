import os
import pytest
from fastapi.testclient import TestClient

@pytest.fixture(scope="function")
def data_file(tmp_path, monkeypatch):
    path = tmp_path / "lms_data.json"
    monkeypatch.setenv("DATA_FILE_PATH", str(path))
    return str(path)

@pytest.fixture(scope="function")
def client(data_file):
    from src.app.main import create_app
    app = create_app()
    with TestClient(app) as client:
        yield client
