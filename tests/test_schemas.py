"""Tests for Pydantic schemas in app/schemas.py."""
import pytest
from pydantic import ValidationError

from app.schemas import (
    IssueCreate,
    IssueOut,
    IssuePriority,
    IssueStatus,
    IssueUpdate,
)


class TestEnums:
    def test_issue_priority_values(self):
        assert IssuePriority.low.value == "low"
        assert IssuePriority.medium.value == "medium"
        assert IssuePriority.high.value == "high"

    def test_issue_status_values(self):
        assert IssueStatus.open.value == "open"
        assert IssueStatus.in_progress.value == "in_progress"
        assert IssueStatus.closed.value == "closed"


class TestIssueCreate:
    def test_defaults_priority_to_medium(self):
        issue = IssueCreate(title="abc", description="hello")
        assert issue.priority == IssuePriority.medium

    def test_accepts_valid_priority_string(self):
        issue = IssueCreate(title="abc", description="hello", priority="high")
        assert issue.priority == IssuePriority.high

    @pytest.mark.parametrize("title", ["", "ab"])
    def test_title_too_short(self, title):
        with pytest.raises(ValidationError):
            IssueCreate(title=title, description="hello")

    def test_title_too_long(self):
        with pytest.raises(ValidationError):
            IssueCreate(title="x" * 101, description="hello")

    def test_description_too_short(self):
        with pytest.raises(ValidationError):
            IssueCreate(title="abc", description="hi")

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            IssueCreate(title="abc", description="x" * 2001)

    def test_invalid_priority(self):
        with pytest.raises(ValidationError):
            IssueCreate(title="abc", description="hello", priority="urgent")


class TestIssueUpdate:
    def test_all_fields_optional(self):
        update = IssueUpdate()
        assert update.title is None
        assert update.description is None
        assert update.priority is None
        assert update.status is None

    def test_partial_update(self):
        update = IssueUpdate(status="closed")
        assert update.status == IssueStatus.closed
        assert update.title is None

    def test_description_min_length_enforced(self):
        with pytest.raises(ValidationError):
            IssueUpdate(description="hi")

    def test_description_max_length_enforced(self):
        with pytest.raises(ValidationError):
            IssueUpdate(description="x" * 2001)

    def test_title_max_length_enforced(self):
        with pytest.raises(ValidationError):
            IssueUpdate(title="x" * 101)

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            IssueUpdate(status="done")


class TestIssueOut:
    def test_round_trip(self):
        data = {
            "id": "abc-123",
            "title": "t",
            "description": "desc",
            "priority": "low",
            "status": "open",
        }
        out = IssueOut(**data)
        assert out.id == "abc-123"
        assert out.priority == IssuePriority.low
        assert out.status == IssueStatus.open

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            IssueOut(id="x", title="t", description="d", priority="low")
