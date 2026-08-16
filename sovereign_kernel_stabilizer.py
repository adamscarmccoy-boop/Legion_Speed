# sovereign_kernel_stabilizer.py
# Sovereign Multi-Process Stabilizer, Dynamic Port-Catcher, and JS SDK Bridge
# Cleanly terminates zombie processes, tracks the shifting C++ llama_server port, 
# and aligns the local LM Studio SDK JavaScript client inside your active memory space.

import os
import sys
import time
import socket
import json
import logging
import subprocess
import traceback
import shutil

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


# Prevent console encoding issues on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Setup robust system logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | [SOVEREIGN STABILIZER] | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("SovereignStabilizer")

# Import psutil defensively
try:
    import psutil
except ImportError:
    log.error("[-] psutil is not installed. Running 'pip install psutil' is required on the host.")
    sys.exit(1)

# Import Ray defensively
try:
    import ray
except ImportError:
    log.error("[-] Ray Core SDK is not installed. Running 'pip install ray' is required on the host.")
    sys.exit(1)

# =============================================================================
# 1. PROCESS CLEANUP LAYER (KILLING ZOMBIE PYTHONS)
# =============================================================================

def kill_zombie_pythons():
    """
    Iterates through the host process table and terminates all other running 
    Python processes (e.g. stranded background servers, hung tool executors) 
    while safeguarding the current script's PID.
    """
    my_pid = os.getpid()
    log.info(f"🧹 Sweeping process table to locate zombie scripts. Current PID: {my_pid}")
    
    kill_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check for Python runtimes
            proc_name = proc.info['name'] or ''
            cmdline = proc.info['cmdline'] or []
            proc_pid = proc.info['pid']
            
            # Safeguard our own process
            if proc_pid == my_pid:
                continue
                
            cmdline_str = " ".join(cmdline).lower()
            is_python = "python" in proc_name.lower() or any("python" in arg.lower() for arg in cmdline)
            
            # Check for running helper scripts we want to flush
            if is_python and proc_pid != my_pid:
                log.warning(f"   [TERMINATING] Stranded process found: PID {proc_pid} | Cmd: {' '.join(cmdline[:4])}...")
                p = psutil.Process(proc_pid)
                p.terminate()  # Graceful exit trigger
                
                # Check if it died, otherwise force kill
                try:
                    p.wait(timeout=1.0)
                except psutil.TimeoutExpired:
                    log.warning(f"   [FORCE KILLING] Process PID {proc_pid} refused to stop.")
                    p.kill()
                kill_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
            
    log.info(f"✅ Process sweep complete. Terminated {kill_count} lingering background scripts.")

# =============================================================================
# 2. DYNAMIC KERNEL PORT DETECTOR (THE SOCKET CATCHER)
# =============================================================================

def detect_llama_server_port() -> int:
    """
    Scans the system process tree to locate the running C++ llama_server or lms engine,
    queries its active TCP listening ports, and returns the dynamically assigned port.
    """
    log.info("📡 Scanning host sockets to catch the moving C++ llama_server kernel...")
    
    # 1. First, search for active listening connections owned by llama_server or lmstudio
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = (proc.info['name'] or '').lower()
            if "llama_server" in name or "lmstudio" in name or "lms" in name:
                pid = proc.info['pid']
                connections = proc.connections(kind='tcp')
                for conn in connections:
                    if conn.status == 'LISTEN':
                        log.info(f"🎯 Dynamic Port Caught! Found '{name}' (PID {pid}) listening on Port: {conn.laddr.port}")
                        return conn.laddr.port
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
            
    # 2. Fallback: Scan our standard port targets via socket connection sweeps
    fallback_ports = [1234, 1010, 56217, 61777, 52519, 64801]
    log.warning("⚠️ Could not trace socket connections via process tree. Running active fallback port sweep...")
    for port in fallback_ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                res = s.connect_ex(("127.0.0.1", port))
                if res == 0:
                    log.info(f"🟢 Success! Active model server detected on Port: {port}")
                    return port
        except Exception:
            pass
            
    log.warning("⚠️ No active server port detected. Defaulting to standard Port 1234.")
    return 1234

# =============================================================================
# 3. IMMORTAL DETACHED PORT REGISTRY ACTOR
# =============================================================================

@ray.remote(max_restarts=-1, max_task_retries=-1, namespace="legion")
class SovereignKernelTrackerActor:
    """
    Immortal Ray Actor registered in the GCS 'legion' directory. Exposes 
    the active dynamic llama_server port and API configurations to the entire swarm.
    """
    def __init__(self, initial_port: int):
        self.active_port = initial_port
        self.log_file = r"C:\Users\adams\.lmstudio\logs\main.log"
        log.info(f"🧬 SovereignKernelTrackerActor deployed in GCS namespace 'legion' on Port {initial_port}.")

    def update_port(self, port: int) -> str:
        self.active_port = port
        log.info(f"⚡ Port updated in GCS registry to: {port}")
        return f"SUCCESS: Port set to {port}"

    def get_port(self) -> int:
        return self.active_port

    def get_api_url(self) -> str:
        return f"http://127.0.0.1:{self.active_port}/v1"

    def get_metadata(self) -> dict:
        return {
            "status": "ONLINE",
            "active_port": self.active_port,
            "api_url": f"http://127.0.0.1:{self.active_port}/v1",
            "log_file": self.log_file,
            "timestamp": time.time()
        }

