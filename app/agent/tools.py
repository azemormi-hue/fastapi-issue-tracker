"""
Tool functions exposed to the OpenAI function-calling agent.

Each function maps directly to an existing issues CRUD operation and
returns plain Python objects that are JSON-serialisable.
"""

import uuid
from app.storage import load_data, save_data


# ---------------------------------------------------------------------------
# Tool definitions (passed to OpenAI as `tools`)
# ---------------------------------------------------------------------------

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "list_issues",
            "description": "Return all issues currently in the tracker.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_issue",
            "description": "Return a single issue by its UUID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue to retrieve.",
                    }
                },
                "required": ["issue_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_issue",
            "description": "Create a new issue and persist it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Short title (3-100 characters).",
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description (5-2000 characters).",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Issue priority. Defaults to 'medium'.",
                    },
                },
                "required": ["title", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_issue",
            "description": "Update one or more fields of an existing issue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue to update.",
                    },
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                    },
                    "status": {
                        "type": "string",
                        "enum": ["open", "in_progress", "closed"],
                    },
                },
                "required": ["issue_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_issue",
            "description": "Delete an issue by its UUID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "UUID of the issue to delete.",
                    }
                },
                "required": ["issue_id"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Implementations
# ---------------------------------------------------------------------------


def list_issues() -> list[dict]:
    return load_data()


def get_issue(issue_id: str) -> dict:
    issues = load_data()
    for issue in issues:
        if issue["id"] == issue_id:
            return issue
    return {"error": f"Issue '{issue_id}' not found."}


def create_issue(title: str, description: str, priority: str = "medium") -> dict:
    issues = load_data()
    issue = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "priority": priority,
        "status": "open",
    }
    issues.append(issue)
    save_data(issues)
    return issue


def update_issue(
    issue_id: str,
    title: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    status: str | None = None,
) -> dict:
    issues = load_data()
    for issue in issues:
        if issue["id"] == issue_id:
            if title is not None:
                issue["title"] = title
            if description is not None:
                issue["description"] = description
            if priority is not None:
                issue["priority"] = priority
            if status is not None:
                issue["status"] = status
            save_data(issues)
            return issue
    return {"error": f"Issue '{issue_id}' not found."}


def delete_issue(issue_id: str) -> dict:
    issues = load_data()
    for i, issue in enumerate(issues):
        if issue["id"] == issue_id:
            issues.pop(i)
            save_data(issues)
            return {"deleted": issue_id}
    return {"error": f"Issue '{issue_id}' not found."}


# ---------------------------------------------------------------------------
# Dispatch helper
# ---------------------------------------------------------------------------

TOOL_HANDLERS = {
    "list_issues": list_issues,
    "get_issue": get_issue,
    "create_issue": create_issue,
    "update_issue": update_issue,
    "delete_issue": delete_issue,
}


def call_tool(name: str, arguments: dict) -> dict:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return {"error": f"Unknown tool '{name}'."}
    return handler(**arguments)
