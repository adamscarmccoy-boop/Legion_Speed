import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
os.environ["LOGFIRE_CONFIG_FILE"] = ""

import json
import asyncio
from typing import Any, Dict, Optional, Type

# 1. Consolidated Pydantic & Distributed Compute Imports
import ray
from pydantic import BaseModel, Field, ValidationError

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

#from  langchain_core import HumanMessage

# 2. Local Brain Import
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "antigravity_vscode_ext", "backend"))

try:
    from legion_langgraph_brain import LegionLangGraphAgent
    from langchain_core.messages import HumanMessage
except ImportError as e:
    print(f"❌ CRITICAL: Could not import Legion Brain components: {e}")
    sys.exit(1)

# 3. UI Imports
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.theme import Theme
    USE_RICH = True
except ImportError:
    print("⚠️ 'rich' library not found. Falling back to standard terminal output.")
    USE_RICH = False


# =====================================================================
# INLINE SCHEMAS (Replaces sovereign_schemas.py)
# =====================================================================

class AudioRequest(BaseModel):
    """Schema for audio generation and mastering parameters."""
    target_rms: str = Field(..., description="The target RMS in dB (e.g., '-13.9')")
    crest_factor: float = Field(default=5.69, description="Target crest factor")
    
class DuckDBQuery(BaseModel):
    """Schema for SQL-based metadata queries."""
    sql_query: str = Field(..., description="The exact SQL statement to execute")
    db_version: str = Field(default="v2", description="Which database version to target (v1 or v2)")

class LanceDBQuery(BaseModel):
    """Schema for semantic vector searches."""
    search_text: str = Field(..., description="The semantic vibe or text to search for")
    top_k: int = Field(default=10, description="Number of results to return")


# =====================================================================
# THEME & CLI LOGIC
# =====================================================================

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
        
        # Explicit intent mapping directly to the classes defined above
        self.intent_registry = {
            "audio": AudioRequest,
            "master": AudioRequest,
            "sql": DuckDBQuery,
            "query": DuckDBQuery,
            "vector": LanceDBQuery,
            "vibe": LanceDBQuery
        }

    def _print(self, text: str, style: str = ""):
        if self.console:
            self.console.print(text, style=style)
        else:
            print(text)

    def display_capabilities(self):
        """List available capabilities/options on startup."""
        self._print("\n[bold]Initializing Sovereign Intelligence Interface...[/bold]")
        
        table = Table(title="Legion Intelligence Capabilities", expand=True)
        table.add_column("Capability (Tool)", style="legion.node")
        table.add_column("Description", style="legion.info")
        table.add_column("Data Source", style="legion.tool")

        for tool in self.app.tools:
            name = tool.name
            desc = tool.description.split('\n')[0]
            
            source = "Local/Generic"
            if "duckdb" in desc.lower() or "sql" in name.lower(): source = "DuckDB"
            elif "lancedb" in desc.lower() or "vector" in name.lower(): source = "LanceDB"
            elif "parquet" in desc.lower(): source = "Parquet Lake"

            table.add_row(f"[bold]{name}[/bold]", desc, source)

        if self.console:
            self.console.print(table)
        else:
            print(table)

        self._print("\n[dim]System Status: Connected to Ray Cluster | Protocol: LangGraph[/dim]\n")

    def _check_underspecification(self, user_query: str) -> Optional[Type[BaseModel]]:
        """Intercept queries matching registered intents."""
        query_lower = user_query.lower()
        for keyword, model_class in self.intent_registry.items():
            if keyword in query_lower:
                return model_class
        return None

    async def _intercept_and_prompt(self, user_query: str, model: Type[BaseModel]):
        """Prompt user for missing Pydantic fields before hitting the LLM."""
        self._print(f"\n[legion.reasoning]Sovereign Logic: Query detected as intent '{model.__name__}'.[/legion.reasoning]")
        
        required_fields = model.model_fields
        missing_fields = []
        
        for field_name, field_info in required_fields.items():
            if field_info.is_required() and field_name.lower() not in user_query.lower():
                missing_fields.append(field_name)

        if not missing_fields:
            return True

        self._print(f"[legion.warning]Underspecification Detected. Missing context for {model.__name__}:[/legion.warning]")
        
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
            user_input = Prompt.ask("\n[bold white]LEGION[/bold white] ❯")
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                self._print("[yellow]Closing connection... Goodbye.[/yellow]")
                break

            # 1. Local Schema Interception
            model_to_check = self._check_underspecification(user_input)
            if model_to_check:
                extra_context = await self._intercept_and_prompt(user_input, model_to_check)
                if isinstance(extra_context, str):
                    user_input = f"{user_input} ({extra_context})"

            # 2. Graph Traversal
            self._print("\n[legion.reasoning]Commencing Graph Traversal...[/legion.reasoning]")
            
            try:
                final_answer = "No response generated."
                async for event in self.app.graph.astream(
                    {
                        "messages": [HumanMessage(content=user_input)], 
                        "recursion_count": 0,
                        "max_recursion_limit": 5
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
                                        self.console.print(f"      [legion.reasoning]{content}[/legion.reasoning]")
                                        final_answer = content
                        else:
                            print(f"  Node: {node_name}")
                            if node_name == "agent":
                                if "messages" in output and output["messages"]:
                                    content = output["messages"][-1].content
                                    if content:
                                        final_answer = content

                if self.console:
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
                self._print(f"SCHEMA VALIDATION ERROR:", style="legion.error")
                for err in ve.errors():
                    self._print(f"  Field: {'.'.join(str(x) for x in err['loc'])} | Error: {err['msg']}", style="legion.warning")
            except Exception as e:
                self._print(f"CRITICAL ERROR DURING EXECUTION: {e}", style="legion.error")


if __name__ == "__main__":
    # =====================================================================
    # RAY INITIALIZATION CONFIGURATION (IP OPTIONS)
    # =====================================================================
    
    # OPTION 1: Pure Local Mode (Auto-starts a local session on localhost)
    ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
    
    # OPTION 2: Cross-Network LAN Mode 
    # Uncomment the line below (and comment out Option 1) to connect to a specific 
    # running head node across your network (e.g., if running from an external laptop/device)
    # ray.init(address="ray://192.168.1.50:10001", namespace="legion", ignore_reinit_error=True)

    cli = LegionInteractiveCLI()
    try:
        asyncio.run(cli.run_session())
    except KeyboardInterrupt:
        try:
            ray.shutdown()
            sys.exit(0)
        except SystemExit:
            pass