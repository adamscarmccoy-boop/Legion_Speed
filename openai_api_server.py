"""
OpenAI-Compatible API Server for the Legion LangGraph Audio Agent.
This server wraps the LangGraph agent and exposes it via the standard
OpenAI /v1/chat/completions and /v1/models endpoints so that
OpenWebUI (or any OpenAI-compatible client) can connect to it.

Run:  python openai_api_server.py
      (or) uvicorn openai_api_server:app --host 0.0.0.0 --port 8080
"""

import os
import sys
import json
import time
import uuid
import asyncio
import logging
from typing import List, Dict, Any, Optional

# --- FastAPI & SSE Streaming ---
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

# --- LangChain Message Types ---
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)

# --- Your Agent ---
# Import your fixed agent class. Adjust the import path to match your filename.
from legion_agent import LegionLangGraphAgent

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("openai_api_server")

# ──────────────────────────────────────────────
# Pydantic Models for OpenAI-Compatible Request/Response
# ──────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    tool_call_id: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str = "legion-sonic-engine"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    top_p: Optional[float] = 1.0


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None


class ModelsResponse(BaseModel):
    object: str = "list"
    data: List[Dict[str, Any]]


# ──────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────

app = FastAPI(
    title="Legion Sonic Engine - OpenAI-Compatible API",
    description="LangGraph-powered audio analysis & mastering agent.",
    version="1.0.0",
)

# Enable CORS so any client can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# Initialize the LangGraph Agent
# ──────────────────────────────────────────────

# You can switch provider here: "nvidia" | "lmstudio" | "gemini"
AGENT_PROVIDER = os.getenv("AGENT_PROVIDER", "nvidia")
AGENT_RECURSION_LIMIT = int(os.getenv("AGENT_RECURSION_LIMIT", "3"))

logger.info(f"Initializing LegionLangGraphAgent (provider={AGENT_PROVIDER})...")
try:
    agent_instance = LegionLangGraphAgent(
        max_recursion_limit=AGENT_RECURSION_LIMIT,
        provider=AGENT_PROVIDER,
    )
    logger.info("✅ Agent initialized successfully.")
except Exception as e:
    logger.error(f"❌ Failed to initialize agent: {e}", exc_info=True)
    # We'll still start the server so OpenWebUI can at least see the /v1/models endpoint
    agent_instance = None


# ──────────────────────────────────────────────
# Helper: Convert OpenAI messages → LangChain BaseMessages
# ──────────────────────────────────────────────

def convert_openai_messages_to_langchain(
    messages: List[ChatMessage],
) -> List[BaseMessage]:
    """Converts OpenAI-format chat messages into LangChain BaseMessage objects."""
    converted: List[BaseMessage] = []

    for msg in messages:
        if msg.role == "system":
            converted.append(SystemMessage(content=msg.content))
        elif msg.role == "user":
            converted.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            converted.append(AIMessage(content=msg.content))
        elif msg.role == "tool":
            converted.append(
                ToolMessage(content=msg.content, tool_call_id=msg.tool_call_id or "")
            )
        else:
            # Fallback: treat unknown roles as human messages
            logger.warning(f"Unknown message role '{msg.role}', treating as user.")
            converted.append(HumanMessage(content=msg.content))

    return converted


# ──────────────────────────────────────────────
# Helper: Extract final assistant text from agent state
# ──────────────────────────────────────────────

def extract_final_response(state: Dict[str, Any]) -> str:
    """Pulls the last AIMessage content from the agent's final state."""
    messages = state.get("messages", [])
    # Walk backwards to find the last AIMessage with non-empty content
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            return msg.content
        elif isinstance(msg, AIMessage) and msg.tool_calls and msg.content:
            # If the last AI message has both tool calls and content, return the content
            return msg.content
    # Fallback: return whatever the last message content is
    if messages:
        last = messages[-1]
        if hasattr(last, "content"):
            return str(last.content)
    return "I was unable to process your request."


# ──────────────────────────────────────────────
# Helper: Collect tool-call summaries from agent state
# ──────────────────────────────────────────────

def extract_tool_summaries(state: Dict[str, Any]) -> List[str]:
    """Extracts a human-readable summary of tool calls made during the agent run."""
    summaries = []
    messages = state.get("messages", [])
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                summaries.append(f"🔧 Calling tool: {tc['name']} with args: {tc['args']}")
        elif isinstance(msg, ToolMessage):
            # Truncate long tool outputs for the UI display
            content = msg.content
            if len(content) > 500:
                content = content[:500] + "...[truncated]"
            summaries.append(f"📊 Tool result: {content}")
    return summaries


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "status": "running",
        "agent_initialized": agent_instance is not None,
        "provider": AGENT_PROVIDER,
        "endpoints": {
            "chat": "/v1/chat/completions",
            "models": "/v1/models",
            "health": "/health",
        },
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy" if agent_instance else "degraded",
        "agent_ready": agent_instance is not None,
    }


