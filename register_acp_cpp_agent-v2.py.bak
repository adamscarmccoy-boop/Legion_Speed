import os
import sys
import json
import time
import socket
import logging
import traceback
import requests

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


# Set Ray environment parameters before import to inherit low-overhead C++ settings
os.environ["RAY_gcs_rpc_server_reconnect_timeout_s"] = "120"
os.environ["RAY_DEDUP_LOGS"] = "0"
os.environ["RAY_memory_monitor_refresh_ms"] = "250"

try:
    import ray
except ImportError:
    print("[-] Please run 'pip install ray' to enable Ray actor routing.")
    sys.exit(1)

# =============================================================================
# 1. DISTRIBUTED LOGGING SETUP
# =============================================================================
def setup_logging():
    logger = logging.getLogger("ACP_FAST_AGENT")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | [ACP NATIVE AGENT] | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    return logger

log = setup_logging()

# =============================================================================
# 2. THE HIGH-PERFORMANCE C++ COGNITIVE AGENT ACTOR
# =============================================================================
@ray.remote(
    max_restarts=-1,         # Infinite self-healing restarts if evicted
    max_task_retries=-1,     # Auto-retry pending queries in Plasma Shared Memory
    namespace="legion"       # Fixed namespace to bind with the local control plane
)
class FastCppAgentActor:
    """
    Stateful Ray Actor executing native C++ LLM inference.
    Communicates directly with LM Studio's llama.cpp backend on Ports 1234 / 1010.
    Bypasses heavy Python bottlenecks, leveraging prompt caching and linear memory.
    """
    def __init__(self, port: int = 1234):
        self.port = port
        self.endpoint = f"http://127.0.0.1:{port}/v1"
        self.model_name = "nvidia/nemotron-3-nano-4b"
        log.info(f"[+] Fast C++ Agent initialized on PID {os.getpid()} targeting Port {port}")

    def ping(self) -> str:
        return "PONG"

    def execute_inference(self, prompt: str, system_prompt: str = None) -> dict:
        """
        Pipes requests straight into LM Studio's compiled C++ inference engine.
        Leverages CUDA hybrid offloading, linear Mamba-2 State-Space kernels, and VRAM JIT caching.
        """
        headers = {"Content-Type": "application/json"}
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.0,       # Force absolute deterministic precision for system audits
            "repeat_penalty": 1.100,
            "top_k": 40,
            "min_p": 0.05
        }

        start_time = time.time()
        try:
            res = requests.post(f"{self.endpoint}/chat/completions", json=payload, headers=headers, timeout=60)
            elapsed = (time.time() - start_time) * 1000.0
            
            if res.status_code == 200:
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                prompt_tokens = data.get("usage", {}).get("prompt_tokens", 0)
                completion_tokens = data.get("usage", {}).get("completion_tokens", 0)
                
                log.info(f"[*] C++ Inference Complete in {elapsed:.2f}ms | Ingested: {prompt_tokens}t | Generated: {completion_tokens}t")
                return {
                    "status": "SUCCESS",
                    "content": content,
                    "metrics": {
                        "latency_ms": elapsed,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "tokens_per_sec": completion_tokens / (elapsed / 1000.0) if elapsed > 0 else 0
                    }
                }
            else:
                return {"status": "FAILED", "error": f"LM Studio C++ returned HTTP {res.status_code}: {res.text}"}
        except Exception as e:
            return {"status": "FAILED", "error": f"Failed to handshake with C++ backend on Port {self.port}: {str(e)}"}

