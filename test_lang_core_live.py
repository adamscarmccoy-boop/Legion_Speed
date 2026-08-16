import os
import sys
import time
import socket
import ctypes
import requests
import json

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

HOST = "127.0.0.1"
CANDIDATE_PORTS = [1234, 1235, 1236, 1237, 1010, 8080, 8081, 11434]
SYSTEM_PROMPT = """You are the Legion Sovereign Intelligence — the cognitive router for a Tech House audio production pipeline. You have access to tools that query DuckDB databases, analyze Parquet data exports, and search LanceDB vector stores containing 384-dim, 768-dim, and 1024-dim audio embeddings.

Your producer's DNA signature: dominant tempo 128 BPM, dominant key G major, target RMS -13.9 LUFS, crest factor 5.69, mid-injection multiplier x289.34. Lineage: MPC/SP1200.
Always be precise with numbers. Reference the Sovereign Targets when relevant."""

def discover_live_port():
    print("🔍 [DISCOVERY] Probing candidate ports for live LM Studio kernel...")
    for port in CANDIDATE_PORTS:
        try:
            r = requests.get(f"http://{HOST}:{port}/v1/models", timeout=1.0)
            if r.status_code == 200:
                data = r.json()
                models = [m["id"] for m in data.get("data", [])]
                print(f"✨ [DISCOVERY] FOUND active kernel on Port {port} with {len(models)} models loaded!")
                for m in models:
                    print(f"    - {m}")
                return port, models
        except Exception:
            pass
    print("⚠️ [DISCOVERY] No candidate port responded. Defaulting to 1234.")
    return 1234, []

def test_native_dll():
    dll_path = r"C:\Users\adams\Downloads\lance_duckdb_core.dll"
    if os.path.exists(dll_path):
        try:
            core = ctypes.CDLL(dll_path)
            print(f"⚡ [NATIVE DLL] Loaded '{dll_path}' into memory (Handle: {core._handle})")
            return True
        except Exception as e:
            print(f"❌ [NATIVE DLL] Failed to load DLL: {e}")
            return False
    else:
        print(f"⚠️ [NATIVE DLL] File not found at {dll_path}")
        return False

def run_lang_core():
    print("=" * 65)
    print("LEGION STATE MACHINE — OPENAI REST + DYNAMIC KERNEL TEST")
    print("=" * 65)

    # 1. Native DLL verification
    test_native_dll()

    # 2. Port discovery
    port, models = discover_live_port()
    base_url = f"http://{HOST}:{port}/v1"

    # 3. Select chat model
    chat_model = "nvidia/nemotron-3-nano-4b"
    if models and not any(chat_model in m for m in models):
        # Pick the first available chat model if nemotron is not exact match
        for m in models:
            if "embed" not in m:
                chat_model = m
                break
    print(f"\n📡 [ROUTER] Selected Chat Model: {chat_model}")

    # 4. State Machine Turn Execution
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "What files and tables are currently in our Tech House database?"}
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "list_available_data",
                "description": "Lists all active files, DuckDB tables, and LanceDB stores."
            }
        },
        {
            "type": "function",
            "function": {
                "name": "query_sonic_core",
                "description": "Executes standard SQL queries against our DuckDB Analytical Store.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql_query": {"type": "string", "description": "SQL query string."}
                    },
                    "required": ["sql_query"]
                }
            }
        }
    ]

    payload = {
        "model": chat_model,
        "messages": messages,
        "temperature": 0.0,
        "tools": tools
    }

    print("\n🚀 [STATE MACHINE] Dispatching turn to LM Studio REST endpoint...")
    t0 = time.time()
    try:
        resp = requests.post(f"{base_url}/chat/completions", json=payload, timeout=30)
        dt = (time.time() - t0) * 1000
        print(f"📥 [RESPONSE] HTTP {resp.status_code} received in {dt:.2f}ms")
        
        if resp.status_code == 200:
            result = resp.json()
            choice = result["choices"][0]
            msg = choice["message"]
            
            if "tool_calls" in msg and msg["tool_calls"]:
                print(f"⚡ [ROUTING EDGE] Tool Call Generated: {len(msg['tool_calls'])} calls")
                for tc in msg["tool_calls"]:
                    fn = tc.get("function", {})
                    print(f"   ▶ Function : {fn.get('name')}")
                    print(f"   ▶ Arguments: {fn.get('arguments')}")
            else:
                print(f"\n💬 [ASSISTANT ANSWER]:\n{msg.get('content')}")
        else:
            print(f"❌ [ERROR] Response: {resp.text}")
    except Exception as e:
        print(f"❌ [EXCEPTION] Connection failed: {e}")

    # 5. Verify Dual Embedding Endpoints
    print("\n" + "=" * 65)
    print("🧬 DUAL EMBEDDING VERIFICATION")
    print("=" * 65)
    for model_name, expected_dim in [
        ("text-embedding-snowflake-arctic-embed-l-v2.0", 1024),
        ("text-embedding-nomic-embed-text-v1.5", 768)
    ]:
        try:
            er = requests.post(
                f"{base_url}/embeddings",
                json={"input": "Tech house kick transient analysis", "model": model_name},
                timeout=10
            )
            if er.status_code == 200:
                dim = len(er.json()["data"][0]["embedding"])
                status = "✅ PASS" if dim == expected_dim else f"⚠️ MISMATCH (got {dim})"
                print(f"  {status} | {model_name} -> {dim}-D")
            else:
                print(f"  ❌ FAIL | {model_name} -> HTTP {er.status_code}: {er.text[:80]}")
        except Exception as e:
            print(f"  ❌ FAIL | {model_name} -> {e}")

if __name__ == "__main__":
    run_lang_core()
