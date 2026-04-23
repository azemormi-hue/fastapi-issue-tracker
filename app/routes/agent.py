import json
import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status
from openai import OpenAI

from app.agent.schemas import ChatRequest, ChatResponse
from app.agent.tools import TOOLS, call_tool

load_dotenv()

router = APIRouter(prefix="/api/v1/agent", tags=["Agent"])

SYSTEM_PROMPT = (
    "You are a helpful issue-tracker assistant. "
    "You can list, retrieve, create, update, and delete issues on behalf of the user. "
    "Use the provided tools whenever an action is requested. "
    "Be concise and friendly in your responses."
)


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY is not configured on this server.",
        )
    return OpenAI(api_key=api_key)


@router.post("/chat", response_model=ChatResponse)
def agent_chat(payload: ChatRequest):
    """
    Send a message to the AI agent.

    The agent can call issue CRUD tools automatically based on the request.
    Pass previous turns in `history` to maintain conversation context.
    """
    client = _get_client()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in payload.history:
        messages.append({"role": turn.role, "content": turn.content})
    messages.append({"role": "user", "content": payload.message})

    actions: list[str] = []

    # Agentic loop: keep running until the model stops requesting tool calls
    while True:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        choice = response.choices[0]
        messages.append(choice.message.model_dump(exclude_unset=True))

        if choice.finish_reason == "tool_calls":
            for tc in choice.message.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)
                result = call_tool(fn_name, fn_args)
                actions.append(f"{fn_name}({json.dumps(fn_args)})")
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    }
                )
        else:
            # "stop" or any other finish reason — model has produced its final reply
            break

    reply = choice.message.content or ""
    return ChatResponse(reply=reply, actions=actions)
