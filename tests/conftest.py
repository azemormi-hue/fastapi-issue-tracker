"""Shared pytest fixtures.

The storage layer persists to ``data/issues.json`` via module-level ``Path``
constants in :mod:`app.storage`. To keep tests isolated and avoid clobbering
any real data, we redirect those paths to a temporary directory for every
test via an autouse fixture.
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import storage
import main


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    """Redirect storage to a per-test temporary directory."""
    data_dir = tmp_path / "data"
    data_file = data_dir / "issues.json"
    monkeypatch.setattr(storage, "DATA_DIR", data_dir)
    monkeypatch.setattr(storage, "DATA_FILE", data_file)
    yield data_file


@pytest.fixture
def client():
    """A TestClient bound to the FastAPI app."""
    with TestClient(main.app) as c:
        yield c


@pytest.fixture
def created_issue(client):
    """Create a single issue through the API and return its JSON body."""
    response = client.post(
        "/api/v1/issues",
        json={
            "title": "Sample issue",
            "description": "A reasonably long description.",
            "priority": "high",
        },
    )
    assert response.status_code == 201
    return response.json()
