"""
NVIDIA NIM Nemotron MCP server (stdio).
Uses FastMCP + Pydantic schemas.
Reads NVIDIA_API_KEY from environment.
"""
import os
import json
import sys
from typing import List, Optional, Literal

import httpx
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

# ==============================================================================
# SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
# Prevents dangling stdout/stdio pipes and GCS registry locks on Windows exit
# ==============================================================================
import atexit
import signal

def clean_exit_handler(*args, **kwargs):
    import sys
    sys.stderr.write("\n[LMS LIFECYCLE] Exit triggered. Flushing system streams...\n")
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write("[LMS LIFECYCLE] Active Ray session detected. Disconnecting...\n")
            ray.shutdown()
    except Exception:
        pass
    sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

DEFAULT_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1"

# Curated model presets (Nemotron family first, fallback NVIDIA + partners)
MODEL_PRESETS: dict[str, str] = {
    "nemotron-super":    "nvidia/llama-3.3-nemotron-super-49b-v1",
    "nemotron-super-15": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
    "nemotron-ultra":    "nvidia/llama-3.1-nemotron-ultra-253b-v1",
    "nemotron-51b":      "nvidia/llama-3.1-nemotron-51b-instruct",
    "nemotron-70b":      "nvidia/llama-3.1-nemotron-70b-instruct",
    "nemotron-nano":     "nvidia/llama-3.1-nemotron-nano-8b-v1",
    "nemotron-340b":     "nvidia/nemotron-4-340b-instruct",
    "nemotron-3-super":  "nvidia/nemotron-3-super-120b-a12b",
    "nemotron-3-ultra":  "nvidia/nemotron-3-ultra-550b-a55b",
    "nemotron-3-nano":   "nvidia/nemotron-3-nano-30b-a3b",
    "nemotron-3-omni":   "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    "cosmos-reason2":    "nvidia/cosmos-reason2-8b",
    "kimi":              "moonshotai/kimi-k2.6",
    "deepseek-pro":      "deepseek-ai/deepseek-v4-pro",
}


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = "user"
    content: str = Field(..., min_length=1)


class NemotronChatInput(BaseModel):
    prompt: str = Field(..., description="User prompt")
    model: str = Field(default=DEFAULT_MODEL, description="Model id or preset name")
    system: Optional[str] = Field(default=None, description="Optional system prompt")
    temperature: float = Field(default=0.6, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    preset: Optional[Literal[*MODEL_PRESETS.keys()]] = None  # type: ignore


class NemotronChatOutput(BaseModel):
    model: str
    content: str
    finish_reason: str = ""


def _resolve_model(model: str, preset: Optional[str]) -> str:
    if preset and preset in MODEL_PRESETS:
        return MODEL_PRESETS[preset]
    if model in MODEL_PRESETS:
        return MODEL_PRESETS[model]
    return model


def _call_nim(payload: dict) -> dict:
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY not set in environment")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    with httpx.Client(timeout=120.0) as client:
        r = client.post(API_URL, headers=headers, json=payload)
        if r.status_code >= 400:
            raise RuntimeError(f"NIM {r.status_code}: {r.text[:500]}")
        return r.json()


mcp = FastMCP("nvidia-nim-nemotron")


@mcp.tool()
def list_models() -> dict:
    """List curated Nemotron/NVIDIA model presets available on integrate.api.nvidia.com."""
    return {"presets": MODEL_PRESETS, "default": DEFAULT_MODEL}


@mcp.tool()
def nemotron_chat(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system: Optional[str] = None,
    temperature: float = 0.6,
    max_tokens: int = 1024,
) -> dict:
    """Send a single-turn chat completion to NVIDIA NIM (Nemotron family by default).

    Args:
        prompt: User prompt.
        model: Full model id (e.g. nvidia/llama-3.3-nemotron-super-49b-v1).
        system: Optional system prompt.
        temperature: Sampling temperature 0.0-2.0.
        max_tokens: Max output tokens (1-8192).
    """
    inp = NemotronChatInput(
        prompt=prompt, model=model, system=system,
        temperature=temperature, max_tokens=max_tokens,
    )
    resolved = _resolve_model(inp.model, None)
    messages: List[dict] = []
    if inp.system:
        messages.append({"role": "system", "content": inp.system})
    messages.append({"role": "user", "content": inp.prompt})

    payload = {
        "model": resolved,
        "messages": messages,
        "temperature": inp.temperature,
        "max_tokens": inp.max_tokens,
        "stream": False,
    }
    raw = _call_nim(payload)
    choice = raw.get("choices", [{}])[0]
    msg = choice.get("message", {}) or {}
    out = NemotronChatOutput(
        model=resolved,
        content=msg.get("content", ""),
        finish_reason=choice.get("finish_reason", ""),
    )
    return out.model_dump()


@mcp.tool()
def nemotron_preset_chat(preset: str, prompt: str, max_tokens: int = 1024) -> dict:
    """Chat using a named preset (e.g. 'nemotron-super', 'nemotron-ultra', 'cosmos-reason2').

    Args:
        preset: One of the keys from list_models().
        prompt: User prompt.
        max_tokens: Max output tokens.
    """
    if preset not in MODEL_PRESETS:
        raise ValueError(f"Unknown preset '{preset}'. Call list_models() first.")
    resolved = MODEL_PRESETS[preset]
    messages = [{"role": "user", "content": prompt}]
    payload = {
        "model": resolved,
        "messages": messages,
        "temperature": 0.6,
        "max_tokens": max_tokens,
        "stream": False,
    }
    raw = _call_nim(payload)
    choice = raw.get("choices", [{}])[0]
    msg = choice.get("message", {}) or {}
    out = NemotronChatOutput(
        model=resolved,
        content=msg.get("content", ""),
        finish_reason=choice.get("finish_reason", ""),
    )
    return out.model_dump()


@mcp.tool()
def nemotron_reason(prompt: str, max_tokens: int = 2048) -> dict:
    """High-reasoning call routed through nemotron-3-omni (reasoning specialist)."""
    preset = "nemotron-3-omni"
    resolved = MODEL_PRESETS[preset]
    messages = [
        {"role": "system", "content": "Think step by step, then give the final answer."},
        {"role": "user", "content": prompt},
    ]
    payload = {
        "model": resolved,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": max_tokens,
        "stream": False,
    }
    raw = _call_nim(payload)
    choice = raw.get("choices", [{}])[0]
    msg = choice.get("message", {}) or {}
    return {"model": resolved, "content": msg.get("content", ""),
            "finish_reason": choice.get("finish_reason", "")}


if __name__ == "__main__":
    # Pass NVIDIA_API_KEY through even when launched without shell env expanded
    if "NVIDIA_API_KEY" not in os.environ and os.environ.get("NVIDIA_API_KEY_FILE"):
        try:
            with open(os.environ["NVIDIA_API_KEY_FILE"]) as f:
                os.environ["NVIDIA_API_KEY"] = f.read().strip()
        except Exception:
            pass
    mcp.run()