# =============================================================================
# 4. JAVASCRIPT SDK BINDING & EXECUTION LAYER (LM STUDIO SDK BINDING)
# =============================================================================

def align_javascript_sdk(active_port: int):
    """
    Fuses the dynamic port to the environment and spins up the Node.js 
    LM Studio JS SDK preprocessor hook or lms dev workspace.
    """
    log.info(f"⚙️ Aligning LM Studio SDK Javascript layer to Port: {active_port}")
    
    # 1. Update active environment variables so Node / TS processes inherit the exact port
    os.environ["LM_STUDIO_PORT"] = str(active_port)
    os.environ["LM_STUDIO_URL"] = f"http://127.0.0.1:{active_port}/v1"
    
    # Write a dynamic port-config.json file for TypeScript/Javascript imports
    config_path = r"C:\WEB CASE STUDY\data\config\dynamic_port_config.json"
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        config_data = {
            "port": active_port,
            "endpoint": f"http://127.0.0.1:{active_port}/v1",
            "websocket_endpoint": f"ws://127.0.0.1:{active_port}",
            "last_handshake": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
        log.info(f"📝 Port config written for JavaScript SDK: '{config_path}'")
    except Exception as e:
        log.warning(f"⚠️ Could not write JS configuration block: {e}")

    # 2. Trigger lms dev / npm start for the tool plugin in a separate Windows console
    try:
        # Standard workspace paths for your TypeScript/JavaScript SDK setup
        target_js_dir = r"C:\WEB CASE STUDY"
        if not os.path.exists(os.path.join(target_js_dir, "package.json")):
            target_js_dir = r"C:\STUDIES\frontend"
            
        if os.path.exists(target_js_dir):
            creation_flags = 0x00000010 if os.name == 'nt' else 0  # CREATE_NEW_CONSOLE for Windows
            
            # Boot the JS Toolbox / SDK via command line with the port injected
            log.info(f"🚀 Booting Javascript LM Studio SDK client inside: {target_js_dir}")
            
            # Executes the lms development mode plugin sync
            cmd = "lms dev" if shutil.which("lms") else "npm run dev"
            subprocess.Popen(
                cmd,
                cwd=target_js_dir,
                shell=True,
                creationflags=creation_flags,
                env=os.environ
            )
            log.info("✅ JS SDK process detached and executing cleanly in external console.")
        else:
            log.warning("⚠️ JS workspace directories not found. Skipping programmatic Node subprocess boot.")
    except Exception as e:
        log.error(f"❌ Failed to boot JS SDK subprocess: {e}")

# =============================================================================
# 5. ORCHESTRATION RUN LOOP
# =============================================================================

def run_stabilization_cycle():
    log.info("=" * 80)
    log.info("📡 INITIATING SOVEREIGN WORKSPACE STABILIZER & KERNEL PORT CATCHER")
    log.info("=" * 80)
    
    # Step 1: Sweep and kill old Python tasks
    kill_zombie_pythons()
    
    # Step 2: Catch the dynamic port from llama_server
    active_port = detect_llama_server_port()
    
    # Step 3: Attach to the local Ray cluster
    log.info("Connecting to GCS Raylet Cluster...")
    try:
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        log.info("✅ Connected cleanly to active Ray Cluster!")
    except Exception as e:
        log.error(f"❌ Failed to attach to Ray cluster. Make sure 'ray start --head' is active: {e}")
        return

    # Step 4: Register / Update Detached Port Actor inside GCS
    log.info("Synchronizing SovereignPortRegistry in GCS...")
    try:
        tracker = ray.get_actor("SovereignKernelTracker", namespace="legion")
        log.info("💎 SovereignKernelTracker actor handle found. Updating active port...")
        ray.get(tracker.update_port.remote(active_port))
    except ValueError:
        log.info("[-] 'SovereignKernelTracker' not found in GCS. Instantiating immortal detached actor...")
        tracker = SovereignKernelTrackerActor.options(
            name="SovereignKernelTracker",
            lifetime="detached"
        ).remote(initial_port=active_port)
        
    # Step 5: Boot and Align Javascript SDK preprocessors
    align_javascript_sdk(active_port)
    
    log.info("=" * 80)
    log.info(f"🚀 SYSTEM SYNCED: All controllers, Ray Actors, and JS SDK tools mapped to Port {active_port}!")
    log.info("=" * 80)

if __name__ == "__main__":
    try:
        run_stabilization_cycle()
    except KeyboardInterrupt:
        log.info("👋 Exiting stabilizer safely.")
    except Exception as e:
        log.error(f"❌ Master run loop crashed: {e}")
        traceback.print_exc()