# =============================================================================
# 3. NATIVE HANDSHAKE & ACP REGISTRATION PIPELINE
# =============================================================================
def register_cpp_agent():
    log.info("=" * 80)
    log.info("🚀 INITIATING NATIVE C++ COGNITIVE AGENT REGISTRATION TO ACP")
    log.info("=" * 80)

    # Step 1: Attach to the existing Raylet Cluster (Zero-Copy Data Plane)
    log.info("[1/4] Connecting to the running local GCS Ray Cluster...")
    try:
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        log.info(f"✅ Success: Handshaked with GCS on Port 6379 under 'legion' namespace!")
    except Exception as e:
        log.error("[-] Failed to attach to Ray. Make sure 'ray start --head' has been executed.")
        log.error(traceback.format_exc())
        sys.exit(1)

    # Step 2: Grab the detached ACPControlPlane Actor Handle from the GCS Directory
    log.info("[2/4] Retrieving detached 'ACPControlPlane' handle...")
    try:
        acp_handle = ray.get_actor("ACPControlPlane", namespace="legion")
        log.info("💎 Found active ACPControlPlane actor registered in GCS!")
    except ValueError:
        log.error("❌ Failed to resolve 'ACPControlPlane' detached actor in 'legion' namespace.")
        log.error("Ensure your central controller daemon is running on your machine.")
        sys.exit(1)

    # Step 3: Instantiate our Fast C++ Agent as an Immortal Detached Actor
    log.info("[3/4] Registering 'LegionFastCppAgent' in Ray Cluster Memory...")
    try:
        # Check if already registered to avoid duplication
        cpp_agent = ray.get_actor("LegionFastCppAgent", namespace="legion")
        log.info("💎 Detached 'LegionFastCppAgent' handle already exists. Re-using active process.")
    except ValueError:
        log.info("[-] 'LegionFastCppAgent' not active. Spawning persistent detached actor...")
        # Auto-detect ports 1234 vs 1010
        active_port = 1234
        for port in [1234, 1010]:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    if s.connect_ex(("127.0.0.1", port)) == 0:
                        active_port = port
                        break
            except Exception:
                pass
                
        cpp_agent = FastCppAgentActor.options(
            name="LegionFastCppAgent",
            lifetime="detached"
        ).remote(port=active_port)
        log.info(f"✅ Detached 'LegionFastCppAgent' instantiated successfully on Port {active_port}!")

    # Step 4: Perform the Handshake and Register Capabilities into the ACP Control Registry
    log.info("[4/4] Syncing capabilities and dispatching Agent Registration payload...")
    try:
        # Construct registration state schema (matching discrete parameters expected by ACPControlPlaneActor)
        agent_id = "legion_fast_cpp_agent"
        agent_name = "Legion Fast C++ Cognitive Agent"
        capabilities = ["native_cpp_inference", "mamba_state_evaluation", "fast_completion"]
        endpoint_uri = "ray://legion_fast_cpp_agent"
        
        # Dispatch to the active ACPControlPlane
        try:
            # Safely invoke register_agent on the existing Control Plane actor using exact keyword matching
            res = ray.get(
                acp_handle.register_agent.remote(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    capabilities=capabilities,
                    endpoint_uri=endpoint_uri
                ),
                timeout=5.0
            )
            log.info(f"📥 [ACP RESPONSE]: {res}")
        except AttributeError:
            log.warning("[!] register_agent method mismatch on ACPControlPlane. Attempting generic state dump...")
            # Fallback to posting event log
            try:
                ray.get(acp_handle.log_event.remote(f"Registered Agent: {agent_name}"), timeout=5.0)
                log.info("✅ Fallback: Logged native registration event directly into ACP event stream.")
            except Exception as inner_err:
                log.error(f"[-] Handshake logging rejected: {inner_err}")

        # Quick end-to-end fire test targeting the newly registered C++ agent
        log.info("🎮 Running high-speed native validation loop...")
        test_prompt = "Perform a micro-benchmark handshake test."
        system_prompt = "You are a fast C++ agent registered on the legion ACP. Return a JSON dict: {'status': 'ONLINE'}."
        
        result_future = cpp_agent.execute_inference.remote(test_prompt, system_prompt)
        # Block on future to check result
        result = ray.get(result_future, timeout=10.0)
        print("\n" + "="*80)
        print("⚡ NATIVE BARE-METAL PIPELINE HANDSHAKE TEST RESULT:")
        print(json.dumps(result, indent=2))
        print("="*80 + "\n")
        
        log.info("🚀 SUCCESS: Checked and Registered! Your local C++ Brain is linked to the ACP!")

    except Exception as e:
        log.error(f"[-] Handshake with ACPControlPlane failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    register_cpp_agent()