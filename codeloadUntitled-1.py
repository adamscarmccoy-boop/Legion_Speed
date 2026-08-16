# --------------------------------------------------------------
# 1️⃣  Imports – keep everything you need in one place
# --------------------------------------------------------------
import os, sys
import ray
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

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
    # Avoid raising SystemExit inside an atexit callback (which causes RuntimeWarnings)
    if args and isinstance(args[0], int):
        sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


# Keep the Ray cluster alive (auto‑join) so the function can be
# imported before any other code that uses `registry`.
if not ray.is_initialized():
    # LEGION namespace is already configured by your system.
    ray.init(address="auto", namespace="legion", ignore_reinit_error=True)

# --------------------------------------------------------------
# 2️⃣  Helper to read a parquet audit file into an Arrow table
# --------------------------------------------------------------
def load_audit_table() -> pa.Table | None:
    """Read `code_knowledge_audit.parquet` (or any similar) and return
       a pyarrow Table. Returns None if the file does not exist."""
    aud_file = Path(r"C:\WEB CASE STUDY\code_knowledge_audit.parquet")
    if not aud_file.is_file():
        print(f"⚠️  Audit file not found: {aud_file}")
        return None

    table = pq.read_table(str(aud_file))
    print(f"✅ Loaded audit parquet ({table.num_rows} rows)")
    return table


# --------------------------------------------------------------
# 3️⃣  The *real* load routine – writes the tables into Swarm
# --------------------------------------------------------------
def load_swarm_registry(sweep_table: pa.Table | None = None) -> dict:
    """
    Registers every Arrow table that has >0 rows into the CodeSwarmKnowledgeRegistry.
    Returns a Python ``dict`` with the same structure as
    ``registry.registry`` (useful for logging).

    Parameters
    ----------
    sweep_table : pyarrow.Table | None
        Optional – if you already have an Arrow table built elsewhere,
        pass it to skip the parquet‑read step.
    
    Returns
    -------
    dict
        The current key/value snapshot of ``registry.registry``.
    """
    # Resolve the actor reference once (cheap)
    registry = ray.get_actor("CodeSwarmKnowledgeRegistry", namespace="legion")

    # If you already have a table in memory, use it; otherwise read it.
    tbl = sweep_table or load_audit_table()

    if tbl is None:
        return {}

    # Register (or re‑register) the table – Ray will overwrite any existing entry
    registry.register_table("code_audit", tbl)
    print(f"📦 Registered table 'code_audit' ({tbl.num_rows} rows)")

    # Verify that it really made it into the actor state
    current = dict(registry.registry)   # same as get_all_tables()
    assert "code_audit" in current, "Table was not stored – check for NameError"
    return current


# --------------------------------------------------------------
# 4️⃣  Call‑site usage (you can call this from a script or unit test)
# --------------------------------------------------------------
if __name__ == "__main__":
    # Example: load the audit parquet → register → see what’s in memory
    loaded = load_swarm_registry()
    print("\n=== All tables now present in Swarm ===")
    for k, v in loaded.items():
        print(f"  {k}: {v.num_rows} rows")

    # (Optional) test that you can read it later:
    # table = ray.get(registry.get_table.remote("code_audit"))