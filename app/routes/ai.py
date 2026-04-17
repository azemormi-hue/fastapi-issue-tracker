import os
from collections import Counter

import anthropic
from fastapi import APIRouter, HTTPException, status

from app.schemas import (
    AIClassifyResponse,
    AISuggestResponse,
    AISummarizeResponse,
    IssuePriority,
)
from app.storage import load_data

router = APIRouter(prefix="/api/v1/ai", tags=["AI Agent"])

MODEL = "claude-opus-4-6"


def _get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ANTHROPIC_API_KEY environment variable is not set",
        )
    return anthropic.Anthropic(api_key=api_key)


def _find_issue(issue_id: str) -> dict:
    issues = load_data()
    for issue in issues:
        if issue["id"] == issue_id:
            return issue
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Issue not found",
    )


@router.post("/classify/{issue_id}", response_model=AIClassifyResponse)
def classify_issue(issue_id: str):
    """Use AI to suggest the priority level for an issue based on its content."""
    issue = _find_issue(issue_id)
    client = _get_client()

    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        thinking={"type": "adaptive"},
        messages=[
            {
                "role": "user",
                "content": (
                    "You are an issue triage assistant. Classify the priority of "
                    "this issue as exactly one of: low, medium, high.\n\n"
                    f"Title: {issue['title']}\n"
                    f"Description: {issue['description']}\n\n"
                    "Respond with ONLY a JSON object (no markdown fences) with two keys:\n"
                    '  "priority": "low" | "medium" | "high"\n'
                    '  "reasoning": a one-sentence explanation'
                ),
            }
        ],
    )

    import json

    text = next(
        (b.text for b in response.content if b.type == "text"), "{}"
    )
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        result = {"priority": "medium", "reasoning": text}

    return AIClassifyResponse(
        issue_id=issue_id,
        suggested_priority=IssuePriority(result.get("priority", "medium")),
        reasoning=result.get("reasoning", "Could not determine reasoning."),
    )


@router.post("/suggest/{issue_id}", response_model=AISuggestResponse)
def suggest_solution(issue_id: str):
    """Use AI to suggest a solution or next steps for an issue."""
    issue = _find_issue(issue_id)
    client = _get_client()

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        thinking={"type": "adaptive"},
        messages=[
            {
                "role": "user",
                "content": (
                    "You are a helpful software engineering assistant. "
                    "Suggest a concise, actionable solution for this issue.\n\n"
                    f"Title: {issue['title']}\n"
                    f"Description: {issue['description']}\n"
                    f"Priority: {issue['priority']}\n"
                    f"Status: {issue['status']}\n\n"
                    "Provide a clear, step-by-step suggestion in plain text."
                ),
            }
        ],
    )

    text = next(
        (b.text for b in response.content if b.type == "text"), ""
    )
    return AISuggestResponse(issue_id=issue_id, suggestion=text)


@router.post("/summarize", response_model=AISummarizeResponse)
def summarize_issues():
    """Use AI to generate a summary and analysis of all current issues."""
    issues = load_data()

    if not issues:
        return AISummarizeResponse(
            summary="No issues found in the tracker.",
            total_issues=0,
            by_status={},
            by_priority={},
        )

    by_status = dict(Counter(i["status"] for i in issues))
    by_priority = dict(Counter(i["priority"] for i in issues))

    issues_text = "\n".join(
        f"- [{i['priority'].upper()}] [{i['status']}] {i['title']}: {i['description'][:120]}"
        for i in issues
    )

    client = _get_client()

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        thinking={"type": "adaptive"},
        messages=[
            {
                "role": "user",
                "content": (
                    "You are a project manager assistant. Summarize the state of "
                    "this issue tracker in 2-4 sentences. Highlight any urgent items "
                    "and overall project health.\n\n"
                    f"Issues ({len(issues)} total):\n{issues_text}"
                ),
            }
        ],
    )

    text = next(
        (b.text for b in response.content if b.type == "text"), ""
    )

    return AISummarizeResponse(
        summary=text,
        total_issues=len(issues),
        by_status=by_status,
        by_priority=by_priority,
    )
