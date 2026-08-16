import psutil
import socket
import requests
import json
import os

try:
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

print("=" * 65)
print("LLAMA.CPP & LM STUDIO DIRECT KERNEL DISCOVERY")
print("=" * 65)

# 1. Inspect all active listening ports on localhost
listening_map = {}
for conn in psutil.net_connections(kind='inet'):
    if conn.status == 'LISTEN' and conn.laddr.ip in ['127.0.0.1', '0.0.0.0', '::1', '::']:
        pid = conn.pid
        port = conn.laddr.port
        if pid:
            try:
                p = psutil.Process(pid)
                pname = p.name()
                cmd = " ".join(p.cmdline())
            except Exception:
                pname = "unknown"
                cmd = ""
            listening_map[port] = {"pid": pid, "name": pname, "cmd": cmd}

# Sort by port
print(f"Total listening ports found on local machine: {len(listening_map)}\n")

llama_ports = []
for port in sorted(listening_map.keys()):
    info = listening_map[port]
    pname = info["name"].lower()
    cmd = info["cmd"].lower()
    if any(k in pname or k in cmd for k in ["llama", "lmstudio", "server", "python", "node", "electron"]):
        print(f"  [PORT {port:>5}] PID {info['pid']:<6} | {info['name']}")
        if len(info['cmd']) > 0:
            print(f"            CMD: {info['cmd'][:120]}...")
        llama_ports.append(port)

# 2. Probe high ports (50000+ and 9000+) for llama.cpp native endpoints (/slots, /props, /v1/models, /health)
print("\n" + "=" * 65)
print("PROBING CANDIDATE PORTS FOR NATIVE LLAMA.CPP / LM STUDIO KERNEL")
print("=" * 65)

test_ports = [p for p in listening_map.keys() if (p >= 50000 or (9000 <= p <= 9999) or p == 1234 or (1230 <= p <= 1240))]

for p in sorted(test_ports):
    # Check llama.cpp native endpoints: /slots, /props, /health, /v1/models
    endpoints = ["/props", "/slots", "/v1/models", "/health"]
    for ep in endpoints:
        try:
            r = requests.get(f"http://127.0.0.1:{p}{ep}", timeout=0.5)
            if r.status_code == 200:
                print(f"  🔥 [PORT {p}] Responded 200 OK on '{ep}'! Server: {r.headers.get('server', 'unknown')}")
                try:
                    js = r.json()
                    if ep == "/props":
                        print(f"       props: default_generation_settings: {list(js.keys())}")
                    elif ep == "/v1/models":
                        models = [m['id'] for m in js.get('data', [])]
                        print(f"       models ({len(models)}): {models[:3]}")
                except Exception:
                    pass
        except Exception:
            pass

print("\n" + "=" * 65)
