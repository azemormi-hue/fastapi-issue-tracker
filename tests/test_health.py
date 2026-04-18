"""Tests for the health-check endpoint and app-level middleware."""


def test_health_check_returns_ok(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_timing_middleware_adds_process_time_header(client):
    """Every response should carry the X-Process-Time header."""
    response = client.get("/api/v1/health")
    assert "x-process-time" in {k.lower() for k in response.headers.keys()}
    value = response.headers["x-process-time"]
    assert value.endswith("s")
    # The numeric portion should parse as a float >= 0.
    assert float(value.rstrip("s")) >= 0.0


def test_cors_headers_present_on_preflight(client):
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # CORSMiddleware is configured with allow_origins=["*"] and
    # allow_credentials=True, which causes Starlette to echo the request
    # Origin back in the Access-Control-Allow-Origin header.
    assert response.status_code in (200, 204)
    assert response.headers.get("access-control-allow-origin") == (
        "https://example.com"
    )
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_unknown_route_returns_404(client):
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
