import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import ray

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


# This server exposes your Ray Swarm over a local HTTP API
# so that the VS Code extension (or any web front-end) can talk to it.

app = FastAPI()

# Allow requests from the VS Code webview extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    """Connect to Ray on server startup."""

    if not ray.is_initialized():
        print("Connecting to Ray cluster (namespace: legion)...")
        ray.init(namespace="legion", ignore_reinit_error=True, address="auto")
    print("FastAPI server started, connected to Ray.")

@app.get("/tables")
def list_swarm_tables():
    """Lists all tables currently registered in the SwarmKnowledgeRegistry."""
    try:
        registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
        summary = ray.get(registry.get_registered_tables_summary.remote())
        return {"tables": sorted(summary.keys())}
    except ValueError:
        raise HTTPException(status_code=404, detail="SwarmKnowledgeRegistry actor not found. Is the swarm running?")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to swarm: {e}")

@app.get("/query/{table_name}")
def query_swarm_table(table_name: str, limit: int = 20):
    """Queries a table in the SwarmKnowledgeRegistry and returns N rows."""
    try:
        registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
        table_ref = registry.get_table.remote(table_name)
        table = ray.get(table_ref)

        if table is None:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found in swarm.")

        # Convert the first N rows of the PyArrow table to a JSON-friendly format
        df = table.to_pandas().head(limit)
        return df.to_dict(orient='records')

    except ValueError:
        raise HTTPException(status_code=404, detail="SwarmKnowledgeRegistry actor not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying swarm: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8010)