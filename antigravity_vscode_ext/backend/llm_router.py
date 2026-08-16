"""
LLM Router — Provider-agnostic LLM interface for the Legion Sonic Engine.
===========================================================================
Supports: NVIDIA API, Google Gemini (google-genai SDK), LM Studio (local).
All expose the same async interface so the orchestrator doesn't care which backend is active.

Default provider: "nvidia" (via OpenAI-compatible endpoint at integrate.api.nvidia.com)
Optional provider: "gemini" (via google.genai SDK — NOT langchain)
Local fallback: "lmstudio" (localhost:1234 OpenAI-compatible)
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any, Callable
from dotenv import load_dotenv

# Load environment
env_path = os.path.join("C:\\", "WEB CASE STUDY", ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

logger = logging.getLogger("llm_router")

# ---------------------------------------------------------------------------
# Provider configs from .env
# ---------------------------------------------------------------------------
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_DEFAULT_MODEL = os.getenv("DEFAULT_MODELS", "meta/llama-3.1-70b-instruct")

LMSTUDIO_BASE_URL = "http://127.0.0.1:1234/v1"
LMSTUDIO_API_KEY = "lm-studio"

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"


class LLMRouter:
    """
    Unified async LLM client. Wraps OpenAI-compatible endpoints (NVIDIA, LM Studio)
    and the google-genai SDK behind one interface.
    """

    PROVIDERS = {"nvidia", "gemini", "lmstudio"}

    def __init__(self, provider: str = "nvidia"):
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unknown provider '{provider}'. Choose from: {self.PROVIDERS}")
        self.provider = provider
        self._openai_client = None
        self._genai_client = None
        self._genai_chat = None
        logger.info(f"LLMRouter initialized with provider: {self.provider}")

    # ------------------------------------------------------------------
    # Lazy client initialization
    # ------------------------------------------------------------------
    def _get_openai_client(self):
        """Returns an AsyncOpenAI client for NVIDIA or LM Studio."""
        if self._openai_client is None:
            from openai import AsyncOpenAI

            if self.provider == "nvidia":
                self._openai_client = AsyncOpenAI(
                    base_url=NVIDIA_BASE_URL,
                    api_key=NVIDIA_API_KEY,
                )
            elif self.provider == "lmstudio":
                self._openai_client = AsyncOpenAI(
                    base_url=LMSTUDIO_BASE_URL,
                    api_key=LMSTUDIO_API_KEY,
                )
        return self._openai_client

    def _get_genai_client(self):
        """Returns a google.genai Client for Gemini."""
        if self._genai_client is None:
            from google import genai
            self._genai_client = genai.Client(api_key=GOOGLE_API_KEY)
        return self._genai_client

    # ------------------------------------------------------------------
    # Core chat method — provider-agnostic
    # ------------------------------------------------------------------
    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request.

        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": "..."}
            tools: Optional OpenAI-format tool/function definitions
            system_prompt: Prepended as a system message if provided
            temperature: Sampling temperature
            max_tokens: Max response tokens

        Returns:
            {"content": str, "tool_calls": list|None, "provider": str, "model": str}
        """
        if self.provider in ("nvidia", "lmstudio"):
            return await self._chat_openai(messages, tools, system_prompt, temperature, max_tokens)
        elif self.provider == "gemini":
            return await self._chat_gemini(messages, tools, system_prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Provider {self.provider} not implemented")

    # ------------------------------------------------------------------
    # OpenAI-compatible implementation (NVIDIA / LM Studio)
    # ------------------------------------------------------------------
    async def _chat_openai(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        client = self._get_openai_client()
        model = NVIDIA_DEFAULT_MODEL if self.provider == "nvidia" else "local-model"

        # Build message list
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Only pass tools if the provider supports them and we have some
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            response = await client.chat.completions.create(**kwargs)
            choice = response.choices[0]

            result: Dict[str, Any] = {
                "content": choice.message.content or "",
                "tool_calls": None,
                "provider": self.provider,
                "model": model,
            }

            # Extract tool calls if present
            if choice.message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments),
                    }
                    for tc in choice.message.tool_calls
                ]

            return result

        except Exception as e:
            logger.error(f"OpenAI-compatible chat error ({self.provider}): {e}", exc_info=True)
            raise

    # ------------------------------------------------------------------
    # Google GenAI SDK implementation (NOT langchain)
    # ------------------------------------------------------------------
    async def _chat_gemini(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        from google import genai
        from google.genai import types

        client = self._get_genai_client()

        # Build contents for genai
        contents = []
        if system_prompt:
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(f"[System Instructions]: {system_prompt}")]
            ))
            contents.append(types.Content(
                role="model",
                parts=[types.Part.from_text("Understood. I will follow these instructions.")]
            ))

        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(msg["content"])]
            ))

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        # Convert OpenAI-format tools to genai function declarations if provided
        if tools:
            genai_tools = self._convert_tools_to_genai(tools)
            if genai_tools:
                config.tools = genai_tools

        try:
            response = await client.aio.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=config,
            )

            result: Dict[str, Any] = {
                "content": response.text or "",
                "tool_calls": None,
                "provider": "gemini",
                "model": GEMINI_MODEL,
            }

            # Extract function calls if present
            if response.candidates and response.candidates[0].content.parts:
                func_calls = []
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        func_calls.append({
                            "id": f"gemini_{fc.name}",
                            "name": fc.name,
                            "arguments": dict(fc.args) if fc.args else {},
                        })
                if func_calls:
                    result["tool_calls"] = func_calls

            return result

        except Exception as e:
            logger.error(f"Gemini chat error: {e}", exc_info=True)
            raise

    # ------------------------------------------------------------------
    # Tool format conversion helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _convert_tools_to_genai(openai_tools: List[Dict]) -> list:
        """Convert OpenAI-format tool definitions to google.genai function declarations."""
        from google.genai import types

        declarations = []
        for tool_def in openai_tools:
            func = tool_def.get("function", tool_def)
            params = func.get("parameters", {})

            # Build genai-compatible Schema from OpenAI JSON Schema
            properties = {}
            for prop_name, prop_def in params.get("properties", {}).items():
                prop_type = prop_def.get("type", "string").upper()
                # Map JSON Schema types to genai Type enum
                type_map = {"STRING": "STRING", "INTEGER": "INTEGER", "NUMBER": "NUMBER", "BOOLEAN": "BOOLEAN"}
                properties[prop_name] = types.Schema(
                    type=type_map.get(prop_type, "STRING"),
                    description=prop_def.get("description", ""),
                )

            declarations.append(types.FunctionDeclaration(
                name=func.get("name", "unknown"),
                description=func.get("description", ""),
                parameters=types.Schema(
                    type="OBJECT",
                    properties=properties,
                    required=params.get("required", []),
                ) if properties else None,
            ))

        return [types.Tool(function_declarations=declarations)] if declarations else []

    @staticmethod
    def build_tool_schema(name: str, description: str, parameters: Dict[str, Any]) -> Dict:
        """
        Helper to build an OpenAI-format tool definition from simple inputs.
        This is the universal format — works with NVIDIA, LM Studio, and converts to Gemini.
        """
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------
def create_router(provider: Optional[str] = None) -> LLMRouter:
    """Create an LLMRouter with the specified or environment-configured provider."""
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "nvidia")
    return LLMRouter(provider=provider)