@app.get("/v1/models")
async def list_models():
    """Returns available models in OpenAI-compatible format."""
    models = [
        {
            "id": "legion-sonic-engine",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "legion-dsp",
        }
    ]
    return ModelsResponse(data=models)


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    Main OpenAI-compatible chat endpoint.
    Runs the full LangGraph agent (including tool calls) and returns the result.
    Supports both streaming (SSE) and non-streaming responses.
    """
    if agent_instance is None:
        raise HTTPException(
            status_code=503,
            detail="Agent is not initialized. Check server logs for startup errors.",
        )

    # Convert incoming OpenAI messages to LangChain format
    lc_messages = convert_openai_messages_to_langchain(request.messages)

    logger.info(
        f"Chat completion request: model={request.model}, "
        f"messages={len(request.messages)}, stream={request.stream}"
    )

    # Run the agent graph asynchronously
    try:
        # Build initial state
        initial_state = {
            "messages": lc_messages,
            "recursion_count": 0,
            "max_recursion_limit": AGENT_RECURSION_LIMIT,
        }

        # Run the LangGraph agent
        final_state = await agent_instance.graph.ainvoke(initial_state)

    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    # Extract the final response text and tool summaries
    final_text = extract_final_response(final_state)
    tool_summaries = extract_tool_summaries(final_state)

    # Build the full response (include tool call summaries as a preface)
    if tool_summaries:
        full_response = "**Agent Tool Calls:**\n\n"
        full_response += "\n".join(tool_summaries)
        full_response += "\n\n---\n\n**Final Response:**\n\n"
        full_response += final_text
    else:
        full_response = final_text

    request_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    created = int(time.time())

    # ── Non-streaming response ──
    if not request.stream:
        response = ChatCompletionResponse(
            id=request_id,
            created=created,
            model=request.model,
            choices=[
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": full_response,
                    },
                    "finish_reason": "stop",
                }
            ],
            usage={
                "prompt_tokens": -1,   # We don't count tokens; set to -1
                "completion_tokens": -1,
                "total_tokens": -1,
            },
        )
        return response

    # ── Streaming (SSE) response ──
    # We simulate streaming by chunking the final response text.
    # (True token-by-token streaming would require hooking into LangChain's
    #  astream_events, which is more complex but possible.)

    async def stream_response():
        # Send tool summaries first (if any)
        if tool_summaries:
            summary_text = "**Agent Tool Calls:**\n\n" + "\n".join(tool_summaries) + "\n\n---\n\n**Final Response:**\n\n"
            chunk_size = 20  # characters per chunk
            for i in range(0, len(summary_text), chunk_size):
                chunk = summary_text[i : i + chunk_size]
                sse_data = {
                    "id": request_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": request.model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": chunk},
                            "finish_reason": None,
                        }
                    ],
                }
                yield f"data: {json.dumps(sse_data)}\n\n"
                await asyncio.sleep(0.02)  # Small delay for streaming effect

        # Stream the final response text
        chunk_size = 5  # characters per chunk for natural feel
        for i in range(0, len(final_text), chunk_size):
            chunk = final_text[i : i + chunk_size]
            sse_data = {
                "id": request_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": chunk},
                        "finish_reason": None,
                    }
                ],
            }
            yield f"data: {json.dumps(sse_data)}\n\n"
            await asyncio.sleep(0.01)

        # Send the final "stop" chunk
        stop_data = {
            "id": request_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop",
                }
            ],
        }
        yield f"data: {json.dumps(stop_data)}\n\n"

        # Send [DONE]
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
    )


# ──────────────────────────────────────────────
# Main Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    HOST = os.getenv("API_SERVER_HOST", "0.0.0.0")
    PORT = int(os.getenv("API_SERVER_PORT", "8080"))

    logger.info(f"Starting OpenAI-compatible API server on {HOST}:{PORT}")
    logger.info(f"Agent provider: {AGENT_PROVIDER}")
    logger.info(f"Recursion limit: {AGENT_RECURSION_LIMIT}")
    logger.info(f"OpenWebUI should connect to: http://localhost:{PORT}/v1")

    uvicorn.run(
        "openai_api_server:app",
        host=HOST,
        port=PORT,
        reload=False,  # Disable reload in production; enable for dev
        log_level="info",
    )
