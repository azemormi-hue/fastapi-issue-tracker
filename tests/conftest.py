"""Shared pytest fixtures.

The app persists data to a JSON file on disk (``data/issues.json``). To keep
tests isolated, fast and safe, we redirect the storage module's ``DATA_DIR``
and ``DATA_FILE`` to a per-test temporary directory.
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import storage
from main import app


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    """Redirect storage to a temporary directory for every test.

    This prevents tests from reading/writing the real ``data/issues.json``
    file and ensures each test starts with an empty data store.
    """
    data_dir = tmp_path / "data"
    data_file = data_dir / "issues.json"
    monkeypatch.setattr(storage, "DATA_DIR", data_dir)
    monkeypatch.setattr(storage, "DATA_FILE", data_file)
    yield data_file


@pytest.fixture
def client():
    """Return a FastAPI TestClient for the app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_payload():
    return {
        "title": "Sample bug",
        "description": "Something is broken in the app.",
        "priority": "high",
    }


@pytest.fixture
def created_issue(client, sample_payload):
    """Create an issue and return its response JSON."""
    response = client.post("/api/v1/issues", json=sample_payload)
    assert response.status_code == 201
    return response.json()
