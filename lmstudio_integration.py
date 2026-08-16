import asyncio
import json
import logging
import os
import sys
from typing import Any, Callable, Dict, List, Optional

# LM Studio typically runs on port 1234 by default, but memory states the user environment explicitly uses port 1010.
LM_STUDIO_API_BASE = "http://localhost:1010/v1"

logger = logging.getLogger(__name__)
# Suppress httpx logging
logging.getLogger("httpx").setLevel(logging.WARNING)

class LMStudioClient:
    """
    A lightweight asynchronous client for LM Studio, inspired by `lmstudio-js` and `lmstudio-python`.
    It interfaces with the local OpenAI-compatible REST API.
    """

    def __init__(self, api_base: str = LM_STUDIO_API_BASE, timeout: int = 60):
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        try:
            import httpx
            self._client = httpx.AsyncClient(timeout=self.timeout)
        except ImportError:
            # Fallback or error if httpx is not present in the environment
            raise RuntimeError("httpx library is required. Install via `pip install httpx`")

    async def list_models(self) -> List[Dict[str, Any]]:
        """Retrieve the list of models currently loaded in LM Studio."""
        url = f"{self.api_base}/models"
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            return response.json().get("data", [])
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    async def chat_completion(self, messages: List[Dict[str, str]], model: str = "local-model", **kwargs) -> Dict[str, Any]:
        """
        Send a chat completion request to LM Studio.
        """
        url = f"{self.api_base}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise

    async def act(
        self,
        prompt: str,
        tools: List[Callable],
        model: str = "local-model",
        system_prompt: str = "You are a helpful AI assistant. You can use tools to solve problems.",
        max_iterations: int = 5,
        history: Optional[List[Dict[str, str]]] = None
    ) -> tuple[str, List[Dict[str, str]]]:
        """
        Simulates the `.act()` autonomous agent loop from `lmstudio-js`.
        It allows the LLM to call provided Python functions (tools).

        Returns the final content string and the updated message history.
        """
        if history is None:
            messages = [
                {"role": "system", "content": system_prompt},
            ]
        else:
            messages = history.copy()

        messages.append({"role": "user", "content": prompt})

        # Convert Python callables to OpenAI tool definitions
        openai_tools = [self._callable_to_tool(tool) for tool in tools]
        tool_map = {tool.__name__: tool for tool in tools}

        for iteration in range(max_iterations):
            try:
                response = await self.chat_completion(
                    messages=messages,
                    model=model,
                    tools=openai_tools,
                    tool_choice="auto"
                )
            except Exception as e:
                return f"API Error: {e}", messages

            message = response["choices"][0]["message"]
            messages.append(message)

            if not message.get("tool_calls"):
                # No more tool calls, return final response
                return message.get("content", ""), messages

            for tool_call in message["tool_calls"]:
                func_name = tool_call["function"]["name"]
                args_str = tool_call["function"]["arguments"]
                call_id = tool_call["id"]

                print(f"\\033[93m[System: Agent calling tool '{func_name}' with args {args_str}]\\033[0m")

                try:
                    args = json.loads(args_str)
                    if func_name in tool_map:
                        # Execute the tool
                        result = tool_map[func_name](**args)
                        result_str = str(result)
                    else:
                        result_str = f"Error: Tool '{func_name}' not found."
                except Exception as e:
                    result_str = f"Error executing '{func_name}': {e}"

                # Append tool result to history
                messages.append({
                    "role": "tool",
                    "content": result_str,
                    "tool_call_id": call_id
                })

        return "Error: Maximum iterations reached without final answer.", messages

    def _callable_to_tool(self, func: Callable) -> Dict[str, Any]:
        """
        Naively converts a Python function to an OpenAI tool definition.
        """
        import inspect
        doc = inspect.getdoc(func) or "No description provided."
        sig = inspect.signature(func)

        properties = {}
        required = []
        for name, param in sig.parameters.items():
            properties[name] = {"type": "string"} # Simplified: assume string if unknown
            if param.annotation is int:
                properties[name]["type"] = "integer"
            elif param.annotation is float:
                properties[name]["type"] = "number"
            elif param.annotation is bool:
                properties[name]["type"] = "boolean"

            if param.default is inspect.Parameter.empty:
                required.append(name)

        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": doc,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    async def close(self):
        await self._client.aclose()


# --- TOOLS ---

def list_directory(path: str) -> str:
    """Lists all files and directories in the given path."""
    try:
        items = os.listdir(path)
        return f"Contents of '{path}':\\n" + "\\n".join(items)
    except Exception as e:
        return f"Error listing directory: {e}"

def read_file_content(filepath: str) -> str:
    """Reads the contents of the specified file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def search_files(directory: str, keyword: str) -> str:
    """Searches for a keyword in all files within the given directory (non-recursive)."""
    results = []
    try:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        if keyword in f.read():
                            results.append(filename)
                except:
                    pass
        if results:
            return f"Files containing '{keyword}': " + ", ".join(results)
        return f"No files contained '{keyword}'."
    except Exception as e:
        return f"Error searching files: {e}"


# --- TERMINAL APP ---

async def terminal_chat():
    print("\\033[96m" + "="*50)
    print("🤖 SOLO TERMINAL CHAT (LM Studio Backend)")
    print("   Data Access: Local Filesystem Only (No SQL3)")
    print("="*50 + "\\033[0m")

    client = LMStudioClient()

    print("Checking LM Studio connection...")
    try:
        models = await client.list_models()
        if not models:
            print("\\033[91mNo models currently loaded in LM Studio. Please load a model in the UI.\\033[0m")
            return

        # Use the first loaded model, or default to a common name
        model_name = models[0].get("id", "local-model")
        print(f"\\033[92mConnected! Using model: {model_name}\\033[0m")
    except Exception as e:
        print(f"\\033[91mFailed to connect to LM Studio at {client.api_base}. Ensure it is running and CORS is enabled.\\033[0m")
        print(f"Error: {e}")
        return

    tools = [list_directory, read_file_content, search_files]

    system_prompt = (
        "You are an expert coding assistant with access to the local filesystem. "
        "You help the user navigate their codebase, read files, and write code. "
        "You must use the provided tools to interact with data instead of guessing."
    )

    history = [{"role": "system", "content": system_prompt}]

    print("\\nType 'exit' or 'quit' to end the session.")
    print("\\033[90m(Available tools: list_directory, read_file_content, search_files)\\033[0m\\n")

    try:
        while True:
            try:
                user_input = input("\\033[94mYou: \\033[0m")
            except (EOFError, KeyboardInterrupt):
                break

            if user_input.lower() in ['exit', 'quit']:
                break

            if not user_input.strip():
                continue

            print("\\033[90mThinking...\\033[0m")

            # Use the .act() logic to handle tool use
            response_content, history = await client.act(
                prompt=user_input,
                tools=tools,
                model=model_name,
                system_prompt=system_prompt,
                history=history
            )

            print(f"\\n\\033[92mAssistant:\\033[0m {response_content}\\n")

    finally:
        print("\\n\\033[96mGoodbye!\\033[0m")
        await client.close()

if __name__ == "__main__":
    # If run with --help or -h, just print a message and exit (useful for testing execution)
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "--test"]:
        print("LM Studio Integration Script.")
        sys.exit(0)

    asyncio.run(terminal_chat())
