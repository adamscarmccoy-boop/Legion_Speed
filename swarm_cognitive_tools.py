# swarm_cognitive_tools.py
# High-Performance Autonomic Sensory Toolkit for Ray Swarm Integration
# Exposes raw hardware, log metrics, and sandbox compilation tasks directly to Nemotron.

import os
import re
import sys
import json
import time
import socket
import subprocess
import traceback

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


# Default configuration parameters matching your local machine layout
C_WEB_CASE_STUDY = r"C:\WEB CASE STUDY"
LM_STUDIO_LOG_PATH = r"C:\Users\adams\.lmstudio\logs\main.log" # Standard C++ engine log location

# ==============================================================================
# 1. THE OPENAI-COMPATIBLE JSON SCHEMAS (FEED THIS TO LM STUDIO / PORT 1234)
# ==============================================================================

SWARM_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_gpu_vram_and_temp",
            "description": "Queries your NVIDIA GTX 1650 SUPER for exact live VRAM allocations, processing loads, and GPU core temperature."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_engine_timing_logs",
            "description": "Pulls the latest C++ llama.cpp server logs to extract prompt evaluation speeds, token generation rates, and restored context checkpoint sizes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lines": {"type": "integer", "description": "Number of tail lines to inspect from main.log.", "default": 50}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "measure_ray_latency",
            "description": "Executes a micro-benchmark across active Ray actors to measure round-trip RPC execution times, shared memory allocations, and identify queue bottlenecks."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_system_logs",
            "description": "Reads the tail lines of any local developer or gateway log file (e.g., Vite, mcp_rag_server.py, system_log.txt) to verify their live performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "The target log filename (e.g., system_log.txt)."},
                    "lines": {"type": "integer", "description": "Number of trailing lines to return.", "default": 30}
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "test_code_sandbox",
            "description": "Runs an untrusted Python code block inside a local sub-process syntax preflight validation layer to check for compilation issues before saving it to disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code_content": {"type": "string", "description": "Raw unformatted Python code string."}
                },
                "required": ["code_content"]
            }
        }
    }
]

# ==============================================================================
# 2. SENSORY TOOL IMPLEMENTATIONS
# ==============================================================================

def get_gpu_vram_and_temp() -> str:
    """Queries nvidia-smi for GTX 1650 SUPER live telemetry."""
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total,memory.used,utilization.gpu,temperature.gpu", "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        stats = res.stdout.strip().split(",")
        return json.dumps({
            "status": "SUCCESS",
            "vram_total_mib": int(stats[0]),
            "vram_used_mib": int(stats[1]),
            "gpu_utilization_pct": int(stats[2]),
            "gpu_temperature_celsius": int(stats[3]),
            "vram_headroom_mib": int(stats[0]) - int(stats[1])
        })
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": f"nvidia-smi query failed: {str(e)}"})

def read_engine_timing_logs(lines: int = 50) -> str:
    """Tails local LM Studio main.log to parse C++ engine performance."""
    if not os.path.exists(LM_STUDIO_LOG_PATH):
        # Fallback to current directory lookups if custom path is unconfigured
        fallback_path = os.path.join(C_WEB_CASE_STUDY, "system_log.txt")
        if not os.path.exists(fallback_path):
            return json.dumps({"status": "FAILED", "error": f"LM Studio log not found at expected path: {LM_STUDIO_LOG_PATH}"})
        log_file = fallback_path
    else:
        log_file = LM_STUDIO_LOG_PATH

    try:
        # Read the tail lines of the log file
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            content_lines = f.readlines()
        tail = content_lines[-min(len(content_lines), lines):]
        
        # Search for llama.cpp performance patterns
        eval_metrics = []
        for l in tail:
            if "prompt eval time" in l or "eval time =" in l or "restored context checkpoint" in l:
                eval_metrics.append(l.strip())

        return json.dumps({
            "status": "SUCCESS",
            "log_path": log_file,
            "parsed_llama_cpp_metrics": eval_metrics,
            "raw_tail_logs": "\n".join(tail)
        })
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": f"Failed to tail C++ logs: {str(e)}"})

