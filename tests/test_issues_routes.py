"""Tests for the /api/v1/issues CRUD endpoints."""
import uuid


VALID_PAYLOAD = {
    "title": "Bug in login",
    "description": "Users cannot log in when the session cookie is missing.",
    "priority": "high",
}


# ---- GET /api/v1/issues ----------------------------------------------------

class TestListIssues:
    def test_empty_initially(self, client):
        response = client.get("/api/v1/issues")
        assert response.status_code == 200
        assert response.json() == []

    def test_lists_created_issues(self, client):
        client.post("/api/v1/issues", json=VALID_PAYLOAD)
        client.post(
            "/api/v1/issues",
            json={**VALID_PAYLOAD, "title": "Second", "priority": "low"},
        )
        response = client.get("/api/v1/issues")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        titles = {issue["title"] for issue in body}
        assert titles == {"Bug in login", "Second"}


# ---- POST /api/v1/issues ---------------------------------------------------

class TestCreateIssue:
    def test_create_returns_201_and_full_issue(self, client):
        response = client.post("/api/v1/issues", json=VALID_PAYLOAD)
        assert response.status_code == 201
        body = response.json()
        assert body["title"] == VALID_PAYLOAD["title"]
        assert body["description"] == VALID_PAYLOAD["description"]
        assert body["priority"] == "high"
        assert body["status"] == "open"
        # id is a valid UUID4
        parsed = uuid.UUID(body["id"])
        assert parsed.version == 4

    def test_create_defaults_priority_to_medium(self, client):
        payload = {"title": "No priority", "description": "Still works fine."}
        response = client.post("/api/v1/issues", json=payload)
        assert response.status_code == 201
        assert response.json()["priority"] == "medium"

    def test_create_persists_issue(self, client):
        created = client.post("/api/v1/issues", json=VALID_PAYLOAD).json()
        listed = client.get("/api/v1/issues").json()
        assert any(item["id"] == created["id"] for item in listed)

    def test_each_issue_gets_unique_id(self, client):
        a = client.post("/api/v1/issues", json=VALID_PAYLOAD).json()
        b = client.post("/api/v1/issues", json=VALID_PAYLOAD).json()
        assert a["id"] != b["id"]

    def test_create_missing_title(self, client):
        response = client.post(
            "/api/v1/issues",
            json={"description": "A valid description here."},
        )
        assert response.status_code == 422

    def test_create_title_too_short(self, client):
        response = client.post(
            "/api/v1/issues",
            json={"title": "ab", "description": "A valid description here."},
        )
        assert response.status_code == 422

    def test_create_description_too_short(self, client):
        response = client.post(
            "/api/v1/issues",
            json={"title": "Valid title", "description": "hi"},
        )
        assert response.status_code == 422

    def test_create_invalid_priority(self, client):
        response = client.post(
            "/api/v1/issues",
            json={**VALID_PAYLOAD, "priority": "urgent"},
        )
        assert response.status_code == 422


# ---- GET /api/v1/issues/{id} -----------------------------------------------

class TestGetIssue:
    def test_get_existing_issue(self, client, created_issue):
        response = client.get(f"/api/v1/issues/{created_issue['id']}")
        assert response.status_code == 200
        assert response.json() == created_issue

    def test_get_missing_issue_returns_404(self, client):
        response = client.get("/api/v1/issues/nonexistent")
        assert response.status_code == 404
        assert response.json() == {"detail": "Issue not found"}


# ---- PUT /api/v1/issues/{id} -----------------------------------------------

class TestUpdateIssue:
    def test_full_update(self, client, created_issue):
        response = client.put(
            f"/api/v1/issues/{created_issue['id']}",
            json={
                "title": "New title",
                "description": "A brand new description.",
                "priority": "low",
                "status": "closed",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == created_issue["id"]
        assert body["title"] == "New title"
        assert body["description"] == "A brand new description."
        assert body["priority"] == "low"
        assert body["status"] == "closed"

    def test_partial_update_only_status(self, client, created_issue):
        response = client.put(
            f"/api/v1/issues/{created_issue['id']}",
            json={"status": "in_progress"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "in_progress"
        # Other fields preserved
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
            json={"title": "Persisted"},
        )
        fetched = client.get(f"/api/v1/issues/{created_issue['id']}").json()
        assert fetched["title"] == "Persisted"

    def test_update_missing_issue_returns_404(self, client):
        response = client.put(
            "/api/v1/issues/does-not-exist", json={"title": "x"}
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "Issue not found"}

    def test_update_invalid_priority(self, client, created_issue):
        response = client.put(
            f"/api/v1/issues/{created_issue['id']}",
            json={"priority": "urgent"},
        )
        assert response.status_code == 422

    def test_update_invalid_status(self, client, created_issue):
        response = client.put(
            f"/api/v1/issues/{created_issue['id']}",
            json={"status": "done"},
        )
        assert response.status_code == 422

    def test_update_description_too_short(self, client, created_issue):
        response = client.put(
            f"/api/v1/issues/{created_issue['id']}",
            json={"description": "hi"},
        )
        assert response.status_code == 422


# ---- DELETE /api/v1/issues/{id} --------------------------------------------

class TestDeleteIssue:
    def test_delete_existing_issue(self, client, created_issue):
        response = client.delete(f"/api/v1/issues/{created_issue['id']}")
        assert response.status_code == 204
        assert response.content == b""
        # It should no longer be retrievable
        followup = client.get(f"/api/v1/issues/{created_issue['id']}")
        assert followup.status_code == 404

    def test_delete_only_removes_target_issue(self, client):
        keep = client.post("/api/v1/issues", json=VALID_PAYLOAD).json()
        remove = client.post("/api/v1/issues", json=VALID_PAYLOAD).json()
        client.delete(f"/api/v1/issues/{remove['id']}")
        listed = client.get("/api/v1/issues").json()
        ids = [issue["id"] for issue in listed]
        assert keep["id"] in ids
        assert remove["id"] not in ids

    def test_delete_missing_issue_returns_404(self, client):
        response = client.delete("/api/v1/issues/does-not-exist")
        assert response.status_code == 404
        assert response.json() == {"detail": "Issue not found"}
