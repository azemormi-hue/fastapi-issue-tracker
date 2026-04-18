"""Tests for the issues CRUD endpoints."""
import uuid

import pytest


class TestListIssues:
    def test_list_is_empty_by_default(self, client):
        response = client.get("/api/v1/issues")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_created_issues(self, client, sample_payload):
        client.post("/api/v1/issues", json=sample_payload)
        client.post(
            "/api/v1/issues",
            json={**sample_payload, "title": "Second issue"},
        )
        response = client.get("/api/v1/issues")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        titles = {issue["title"] for issue in body}
        assert titles == {"Sample bug", "Second issue"}


class TestCreateIssue:
    def test_create_returns_201_and_expected_shape(self, client, sample_payload):
        response = client.post("/api/v1/issues", json=sample_payload)
        assert response.status_code == 201
        body = response.json()
        assert set(body.keys()) == {
            "id", "title", "description", "priority", "status"
        }
        assert body["title"] == sample_payload["title"]
        assert body["description"] == sample_payload["description"]
        assert body["priority"] == "high"
        # New issues always start in the "open" state.
        assert body["status"] == "open"
        # ID must be a valid UUID4 string.
        parsed = uuid.UUID(body["id"])
        assert parsed.version == 4

    def test_create_defaults_priority_to_medium(self, client):
        response = client.post(
            "/api/v1/issues",
            json={"title": "No priority", "description": "missing priority field"},
        )
        assert response.status_code == 201
        assert response.json()["priority"] == "medium"

    def test_create_persists_across_requests(self, client, sample_payload):
        created = client.post("/api/v1/issues", json=sample_payload).json()
        listed = client.get("/api/v1/issues").json()
        assert listed == [created]

    def test_create_assigns_unique_ids(self, client, sample_payload):
        first = client.post("/api/v1/issues", json=sample_payload).json()
        second = client.post("/api/v1/issues", json=sample_payload).json()
        assert first["id"] != second["id"]

    @pytest.mark.parametrize(
        "payload",
        [
            # Missing title
            {"description": "a valid description"},
            # Missing description
            {"title": "Valid title"},
            # Title too short (min_length=3)
            {"title": "ab", "description": "a valid description"},
            # Title too long (max_length=100)
            {"title": "x" * 101, "description": "a valid description"},
            # Description too short (min_length=5)
            {"title": "Valid title", "description": "abcd"},
            # Description too long (max_length=2000)
            {"title": "Valid title", "description": "y" * 2001},
            # Invalid priority enum value
            {
                "title": "Valid title",
                "description": "a valid description",
                "priority": "urgent",
            },
        ],
    )
    def test_create_rejects_invalid_payloads(self, client, payload):
        response = client.post("/api/v1/issues", json=payload)
        assert response.status_code == 422

    def test_create_rejects_empty_body(self, client):
        response = client.post("/api/v1/issues", json={})
        assert response.status_code == 422

    def test_create_rejects_non_json(self, client):
        response = client.post("/api/v1/issues", content=b"not json")
        assert response.status_code == 422


class TestGetIssue:
    def test_get_existing_issue(self, client, created_issue):
        response = client.get(f"/api/v1/issues/{created_issue['id']}")
        assert response.status_code == 200
        assert response.json() == created_issue

    def test_get_missing_issue_returns_404(self, client):
        response = client.get(f"/api/v1/issues/{uuid.uuid4()}")
        assert response.status_code == 404
        assert response.json() == {"detail": "Issue not found"}

    def test_get_does_not_match_partial_id(self, client, created_issue):
        prefix = created_issue["id"][:8]
        response = client.get(f"/api/v1/issues/{prefix}")
        assert response.status_code == 404


class TestUpdateIssue:
    def test_update_all_fields(self, client, created_issue):
        response = client.put(
            f"/api/v1/issues/{created_issue['id']}",
            json={
                "title": "Updated title",
                "description": "An updated description.",
                "priority": "low",
                "status": "closed",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == created_issue["id"]
        assert body["title"] == "Updated title"
        assert body["description"] == "An updated description."
        assert body["priority"] == "low"
        assert body["status"] == "closed"

    def test_partial_update_only_changes_provided_fields(self, client, created_issue):
        response = client.put(
            f"/api/v1/issues/{created_issue['id']}",
            json={"status": "in_progress"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "in_progress"
        # Other fields are unchanged.
        assert body["title"] == created_issue["title"]
        assert body["description"] == created_issue["description"]
        assert body["priority"] == created_issue["priority"]

    def test_empty_update_is_noop(self, client, created_issue):
        response = client.put(
            f"/api/v1/issues/{created_issue['id']}", json={}
        )
        assert response.status_code == 200
        assert response.json() == created_issue

    def test_update_persists(self, client, created_issue):
        client.put(
            f"/api/v1/issues/{created_issue['id']}",
            json={"title": "Persisted title"},
        )
        reloaded = client.get(f"/api/v1/issues/{created_issue['id']}").json()
        assert reloaded["title"] == "Persisted title"

    def test_update_missing_issue_returns_404(self, client):
        response = client.put(
            f"/api/v1/issues/{uuid.uuid4()}", json={"title": "nope"}
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "Issue not found"}

    @pytest.mark.parametrize(
        "payload",
        [
            {"description": "abcd"},          # too short
            {"description": "z" * 2001},      # too long
            {"priority": "urgent"},           # bad enum
            {"status": "resolved"},           # bad enum
        ],
    )
    def test_update_rejects_invalid_payloads(self, client, created_issue, payload):
        response = client.put(
            f"/api/v1/issues/{created_issue['id']}", json=payload
        )
        assert response.status_code == 422


class TestDeleteIssue:
    def test_delete_existing_issue_returns_204(self, client, created_issue):
        response = client.delete(f"/api/v1/issues/{created_issue['id']}")
        assert response.status_code == 204
        # No content body.
        assert response.content == b""

    def test_delete_removes_from_storage(self, client, created_issue):
        client.delete(f"/api/v1/issues/{created_issue['id']}")
        follow_up = client.get(f"/api/v1/issues/{created_issue['id']}")
        assert follow_up.status_code == 404
        listed = client.get("/api/v1/issues").json()
        assert listed == []

    def test_delete_only_removes_target_issue(self, client, sample_payload):
        a = client.post("/api/v1/issues", json=sample_payload).json()
        b = client.post(
            "/api/v1/issues",
            json={**sample_payload, "title": "Keep me"},
        ).json()
        response = client.delete(f"/api/v1/issues/{a['id']}")
        assert response.status_code == 204
        remaining = client.get("/api/v1/issues").json()
        assert remaining == [b]

    def test_delete_missing_issue_returns_404(self, client):
        response = client.delete(f"/api/v1/issues/{uuid.uuid4()}")
        assert response.status_code == 404
        assert response.json() == {"detail": "Issue not found"}