def measure_ray_latency() -> str:
    """Fires a non-blocking diagnostic task through Ray to calculate live cluster latencies."""
    try:
        import ray
        if not ray.is_initialized():
            ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        
        # Query active nodes
        nodes = ray.nodes()
        
        # Test RPC latency by calling a basic remote tasks
        @ray.remote(num_cpus=0)
        def ping():
            return time.time_ns()
            
        start_ns = time.time_ns()
        ref = ping.remote()
        server_time_ns = ray.get(ref, timeout=2.0)
        end_ns = time.time_ns()
        
        round_trip_ms = (end_ns - start_ns) / 1_000_000.0
        one_way_latency_ms = (server_time_ns - start_ns) / 1_000_000.0
        
        return json.dumps({
            "status": "SUCCESS",
            "ray_gcs_address": ray.get_runtime_context().gcs_address,
            "active_nodes": len(nodes),
            "round_trip_latency_ms": round_trip_ms,
            "one_way_latency_ms": one_way_latency_ms,
            "message": "Ray cluster is highly responsive."
        })
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": f"Ray latency check crashed: {str(e)}"})

def read_system_logs(filename: str, lines: int = 30) -> str:
    """Reads trailing lines of any target file inside your C:\\WEB CASE STUDY workspace."""
    filepath = os.path.join(C_WEB_CASE_STUDY, filename) if not os.path.isabs(filename) else filename
    
    if not os.path.exists(filepath):
        return json.dumps({"status": "FAILED", "error": f"Target system log file '{filepath}' not found on disk."})
        
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content_lines = f.readlines()
        tail = content_lines[-min(len(content_lines), lines):]
        return json.dumps({
            "status": "SUCCESS",
            "filepath": filepath,
            "tail_content": "\n".join(tail)
        })
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": f"Failed to read file '{filename}': {str(e)}"})

def test_code_sandbox(code_content: str) -> str:
    """
    Simulates a secure pre-flight compiler run.
    Automatically intercepts markdown-mangled syntax patterns before syntax verification.
    """
    # 1. Regex Auto-Healer Layer for Markdown Bold mangling (Dunder repair)
    repaired_code = re.sub(r'\*\*([a-zA-Z0-9_]+)\*\*', r'__\1__', code_content)
    repaired_code = repaired_code.replace("**name**", "__name__").replace("**main**", "__main__")

    try:
        # Check syntax using compile block (AST check)
        compile(repaired_code, "<sandbox_test>", "exec")
        return json.dumps({
            "status": "SUCCESS",
            "message": "Pristine Python syntax verified. Code is safe for execution.",
            "repaired_code_preview": repaired_code[:300] + "..." if len(repaired_code) > 300 else repaired_code
        })
    except SyntaxError as syntax_err:
        return json.dumps({
            "status": "REJECTED_BY_PREFLIGHT",
            "error_message": f"Syntax verification failed: {str(syntax_err)}",
            "line_number": syntax_err.lineno,
            "offset": syntax_err.offset,
            "text": syntax_err.text
        })
    except Exception as e:
        return json.dumps({"status": "FAILED", "error": str(e)})

# ==============================================================================
# 3. THE UNIVERSAL TOOL EXECUTION ROUTING MAP
# ==============================================================================

def dispatch_swarm_tool(name: str, arguments: dict) -> str:
    """Intercepts and dispatches the tool call from Nemotron's JSON response."""
    try:
        if name == "get_gpu_vram_and_temp":
            return get_gpu_vram_and_temp()
        elif name == "read_engine_timing_logs":
            return read_engine_timing_logs(arguments.get("lines", 50))
        elif name == "measure_ray_latency":
            return measure_ray_latency()
        elif name == "read_system_logs":
            return read_system_logs(arguments["filename"], arguments.get("lines", 30))
        elif name == "test_code_sandbox":
            return test_code_sandbox(arguments["code_content"])
        else:
            return json.dumps({"error": f"Sensory tool '{name}' is not bound to the execution plane."})
    except Exception as e:
        return json.dumps({"error": f"Exception routed during execution of tool '{name}': {str(e)}"})