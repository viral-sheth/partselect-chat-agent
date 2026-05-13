"""
Core agentic loop using Groq (OpenAI-compatible API).

Handles:
- Multi-turn conversation with tool/function calling
- Parallel tool execution via asyncio.gather
- Streaming response as Server-Sent Events (SSE)
"""
import asyncio
import json
from typing import AsyncGenerator, List
from groq import AsyncGroq
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from agent.system_prompt import SYSTEM_PROMPT
from agent.tools.definitions import TOOL_DEFINITIONS
from agent.tools.registry import execute_tool

settings = get_settings()
MAX_TOOL_ROUNDS = 5

_client = None


def get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.groq_api_key)
    return _client


def _build_groq_tools() -> list:
    """Convert our tool definitions to OpenAI/Groq function calling format."""
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            },
        }
        for tool in TOOL_DEFINITIONS
    ]


async def run_agent(
    message: str,
    history: List[dict],
    session_id: str,
    db: AsyncSession,
) -> AsyncGenerator[str, None]:
    """
    Yields SSE-formatted strings.

    Event types:
    - data: {"type": "text", "content": "..."}
    - data: {"type": "tool_start", "tool": "...", "input": {...}}
    - data: {"type": "tool_result", "tool": "...", "result": {...}}
    - data: {"type": "done", "final_messages": [...]}
    - data: {"type": "error", "content": "..."}
    """
    client = get_client()
    tools = _build_groq_tools()

    # Build messages list: system + history + new user message
    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + [m for m in history if m["role"] in ("user", "assistant")]
        + [{"role": "user", "content": message}]
    )

    updated_history = list(history)
    # Track which tool names have already been called this turn
    called_tools: set = set()

    for round_num in range(MAX_TOOL_ROUNDS):
        try:
            response = await client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=2048,
            )
        except Exception as e:
            yield _sse({"type": "error", "content": str(e)})
            return

        choice = response.choices[0]
        assistant_message = choice.message

        # --- Duplicate tool-call detection BEFORE yielding anything ---
        # If the model wants to call tools, check whether they're all repeats.
        # If so, quietly inject synthetic results and force a clean text-only
        # wrap-up round — no text or tool events emitted for this round.
        if assistant_message.tool_calls:
            new_tool_names = [
                tc.function.name
                for tc in assistant_message.tool_calls
                if tc.function.name not in called_tools
            ]

            if not new_tool_names:
                # All tool calls are duplicates — suppress this round entirely.
                # Add the assistant turn + synthetic tool results to keep context valid.
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in assistant_message.tool_calls
                    ],
                })
                for tc in assistant_message.tool_calls:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": "Already answered above. Do not repeat tool calls.",
                    })
                # Continue to next round — the model will now produce a clean
                # text-only response since no new info is needed.
                continue

        # --- Normal round: yield text, then handle tool calls / done ---

        if assistant_message.content:
            yield _sse({"type": "text", "content": assistant_message.content})

        # No tool calls — conversation turn is complete
        if not assistant_message.tool_calls:
            updated_history.append({"role": "user", "content": message})
            updated_history.append({
                "role": "assistant",
                "content": assistant_message.content or "",
            })
            yield _sse({"type": "done", "final_messages": updated_history})
            return

        # Signal which tools are being called
        for tc in assistant_message.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            yield _sse({"type": "tool_start", "tool": tc.function.name, "input": args})

        # Add assistant message with tool calls to context
        messages.append({
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in assistant_message.tool_calls
            ],
        })

        # Build list of tool calls to actually execute (skip any already called)
        tool_calls_data = []
        for tc in assistant_message.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            if tc.function.name not in called_tools:
                called_tools.add(tc.function.name)
                tool_calls_data.append({"id": tc.id, "name": tc.function.name, "args": args})

        # Execute in parallel
        tasks = [
            execute_tool(tc["name"], tc["args"], db, session_id)
            for tc in tool_calls_data
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Yield tool results and append to messages
        for tc, result in zip(tool_calls_data, results):
            if isinstance(result, Exception):
                result_data = {"error": str(result)}
            else:
                result_data = result

            yield _sse({"type": "tool_result", "tool": tc["name"], "result": result_data})

            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result_data, default=str),
            })

    yield _sse({"type": "error", "content": "Max reasoning rounds reached."})


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, default=str)}\n\n"
