
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


if __name__ == "__main__":
    mcp.run()

# ── Ray Swarm Bridge ──────────────────────────────────────────────────────────
# These tools let any AI assistant talk to the live Ray SwarmKnowledgeRegistry.
# Without this bridge, Ray actors are locked behind ray.get() Python calls.
@mcp.tool()
def list_swarm_tables() -> str:
    """Lists all tables currently registered in the live Ray SwarmKnowledgeRegistry."""
    try:
        import ray
        if not ray.is_initialized():
            ray.init(namespace="legion", ignore_reinit_error=True, address="auto")
        registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
        summary = ray.get(registry.get_registered_tables_summary.remote())
        if not summary:
            return "No tables registered. Run ray_arrow_swarm.py first."
        lines = [f"Swarm Registry: {len(summary)} tables"]
        for name, info in sorted(summary.items()):
            c = info.get("columns", info.get("cols", []))[:6]
            lines.append(f"  {name}  ({info.get('rows', info.get('num_rows', '?'))} rows)  [{', '.join(c)}]")
        return "\n".join(lines)
    except ValueError:
        return "SwarmKnowledgeRegistry not found. Run ray_arrow_swarm.py first."
    except Exception as e:
        return f"Error connecting to swarm: {e}"
@mcp.tool()
def query_swarm(table_name: str, search: str = "", limit: int = 10) -> str:
    """Queries a table in the live Ray SwarmKnowledgeRegistry."""
    try:
        import ray
        if not ray.is_initialized():
            ray.init(namespace="legion", ignore_reinit_error=True, address="auto")
        registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
        try:
            result = ray.get(registry.query_table.remote(table_name, search if search else None))
        except AttributeError:
            tbl = ray.get(registry.get_table.remote(table_name))
            if tbl is None:
                return f"Table '{table_name}' not found."
                limit = min(limit, 50)
            results = []
            for r in range(min(tbl.num_rows, limit)):
                row = {}
                for c in tbl.schema.names:
                    val = tbl.column(c)[r].as_py()
                    if isinstance(val, str):
                        if not search or search.lower() in val.lower():
                            row[c] = val[:200]
                    else:
                        row[c] = str(val)[:200]
                if row:
                    results.append(row)
            if search and not results:
                return f"No rows in '{table_name}' match '{search}'."
            return json.dumps(results[:limit], indent=2)
        if isinstance(result, str):
            return result
        if isinstance(result, list):
            if not result:
                return f"No matching rows in '{table_name}'."
            return json.dumps(result[:limit], indent=2)
        return str(result)
    except ValueError:
        return "SwarmKnowledgeRegistry not found. Run ray_arrow_swarm.py first."
    except Exception as e:
        return f"Error querying swarm: {e}"
@mcp.tool()
def start_swarm() -> str:
    """Starts the Ray-Arrow JSON ingestion swarm in the background."""
    import subprocess, threading
    swarm_script = r"C:\\WEB CASE STUDY\\ray_arrow_swarm.py"
    if not os.path.exists(swarm_script):
        return f"Swarm script not found at {swarm_script}"
    def _run():
        env = os.environ.copy()
        env["PYTHONPATH"] = r"C:\\WEB CASE STUDY"
        subprocess.Popen([sys.executable, swarm_script], cwd=r"C:\\WEB CASE STUDY", env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    threading.Thread(target=_run, daemon=True).start()
    return "Swarm starting in background (~3-5s). Run list_swarm_tables() in a moment to check."
if __name__ == "__main__":
    mcp.run()