"""Tests for Pydantic schemas defined in ``app.schemas``."""
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
    def test_priority_values(self):
        assert {p.value for p in IssuePriority} == {"low", "medium", "high"}

    def test_status_values(self):
        assert {s.value for s in IssueStatus} == {
            "open", "in_progress", "closed"
        }


class TestIssueCreate:
    def test_defaults_priority_to_medium(self):
        issue = IssueCreate(title="abc", description="hello")
        assert issue.priority == IssuePriority.medium

    def test_accepts_all_priorities(self):
        for priority in IssuePriority:
            assert IssueCreate(
                title="abc", description="hello", priority=priority
            ).priority == priority

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"title": "ab", "description": "hello"},          # title < 3
            {"title": "x" * 101, "description": "hello"},     # title > 100
            {"title": "abc", "description": "hi"},            # description < 5
            {"title": "abc", "description": "y" * 2001},      # description > 2000
            {"title": "abc", "description": "hello",
             "priority": "urgent"},                           # bad enum
        ],
    )
    def test_rejects_invalid_input(self, kwargs):
        with pytest.raises(ValidationError):
            IssueCreate(**kwargs)

    def test_boundary_lengths_are_valid(self):
        IssueCreate(title="abc", description="hello")          # min boundaries
        IssueCreate(title="x" * 100, description="y" * 2000)   # max boundaries


class TestIssueUpdate:
    def test_all_fields_optional(self):
        update = IssueUpdate()
        assert update.title is None
        assert update.description is None
        assert update.priority is None
        assert update.status is None

    def test_accepts_partial_update(self):
        update = IssueUpdate(status=IssueStatus.closed)
        assert update.status == IssueStatus.closed
        assert update.title is None

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"description": "abcd"},           # description < 5
            {"description": "z" * 2001},       # description > 2000
            {"title": "x" * 101},              # title > 100
            {"priority": "urgent"},            # bad enum
            {"status": "resolved"},            # bad enum
        ],
    )
    def test_rejects_invalid_input(self, kwargs):
        with pytest.raises(ValidationError):
            IssueUpdate(**kwargs)


class TestIssueOut:
    def test_serializes_fields(self):
        issue = IssueOut(
            id="abc-123",
            title="Title",
            description="Description here",
            priority=IssuePriority.high,
            status=IssueStatus.open,
        )
        dumped = issue.model_dump()
        assert dumped == {
            "id": "abc-123",
            "title": "Title",
            "description": "Description here",
            "priority": IssuePriority.high,
            "status": IssueStatus.open,
        }
