"""
SOVEREIGN LANGGRAPH — LIVE LM STUDIO REST TEST
================================================
Tests the full ReAct LangGraph agent via LM Studio at http://127.0.0.1:1234/v1
Validates: LM Studio alive → Model loaded → Tool binding → Graph execution → LangSmith trace
"""

import os
import sys
import json
import urllib.request
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LM_BASE = "http://127.0.0.1:1234/v1"

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: Check LM Studio is alive + what model is loaded
# ─────────────────────────────────────────────────────────────────────────────
def check_lmstudio():
    print("\n" + "="*70)
    print("🔌 STEP 1 — LM Studio REST Health Check")
    print("="*70)
    try:
        req = urllib.request.Request(f"{LM_BASE}/models")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        models = data.get("data", [])
        if not models:
            print("❌ LM Studio is running but NO model is loaded. Load a model first.")
            return None
        model_id = models[0]["id"]
        print(f"✅ LM Studio alive. Loaded model: {model_id}")
        for m in models:
            print(f"   • {m['id']}")
        return model_id
    except Exception as e:
        print(f"❌ Cannot reach LM Studio at {LM_BASE}: {e}")
        print("   → Make sure LM Studio is running with 'Start Local Server' enabled.")
        return None

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: Bare REST call to verify the LLM responds
# ─────────────────────────────────────────────────────────────────────────────
def bare_rest_call(model_id: str):
    print("\n" + "="*70)
    print("💬 STEP 2 — Bare REST Chat Completion")
    print("="*70)
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": "You are the Sovereign Audio Intelligence. Reply with exactly one sentence."},
            {"role": "user",   "content": "How many DuckDB records does this system have?"}
        ],
        "temperature": 0.0,
        "max_tokens": 128
    }
    try:
        req = urllib.request.Request(
            f"{LM_BASE}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}
        )
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        latency = (time.perf_counter() - t0) * 1000
        content = data["choices"][0]["message"]["content"]
        tokens  = data.get("usage", {})
        print(f"✅ Response ({latency:.0f}ms): {content}")
        print(f"   Tokens → prompt:{tokens.get('prompt_tokens','?')} completion:{tokens.get('completion_tokens','?')}")
        return True
    except Exception as e:
        print(f"❌ REST call failed: {e}")
        return False

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: Full LangGraph ReAct agent via LM Studio
# ─────────────────────────────────────────────────────────────────────────────
def run_langgraph(model_id: str):
    print("\n" + "="*70)
    print("⚡ STEP 3 — LangGraph ReAct Agent via LM Studio")
    print("="*70)

    # Load .env for LangSmith
    try:
        from dotenv import load_dotenv
        load_dotenv(r"C:\WEB CASE STUDY\.env")
        print(f"📡 LangSmith Project: {os.environ.get('LANGSMITH_PROJECT','legion-starter')}")
    except Exception:
        pass

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage
        try:
            from langchain.agents import create_react_agent  # LangGraph V1.0+
        except ImportError:
            from langgraph.prebuilt import create_react_agent  # fallback
        from langchain_core.tools import tool
        import duckdb, json

        # ── TOOLS ──────────────────────────────────────────────────────────
        @tool
        def query_duckdb_totals() -> str:
            """Returns total record counts across all DuckDB tables and parquet files in the Sovereign system."""
            TARGET = r"C:\WEB CASE STUDY"
            results = {}
            try:
                db_path = os.path.join(TARGET, "web_intel_sonicdb.duckdb")
                con = duckdb.connect(db_path, read_only=True)
                tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
                total = 0
                for t in tables:
                    cnt = con.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
                    results[t] = cnt
                    total += cnt
                con.close()
                results["__TOTAL_ROWS__"] = total

                # Add ray_categories parquet
                cat_path = os.path.join(TARGET, "ray_categories.parquet")
                if os.path.exists(cat_path):
                    cnt2 = duckdb.execute(f"SELECT count(*) FROM read_parquet('{cat_path}')").fetchone()[0]
                    results["ray_categories.parquet"] = cnt2

                return json.dumps(results, indent=2)
            except Exception as e:
                return f"Error: {e}"

        @tool
        def get_onnx_models() -> str:
            """Lists all compiled ONNX neural models in the Sovereign system with their sizes."""
            TARGET = r"C:\WEB CASE STUDY"
            import glob
            models = []
            for f in glob.glob(os.path.join(TARGET, "**/*.onnx"), recursive=True):
                sz = os.path.getsize(f)
                data_f = f + ".data"
                if os.path.exists(data_f):
                    sz += os.path.getsize(data_f)
                models.append({"model": os.path.basename(f), "total_size_kb": round(sz/1024, 1)})
            return json.dumps(models, indent=2)

        @tool
        def get_native_cpp_modules() -> str:
            """Lists all compiled C++ native modules (.dll, .so, .lib) in the AOT engine directory."""
            AOT = r"C:\WEB CASE STUDY\AOT"
            ROOT = r"C:\WEB CASE STUDY"
            files = []
            for d in [AOT, ROOT]:
                for f in os.listdir(d):
                    if f.endswith(('.dll', '.so', '.lib', '.exp')):
                        path = os.path.join(d, f)
                        files.append({"file": f, "dir": d, "size_kb": round(os.path.getsize(path)/1024, 1)})
            return json.dumps(files, indent=2)

        TOOLS = [query_duckdb_totals, get_onnx_models, get_native_cpp_modules]

        # ── AGENT ──────────────────────────────────────────────────────────
        llm = ChatOpenAI(
            base_url=f"{LM_BASE}",
            api_key="not-needed",
            model=model_id,
            temperature=0.0,
        )

        agent = create_react_agent(llm, TOOLS)

        query = (
            "Use your tools to: "
            "1) Get total DuckDB record counts across all tables "
            "2) List all ONNX models "
            "3) List all native C++ modules (.dll/.so). "
            "Then summarize the total data points in this Sovereign system."
        )

        print(f"\n🤖 Invoking agent with query:\n   {query}\n")
        t0 = time.perf_counter()
        result = agent.invoke({"messages": [HumanMessage(content=query)]})
        elapsed = time.perf_counter() - t0

        final_msg = result["messages"][-1].content
        all_msgs  = result["messages"]

        print(f"\n✅ Agent completed in {elapsed:.2f}s | {len(all_msgs)} messages in graph")
        print("\n" + "─"*70)
        print("🤖 LANGGRAPH FINAL ANSWER:")
        print("─"*70)
        print(final_msg)
        print("─"*70)

        # Show tool calls made
        print("\n📊 TOOL CALLS MADE:")
        for msg in all_msgs:
            mtype = type(msg).__name__
            if "ToolMessage" in mtype or hasattr(msg, "name"):
                name = getattr(msg, "name", "?")
                content = getattr(msg, "content", "")
                print(f"   🔧 {name}: {str(content)[:120]}...")
        return True

    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("   Run: pip install langchain-openai langgraph langchain-core")
        return False
    except Exception as e:
        print(f"❌ LangGraph error: {e}")
        import traceback
        traceback.print_exc()
        return False

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║   SOVEREIGN LANGGRAPH + LM STUDIO REST — FULL VALIDATION TEST   ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    model_id = check_lmstudio()
    if not model_id:
        sys.exit(1)

    ok = bare_rest_call(model_id)
    if not ok:
        sys.exit(1)

    run_langgraph(model_id)
