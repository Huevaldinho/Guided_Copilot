"""
Pytest configuration and fixtures with complete type hints and Allure reporting setup.
"""

import os
import pytest
import allure
from typing import Generator, Any
from pathlib import Path
from fastapi.testclient import TestClient
from fastapi import FastAPI


@pytest.fixture(scope="session", autouse=True)
def setup_allure_environment():
    """Configure Allure environment and execution details."""
    allure_results_dir = Path("allure-results")
    if allure_results_dir.exists():
        env_file = allure_results_dir / "environment.properties"
        with open(env_file, "w") as f:
            f.write(f"os.name={os.name}\n")
            f.write(f"python.version={__import__('sys').version.split()[0]}\n")
            f.write(f"framework=FastAPI\n")
            f.write(f"test_framework=pytest\n")
            f.write(f"reporting=allure\n")
            f.write(f"coverage_threshold=85%\n")


@pytest.fixture(scope="function", autouse=True)
def allure_test_context(request):
    """Add test context information to Allure report."""
    if hasattr(request, "node"):
        # Add test file name
        allure.dynamic.story(f"From: {request.node.fspath.basename}")


@pytest.fixture(scope="function")
def data_file(tmp_path: Path, monkeypatch: Any) -> str:
    """Provide isolated temporary data file for each test.
    
    Args:
        tmp_path: pytest tmp_path fixture
        monkeypatch: pytest monkeypatch fixture
        
    Returns:
        str: Path to temporary data file
    """
    path: Path = tmp_path / "lms_data.json"
    monkeypatch.setenv("DATA_FILE_PATH", str(path))
    return str(path)


@pytest.fixture(scope="function")
def client(data_file: str) -> Generator[TestClient, None, None]:
    """Provide FastAPI test client with isolated data.
    
    Args:
        data_file: Fixture providing temporary data file
        
    Yields:
        TestClient: FastAPI test client instance
    """
    from src.app.main import create_app
    
    app: FastAPI = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Set anyio backend for async tests.
    
    Returns:
        str: Backend name for asyncio
    """
    return "asyncio"


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to add test outcome information to Allure report."""
    outcome = yield
    rep = outcome.get_result()
    
    if rep.when == "call":
        if rep.failed:
            allure.dynamic.tag("failed")
        elif rep.passed:
            allure.dynamic.tag("passed")
        elif rep.skipped:
            allure.dynamic.tag("skipped")

