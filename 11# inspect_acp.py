# inspect_acp.py
import os
import json
import ray
from acp_control_plane import ACPControlPlane, ACPEnvelope
from openai import OpenAI
from dotenv import load_dotenv

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


load_dotenv()  # loads .env if present

def main():
    # 1️⃣ Connect to Ray (assumes a cluster is already up)
    ray.init(address="auto", namespace="legion", ignore_reinit_error=True, logging_level=40)
    print("=== Ray cluster info ===")
    # 2️⃣ Grab the existing ACPControlPlane actor (must be named exactly as in your code)
    try:
        acp = ray.get_actor("ACPControlPlane", namespace="legion")
    except ValueError:
        print("❌ Could not find an actor named 'ACPControlPlane' in namespace 'default'.")
        print("   Make sure the ACP control plane is started (e.g., `python acp_control_plane.py`).")
        return

    # 3️⃣ Pull state from the actor (these are regular remote methods)
    agents = ray.get(acp.register_agents.remote())
    events = ray.get(acp.event_log.remote())[-5:]  # last 5 events

    print("=== ACP Control Plane state ===")
    print(f"Registered agents ({len(agents)}):")
    for reg in agents:
        print(f"  • {reg.agent_id}: {reg.agent_name} – {reg.capabilities} – {reg.endpoint_uri}")
    print("\nRecent events:")
    for ev in events:
        print(f"  [{ev.event_type}] from {ev.source_agent} @ {ev.timestamp}")

    # 4️⃣ Quick LM Studio health check (uses the same endpoint as your benchmark)
    try:
        client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")
        resp = client.chat.completions.create(
            model="nvidia/nemotron-3-nano-4b",
            messages=[{"role": "user", "content": "ping"}],
            temperature=0.0,
            max_tokens=5
        )
        print("\n=== LM Studio reachable ===")
        print(f"Reply: {resp.choices[0].message.content.strip()}")
    except Exception as e:
        print("\n⚠️ LM Studio not reachable:", e)

    # 5️⃣ Hint for low‑level socket/pipe inspection
    print("\n=== To see raw sockets / pipes ===")
    print("Run one of these in a PowerShell/CMD window:")
    print("  netstat -ano | findstr :1234          # LM Studio port")
    print("  Get-NetTCPConnection -State Established -RemotePort 1234")
    print("  # For named pipes used by llama.cpp or your C++ code:")
    print("  Get-Process -Id <PID> | Select -Expand Handles | Where {$_.Type -eq 'File' -and $_.Name -like '\\\\Device\\\\NamedPipe\\*'}")

if __name__ == "__main__":
    main()