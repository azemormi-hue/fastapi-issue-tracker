"""Tests for main.py — app wiring, health check, middleware, CORS."""
import re


def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_timing_middleware_adds_process_time_header(client):
    response = client.get("/api/v1/health")
    assert "x-process-time" in response.headers
    value = response.headers["x-process-time"]
    # Format is e.g. "0.0012s" — 4 decimal places followed by 's'.
    assert re.fullmatch(r"\d+\.\d{4}s", value), value


def test_timing_middleware_present_on_error_responses(client):
    response = client.get("/api/v1/issues/does-not-exist")
    assert response.status_code == 404
    assert "x-process-time" in response.headers


def test_cors_headers_present_on_preflight(client):
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://example.com"


def test_openapi_metadata(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "Issue Tracker API"
    assert data["info"]["version"] == "0.1.0"
