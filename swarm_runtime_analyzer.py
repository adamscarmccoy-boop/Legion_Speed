# swarm_runtime_analyzer.py
# High-Performance Swarm Port, Sockets, and Process Telemetry Analyzer
# Collects live running services, maps them to environment variables, and returns a clean Markdown status table.

import socket
import json
import os
import sys
import subprocess

# Define the target mapping of core services, ports, and category tags
TARGET_SERVICES = {
    "LM_STUDIO": {
        "port": 1234,
        "name": "LM Studio (C++ Inference Engine)",
        "desc": "Serves Nemotron SSM & LLM chat completions",
        "env_var": "LM_STUDIO_URL",
        "env_val": "http://127.0.0.1:1234/v1"
    },
    "RAY_GCS": {
        "port": 6379,
        "name": "Ray GCS (Redis Broker)",
        "desc": "Cluster metadata broker and orchestration database",
        "env_var": "RAY_ADDRESS",
        "env_val": "ray://127.0.0.1:6379"
    },
    "RAY_DASHBOARD": {
        "port": 8265,
        "name": "Ray Web Dashboard",
        "desc": "Web-based metrics and task visualizer",
        "env_var": "RAY_DASHBOARD_URL",
        "env_val": "http://127.0.0.1:8265"
    },
    "MCP_SWARM": {
        "port": 8001,
        "name": "MCP Swarm/API Gateway",
        "desc": "Unified interface for Cohesive Swarm coordination",
        "env_var": "MCP_SWARM_URL",
        "env_val": "http://127.0.0.1:8001"
    },
    "MCP_RAG_SSE": {
        "port": 8005,
        "name": "MCP RAG SSE Server",
        "desc": "Server-Sent Events vector database interface (rag-v1)",
        "env_var": "MCP_RAG_SSE_URL",
        "env_val": "http://127.0.0.1:8005"
    },
    "NPM_VITE_FRONTEND": {
        "port": 5173,
        "name": "NPM Dev Server (Vite)",
        "desc": "Visual Playground & Sound Engineering dashboard UI",
        "env_var": "NPM_VITE_URL",
        "env_val": "http://127.0.0.1:5173"
    },
    "NPM_NEXT_FRONTEND": {
        "port": 3000,
        "name": "NPM Dev Server (Next.js)",
        "desc": "Alternative frontend UI dashboard layer",
        "env_var": "NPM_NEXT_URL",
        "env_val": "http://127.0.0.1:3000"
    }
}

def ping_port(host: str, port: int) -> bool:
    """Safely pings a local TCP socket to check if it's listening."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            s.connect((host, port))
        return True
    except Exception:
        return False

def check_process_active(process_substring: str) -> bool:
    """Checks if a process with a given name is active on Windows/Linux host."""
    try:
        if os.name == 'nt': # Windows host
            cmd = f'tasklist /NH /FI "IMAGENAME eq {process_substring}"'
            output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
            return process_substring.lower() in output.lower()
        else: # Linux/POSIX host
            cmd = f'pgrep -f "{process_substring}"'
            output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
            return len(output.strip()) > 0
    except Exception:
        return False

def run_telemetry_scan():
    print("=" * 80)
    print("💎 RUNNING SYSTEM-WIDE RUNTIME SCAN (PORTS, SOCKETS & DAEMONS)")
    print("=" * 80)
    
    # Store running states and variables
    variables_map = {}
    active_process_map = {
        "node.exe" if os.name == 'nt' else "node": check_process_active("node.exe" if os.name == 'nt' else "node"),
        "clangd.exe" if os.name == 'nt' else "clangd": check_process_active("clangd.exe" if os.name == 'nt' else "clangd"),
        "lmstudio.exe" if os.name == 'nt' else "lmstudio": check_process_active("lmstudio.exe" if os.name == 'nt' else "lmstudio"),
    }
    
    # Header for markdown table
    markdown_lines = []
    markdown_lines.append("| SERVICE KEY | PORT | STATUS | DYNAMIC ENV VARIABLE VALUE | DESCRIPTION |")
    markdown_lines.append("|---|---|---|---|---|")
    
    for key, data in TARGET_SERVICES.items():
        is_online = ping_port("127.0.0.1", data["port"])
        
        status_str = "🟢 ONLINE" if is_online else "🔴 OFFLINE"
        env_val = data["env_val"] if is_online else "NULL"
        
        # Bind status to local dictionary for export
        variables_map[key] = {
            "status": "ONLINE" if is_online else "OFFLINE",
            "port": data["port"],
            "env_var": data["env_var"],
            "env_val": env_val
        }
        
        # Add row to markdown list
        markdown_lines.append(f"| `{key}` | `{data['port']}` | **{status_str}** | `{data['env_var']}={env_val}` | {data['desc']} |")
    
    # Process telemetry table
    process_lines = []
    process_lines.append("\n### Host Process Telemetry")
    process_lines.append("| RUNTIME BINARY | HOST PROCESS ACTIVE | STATUS COMMENT |")
    process_lines.append("|---|---|---|")
    for proc, active in active_process_map.items():
        proc_status = "🟢 ACTIVE" if active else "⚪ INACTIVE"
        comment = ""
        if "clangd" in proc:
            comment = "Active indexing daemon (Can starve Raylets if unchecked)" if active else "Suspended (Saves CPU cycles)"
        elif "node" in proc:
            comment = "NPM Dev Servers / WebSocket drivers loaded" if active else "Web frontends suspended"
        elif "lmstudio" in proc:
            comment = "LM Studio UI dashboard running" if active else "Headless server mode or closed"
            
        process_lines.append(f"| `{proc}` | **{proc_status}** | {comment} |")
        variables_map[f"PROCESS_{proc.replace('.', '_').upper()}"] = "ACTIVE" if active else "INACTIVE"
        
    # Combine tables
    full_markdown_report = "\n".join(markdown_lines) + "\n" + "\n".join(process_lines)
    
    # Print Markdown Table to terminal (stderr safe)
    print(full_markdown_report, file=sys.stderr)
    
    # Export state variables as a clean JSON map on disk for other modules to load
    export_path = "swarm_env_state.json"
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(variables_map, f, indent=2)
        
    print(f"\n✅ Telemetry completed. Bound states to variables in '{export_path}'", file=sys.stderr)
    
    # Print variables output for user visual inspection
    print("\n[DYNAMIC PROGRAMMATIC VARIABLES BINDINGS]")
    print(json.dumps(variables_map, indent=2))
    
if __name__ == "__main__":
    run_telemetry_scan()
