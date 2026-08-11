"""
LEGION DYNAMIC LLAMA.CPP KERNEL DISCOVERY & BARE-METAL BRIDGE
Dynamically binds to the running llama-server.exe process on high dynamic ports (50000-60000)
and extracts the runtime session auth token for direct, zero-overhead C++ kernel execution.
"""

import psutil
import requests
import json
import time

try:
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

class LlamaKernelBridge:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 1234
        self.api_key = None
        self.model_path = None
        self.is_direct_kernel = False
        self.refresh()

    def refresh(self):
        """Scans process table for active llama-server.exe instances."""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                pname = proc.info['name'].lower()
                if 'llama-server' in pname:
                    cmdline = proc.info.get('cmdline', [])
                    port = None
                    api_key = None
                    model = None
                    
                    for i, arg in enumerate(cmdline):
                        if arg == '--port' and i + 1 < len(cmdline):
                            port = int(cmdline[i + 1])
                        elif arg == '--api-key' and i + 1 < len(cmdline):
                            api_key = cmdline[i + 1]
                        elif arg == '--model' and i + 1 < len(cmdline):
                            model = cmdline[i + 1]

                    if port:
                        self.port = port
                        self.api_key = api_key
                        self.model_path = model
                        self.is_direct_kernel = True
                        print(f"🔥 [KERNEL FOUND] Bare-metal llama-server.exe on Port {self.port} (PID {proc.info['pid']})")
                        if self.api_key:
                            print(f"🔑 [AUTH TOKEN] Dynamic session key acquired: {self.api_key[:8]}...")
                        if self.model_path:
                            print(f"🧠 [MODEL] {self.model_path.split(chr(92))[-1]}")
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Fallback to standard LM Studio gateway
        self.port = 1234
        self.api_key = None
        self.is_direct_kernel = False
        print("📡 [GATEWAY] Direct llama-server not isolated in process list. Binding to LM Studio Port 1234.")
        return False

    def get_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def chat(self, messages, temperature=0.0, max_tokens=512, tools=None):
        url = f"http://{self.host}:{self.port}/v1/chat/completions"
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if tools:
            payload["tools"] = tools
        
        t0 = time.time()
        resp = requests.post(url, headers=self.get_headers(), json=payload, timeout=60)
        dt = (time.time() - t0) * 1000
        resp.raise_for_status()
        data = resp.json()
        data["_latency_ms"] = dt
        data["_kernel_port"] = self.port
        return data

    def health(self):
        try:
            r = requests.get(f"http://{self.host}:{self.port}/health", timeout=1.0)
            return r.status_code == 200
        except Exception:
            return False

if __name__ == "__main__":
    print("=== TESTING DYNAMIC LLAMA.CPP HIGH-PORT DISCOVERY ===")
    bridge = LlamaKernelBridge()
    print(f"Health Status: {'ONLINE' if bridge.health() else 'OFFLINE'}")
    
    print("\n⚡ Dispatching test turn directly to kernel...")
    res = bridge.chat([{"role": "user", "content": "Sovereign intelligence status ping."}], max_tokens=30)
    print(f"Latency: {res['_latency_ms']:.2f}ms on Port {res['_kernel_port']}")
    print("Response:\n", json.dumps(res, indent=2))
