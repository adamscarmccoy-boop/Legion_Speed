
import sys
import json
import logging
from typing import Dict, Any

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


# ==============================================================================
# FIX 1: Schema Flattener Helper for FastMCP Tool Registration
# ==============================================================================
def flatten_schema_for_lmstudio(schema_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolves $ref and $defs anchors, flattening nested Pydantic models into 
    inline primitive properties compatible with llama.cpp GBNF grammar parsers.
    """
    properties = schema_dict.get("properties", {}).copy()
    required = schema_dict.get("required", []).copy()
    defs = schema_dict.get("$defs", schema_dict.get("definitions", {}))

    flat_props = {}
    for field_name, field_def in properties.items():
        if "type" in field_def:
            flat_props[field_name] = {
                "type": field_def["type"],
                "description": field_def.get("description", "")
            }
        elif "$ref" in field_def:
            ref_path = field_def["$ref"].split("/")[-1]
            ref_def = defs.get(ref_path, {})
            flat_props[field_name] = {
                "type": "object",
                "description": ref_def.get("description", f"Nested {field_name} object"),
                "properties": ref_def.get("properties", {})
            }
        else:
            flat_props[field_name] = {"type": "string", "description": field_def.get("description", "")}

    return {
        "type": "object",
        "properties": flat_props,
        "required": required
    }

# ==============================================================================
# FIX 2: Logging Setup for mcp_api_server.py & mcp_rag_server.py
# ==============================================================================
def configure_clean_mcp_logging():
    """
    Mutes low-level FastMCP debug chatter on sys.stderr so LM Studio
    console does not mark benign handshakes as [ERROR].
    """
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    logging.getLogger("mcp").setLevel(logging.WARNING)
    logging.getLogger("mcp.server.lowlevel.server").setLevel(logging.WARNING)
    print("✅ MCP Logging configured cleanly (stderr noise suppressed).", file=sys.stderr)

if __name__ == "__main__":
    configure_clean_mcp_logging()
    
    # Test Schema Flattening
    dummy_pydantic_schema = {
        "title": "LanceDBQuery",
        "type": "object",
        "properties": {
            "query": {"title": "Query", "type": "string", "description": "Search query term"},
            "limit": {"title": "Limit", "type": "integer", "default": 5}
        },
        "required": ["query"]
    }
    
    flattened = flatten_schema_for_lmstudio(dummy_pydantic_schema)
    print("\n--- Verified Flattened Schema for LM Studio GBNF ---")
    print(json.dumps(flattened, indent=2))
