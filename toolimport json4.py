import os
import json
import time
import ray
import pydantic_monty as monty
from openai import OpenAI

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


# -------------------------------------------------------------------
# 1. INITIALIZE INFRASTRUCTURE
# -------------------------------------------------------------------
if not ray.is_initialized():
    ray.init(address="auto", namespace="legion", ignore_reinit_error=True)

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

LLM_MODEL = "nvidia/nemotron-3-nano-4b"
MAX_PREFLIGHT_RETRIES = 3

print("=" * 80)
print("🛡️ SELF-HEALING PRE-FLIGHT PIPELINE (Max 3 Tries)")
print("=" * 80)

# -------------------------------------------------------------------
# 2. LOCAL TOOLS & PRE-FLIGHT VALIDATOR
# -------------------------------------------------------------------
def get_live_acp_state() -> str:
    """Inspects active Ray actors in the cluster."""
    try:
        named_actors = ray.util.list_named_actors(all_namespaces=True)
        acp_actors = [a for a in named_actors if "ACP" in a["name"] or "ControlPlane" in a["name"]]
        return json.dumps({"status": "SUCCESS", "existing_actors": acp_actors, "namespace": "legion"})
    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})

def run_preflight_check(code_content: str) -> dict:
    """
    Executes generated code in a zero-capability Rust sandbox.
    Intercepts bad imports, invalid class inheritances, or syntax errors.
    """
    print("🔍 [PRE-FLIGHT]: Running isolated AST/VM evaluation via Pydantic-Monty...")
    start_t = time.perf_counter()
    
    try:
        # Correct initialization for Monty AST parse/eval
        # Parse inputs into sandbox AST frame
        interpreter = monty.Monty()
        
        # Dry-run evaluation in-process
        res = interpreter.eval(code_content)
        
        elapsed_us = (time.perf_counter() - start_t) * 1_000_000
        print(f"✅ [PRE-FLIGHT PASSED]: Verified in {elapsed_us:.2f}μs (Zero-trust verified)")
        return {"valid": True, "output": str(res)}

    except Exception as exc:
        elapsed_us = (time.perf_counter() - start_t) * 1_000_000
        print(f"❌ [PRE-FLIGHT REJECTED]: AST/Execution error in {elapsed_us:.2f}μs!")
        print(f"   Reason: {exc}")
        return {"valid": False, "error": str(exc)}

def write_code_file(filename: str, content: str) -> str:
    """
    Gatekeeper function: Executes pre-flight validation BEFORE writing to disk.
    If pre-flight fails, it rejects the write and feeds the error back to LLM.
    """
    # 1. Pre-flight check via Sandboxed VM
    validation = run_preflight_check(content)
    
    if not validation["valid"]:
        # Reject file creation and force LLM self-healing feedback loop
        return json.dumps({
            "status": "REJECTED_BY_PREFLIGHT",
            "error_message": f"Pre-flight rejection: {validation['error']}. Please fix syntax, remove hallucinated imports/classes, and call write_code_file again."
        })

    # 2. Write file safely to workspace upon 100% verification pass
    try:
        target_path = os.path.join(os.getcwd(), filename)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return json.dumps({
            "status": "SUCCESS", 
            "path": target_path, 
            "bytes_written": len(content),
            "preflight": "PASSED"
        })
    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})

# -------------------------------------------------------------------
# 3. TOOL MAP & SCHEMAS FOR OPENAI / NEMOTRON
# -------------------------------------------------------------------
TOOL_MAP = {
    "get_live_acp_state": get_live_acp_state,
    "write_code_file": write_code_file
}

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_live_acp_state",
            "description": "Queries the live Ray cluster for existing active ACP control actors.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_code_file",
            "description": "Evaluates Python code via pre-flight VM and writes it to workspace if valid.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Target filename (e.g. apply_acp_daemon.py)"},
                    "content": {"type": "string", "description": "Complete Python script content."}
                },
                "required": ["filename", "content"]
            }
        }
    }
]

# -------------------------------------------------------------------
# 4. AGENTIC EXECUTION LOOP WITH PRE-FLIGHT RECOVERY
# -------------------------------------------------------------------
prompt = """
1. Inspect live cluster state using `get_live_acp_state`.
2. Generate valid Python code for a detached background Ray actor (`ACPDaemonWorker`) using standard `@ray.remote` class decorators.
3. Call `write_code_file` with filename 'apply_acp_daemon.py' and your code content.
"""

messages = [{"role": "user", "content": prompt}]

print("\n📡 Starting Agent Loop...")

for attempt in range(1, MAX_PREFLIGHT_RETRIES + 1):
    print(f"\n🔄 --- AGENT PASS {attempt} OF {MAX_PREFLIGHT_RETRIES} ---")
    
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        tools=tools_schema,
        tool_choice="auto",
        temperature=0.1
    )

    msg = response.choices[0].message
    messages.append(msg)

    # Check if Nemotron triggered any tool calls
    if msg.tool_calls:
        file_written_successfully = False
        
        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)
            print(f"🎯 [TOOL EXECUTED]: {fn_name}()")
            
            if fn_name in TOOL_MAP:
                result_str = TOOL_MAP[fn_name](**fn_args)
                print(f"⚡ [RESULT]: {result_str}")
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_str
                })
                
                # Check if write_code_file passed pre-flight and succeeded
                if fn_name == "write_code_file":
                    res_json = json.loads(result_str)
                    if res_json.get("status") == "SUCCESS":
                        file_written_successfully = True

        # Exit early if file was successfully verified and saved
        if file_written_successfully:
            print("\n🎉 SUCCESS: Code passed pre-flight validation and was written to disk!")
            break
    else:
        # If Nemotron responded with text instead of a tool call
        print(f"💬 [NEMOTRON]: {msg.content}")
        if "apply_acp_daemon.py" in str(msg.content):
            break

print("\n" + "=" * 80)
print("🏁 PIPELINE EXECUTION COMPLETE")
print("=" * 80)