"""Direct NIM smoke test.

Reads NVIDIA_API_KEY from env, calls openai/gpt-oss-120b on
integrate.api.nvidia.com, exercises both plain chat and a single
tool-calling round-trip, and prints only safe diagnostics
(lengths, model id, finish reason, request id). Never prints the key.
"""

from __future__ import annotations

import json
import os
import sys
from openai import OpenAI, APITimeoutError, APIError

# Make sure no library can accidentally echo the key in a traceback.
os.environ.setdefault("NVIDIA_API_KEY", os.environ.get("NVIDIA_API_KEY", ""))
if not os.environ["NVIDIA_API_KEY"]:
    print("ERROR: NVIDIA_API_KEY is not set in the environment.", file=sys.stderr)
    sys.exit(2)

BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = "openai/gpt-oss-120b"
# 30s is generous for an inference call; if it hasn't returned by then we want
# to know, not wait forever.
HTTP_TIMEOUT = 30.0

# Sanity: only print a short fingerprint, never the key itself.
_key = os.environ["NVIDIA_API_KEY"]
print(
    f"# key fingerprint: len={len(_key)} prefix={_key[:6]}... suffix=...{_key[-4:]}",
    file=sys.stderr,
)

client = OpenAI(base_url=BASE_URL, api_key=_key, timeout=HTTP_TIMEOUT)


def safe_dump(label: str, obj) -> None:
    """Print a label and a compact summary of the object — never the raw key."""
    if hasattr(obj, "model_dump"):
        data = obj.model_dump()
    elif isinstance(obj, dict):
        data = obj
    else:
        data = {"repr": repr(obj)}
    data.pop("api_key", None)
    data.pop("key", None)
    print(f"--- {label} ---")
    print(json.dumps(data, indent=2, default=str)[:1500])


# 1. Plain chat completion.
print("\n=== 1. plain chat ===", file=sys.stderr)
try:
    resp1 = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a concise assistant. Reply in one sentence."},
            {"role": "user", "content": "What is 2 + 2? Reply with just the number."},
        ],
        temperature=0.0,
        max_tokens=32,
    )
except (APITimeoutError, APIError) as e:
    print(f"PLAIN_CHAT_FAILED: {type(e).__name__}: {e}", file=sys.stderr)
    resp1 = None
if resp1 is not None:
    safe_dump("plain_chat", resp1)
    print(
        f"plain_chat finish_reason={resp1.choices[0].finish_reason} "
        f"content={resp1.choices[0].message.content!r}",
        file=sys.stderr,
    )

# 2. Tool-calling round trip — see if gpt-oss-120b emits a tool call correctly.
print("\n=== 2. tool call ===", file=sys.stderr)
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }
]
resp2 = None
try:
    resp2 = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "What's the weather in Tokyo right now?"},
        ],
        tools=tools,
        tool_choice="auto",
        temperature=0.0,
        max_tokens=128,
    )
except (APITimeoutError, APIError) as e:
    print(f"TOOL_CALL_FAILED: {type(e).__name__}: {e}", file=sys.stderr)
if resp2 is not None:
    choice = resp2.choices[0]
    print(
        f"tool_call finish_reason={choice.finish_reason} "
        f"tool_calls={[tc.function.name for tc in (choice.message.tool_calls or [])]}",
        file=sys.stderr,
    )
    safe_dump("tool_call_response", resp2)
