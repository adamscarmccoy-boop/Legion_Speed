import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
os.environ["LOGFIRE_CONFIG_FILE"] = ""
import json
import asyncio
import inspect
from typing import Any, Dict, List, Type, Optional
from pydantic import ValidationError

# Core Legion Imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "antigravity_vscode_ext", "backend"))

try:
    from legion_langgraph_brain import LegionLangGraphAgent
    import sovereign_schemas as schemas 
    from langchain_core.messages import HumanMessage
except ImportError as e:
    print(f"❌ CRITICAL: Could not import Legion Brain components: {e}")
    sys.exit(1)

# UI Imports
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.live import Live
    from rich.prompt import Prompt, Confirm
    from rich.syntax import Syntax
    from rich.theme import Theme
    USE_RICH = True
except ImportError:
    print("⚠️ 'rich' library not found. Please run 'pip install rich' for the full experience.")
    USE_RICH = False

# --- THEME CONFIGURATION ---
custom_theme = Theme({
    "legion.info": "cyan",
    "legion.success": "bold green",
    "legion.warning": "bold yellow",
    "legion.error": "bold red",
    "legion.reasoning": "italic dim magenta",
    "legion.node": "bold bright_blue",
    "legion.tool": "bold bright_green"
})

class LegionInteractiveCLI:
    def __init__(self):
        self.console = Console(theme=custom_theme) if USE_RICH else None
        self.app = LegionLangGraphAgent()
        
        # Mapping of intent keywords to Pydantic Models for underspecification interception
        self.intent_registry = {
            "audio": "AudioRequest",
            "generate": "AudioRequest",
            "sound": "AudioRequest",
            "search": "SearchRequest",
            "find": "SearchRequest",
            "vector": "LanceDBQuery",
            "sql": "DuckDBQuery",
            "file": "FileReadRequest",
            "write": "FileWriteRequest",
            "shell": "ShellCommandRequest",
            "browser": "BrowserNavigateRequest",
            "task": "TaskCreateRequest"
        }
        # Attempt to dynamically map model names to actual classes in your schema module
        self.model_map: Dict[str, Type] = {}
        self._load_schemas()

    def _load_schemas(self):
        """Introspects the sovereign_schemas module to map class names to Pydantic objects."""
        for name, obj in inspect.getmembers(schemas):
            if inspect.isclass(obj) and hasattr(obj, "model_fields"):
                self.model_map[name] = obj

    def _print(self, text: str, style: str = ""):
        if self.console:
            self.console.print(text, style=style)
        else:
            print(text)

    def display_capabilities(self):
        """Requirement 1: List available capabilities/options on startup."""
        self._print("\n[bold]Initializing Sovereign Intelligence Interface...[/bold]")
        
        table = Table(title="Legion Intelligence Capabilities", expand=True)
        table.add_column("Capability (Tool)", style="legion.node")
        table.add_column("Description", style="legion.info")
        table.add_column("Data Source", style="legion.tool")

        for tool in self.app.tools:
            name = tool.name
            desc = tool.description.split('\n')[0] # First line of docstring
            
            source = "Local/Generic"
            if "duckdb" in desc.lower() or "sql" in name.lower(): source = "DuckDB"
            elif "lancedb" in desc.lower() or "vector" in name.lower(): source = "LanceDB"
            elif "parquet" in desc.lower(): source = "Parquet Lake"

            table.add_row(f"[bold]{name}[/bold]", desc, source)

        if self.console:
            self.console.print(table)
        else:
            print(table)

        self._print("\n[dim]System Status: Operational | Agents: Gemma-2-2b-it ONNX | Protocol: LangGraph[/dim]\n")

    def _check_underspecification(self, user_query: str) -> Optional[Type[Any]]:
        """Requirement 3: Intercept underspecified queries using Pydantic Schema definitions."""
        query_lower = user_query.lower()
        target_model_name = None
        
        for keyword, model_name in self.intent_registry.items():
            if keyword in query_lower:
                target_model_name = model_name
                break
        
        if target_model_name and target_model_name in self.model_map:
            return self.model_map[target_model_name]
        return None

    async def _intercept_and_prompt(self, user_query: str, model: Type[Any]):
        """Requirement 3: Prompts user with choices based on Pydantic schema definition."""
        self._print(f"\n[legion.reasoning]Sovereign Logic: Query detected as intent '{model.__name__}'.[/legion.reasoning]")
        self._print(f"[legion.warning]Underspecification Detected:[/legion.warning]")
        self._print(f"The `{model.__name__}` schema requires specific parameters to proceed.")

        # Get required fields from Pydantic
        required_fields = model.model_fields
        missing_fields = []
        
        for field_name, field_info in required_fields.items():
            if field_info.is_required():
                if field_name.lower() not in user_query.lower():
                    missing_fields.append(field_name)

        if not missing_fields:
            return True # Proceed

        # Interactive prompting
        self._print(f"\n[bold]Please provide the following missing parameters for `{model.__name__}`:[/bold]")
        params = {}
        for field in missing_fields:
            val = Prompt.ask(f"  [cyan]{field}[/cyan]")
            params[field] = val
        
        self._print(f"\n[legion.success]Parameters captured. Integrating into context...[/legion.success]")
        return f"Context Update: {json.dumps(params)}"

    async def run_session(self):
        """The main execution loop."""
        self.display_capabilities()

        while True:
            try:
                user_input = Prompt.ask("\n[bold white]LEGION[/bold white] ❯")
            except EOFError:
                self._print("\n[yellow]Input stream closed. Exiting...[/yellow]")
                break
                
            if user_input.lower() in ['exit', 'quit', 'q']:
                self._print("[yellow]Closing connection... Goodbye.[/yellow]")
                break

            # 1. Intercept Underspecification
            model_to_check = self._check_underspecification(user_input)
            if model_to_check:
                extra_context = await self._intercept_and_prompt(user_input, model_to_check)
                if isinstance(extra_context, str):
                    user_input = f"{user_input} ({extra_context})"

            # 2. Execute with Reasoning Streaming
            self._print("\n[legion.reasoning]Commencing Graph Traversal...[/legion.reasoning]")
            
            try:
                final_answer = "No response generated."
                # Stream reasoning processes of the nodes
                async for event in self.app.graph.astream(
                    {
                        "messages": [HumanMessage(content=user_input)], 
                        "active_dna_context": {},
                        "recursion_count": 0,
                        "max_recursion_limit": self.app.max_recursion_limit
                    },
                    stream_mode="updates"
                ):
                    for node_name, output in event.items():
                        if self.console:
                            self.console.print(f"  [legion.node]──▶ {node_name}[/legion.node]")
                            
                            if node_name == "tools":
                                for msg in output.get("messages", []):
                                    if hasattr(msg, "content") and msg.content:
                                        snippet = (msg.content[:100] + '...') if len(msg.content) > 100 else msg.content
                                        self.console.print(f"      [legion.tool]Result:[/legion.tool] {snippet}")
                            
                            elif node_name == "agent":
                                if "messages" in output and output["messages"]:
                                    content = output["messages"][-1].content
                                    if content:
                                        # Handle list of blocks (e.g. thinking block + text block)
                                        if isinstance(content, list):
                                            text_parts = []
                                            for block in content:
                                                if isinstance(block, dict) and "text" in block:
                                                    text_parts.append(block["text"])
                                                elif isinstance(block, dict) and "thinking" in block:
                                                    pass # Skip thinking block in final output
                                            content = "\n".join(text_parts) if text_parts else str(content)
                                        
                                        self.console.print(f"      [legion.reasoning]{content}[/legion.reasoning]")
                                        final_answer = content
                        else:
                            print(f"  Node: {node_name}")
                            if node_name == "agent":
                                if "messages" in output and output["messages"]:
                                    content = output["messages"][-1].content
                                    if content:
                                        if isinstance(content, list):
                                            content = "\n".join(b["text"] for b in content if isinstance(b, dict) and "text" in b) or str(content)
                                        final_answer = content

                if self.console:
                    # Ensure final_answer is a string before rendering in Panel
                    if isinstance(final_answer, list):
                        final_answer = "\n".join(b.get("text", "") for b in final_answer if isinstance(b, dict) and "text" in b) or str(final_answer)
                    elif not isinstance(final_answer, str):
                        final_answer = str(final_answer)
                        
                    self.console.print()
                    self.console.print(Panel(
                        final_answer,
                        title="[legion.success]Sovereign Response[/legion.success]",
                        border_style="bright_blue",
                        padding=(1, 2)
                    ))
                else:
                    print(f"\nANSWER: {final_answer}")

            except ValidationError as ve:
                self._print(f"SCHEMA VALIDATION ERROR: {ve.title}", style="legion.error")
                if self.console:
                    for err in ve.errors():
                        self.console.print(f"  Field: [cyan]{'.'.join(str(x) for x in err['loc'])}[/cyan] | Error: [yellow]{err['msg']}[/yellow]")
                else:
                    for err in ve.errors():
                        print(f"  Field: {'.'.join(str(x) for x in err['loc'])} | Error: {err['msg']}")
            except Exception as e:
                self._print(f"CRITICAL ERROR DURING EXECUTION: {e}", style="legion.error")
                import traceback
                self._print(traceback.format_exc(), style="legion.error")

if __name__ == "__main__":
    cli = LegionInteractiveCLI()
    if not USE_RICH:
        print("Note: Run 'pip install rich' for full capability visualization.")
        
    try:
        asyncio.run(cli.run_session())
    except KeyboardInterrupt:
        # Suppress known Windows ProactorEventLoop exit bug in Python 3.12
        try:
            sys.exit(0)
        except SystemExit:
            pass
