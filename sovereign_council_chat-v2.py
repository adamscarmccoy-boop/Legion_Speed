# sovereign_council_chat-v2.py
# =============================================================================
# 🏛️ SOVEREIGN COUNCIL MASTER CLI CHAT - VERSION 2
# Fused with a native LangGraph State Machine (StateGraph) for multi-node routing.
# Coordinates local/cloud preprocessors, ctypes memory-mapping, and execution.
# Supports robust manual/automatic dynamic state nodes and real-time telemetry.
# =============================================================================

import os
import sys
import time
import ctypes
import struct
import atexit
import signal
import json
import urllib.request
import urllib.error
from pydantic import BaseModel, Field, field_validator

# Configurable endpoints
DEFAULT_LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"
DEFAULT_NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
DEFAULT_NVIDIA_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1"
DEFAULT_LOCAL_MODEL = "nvidia/nemotron-3-nano-4b"

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

# ANSI Color escapes for pristine console telemetry
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

STRUCT_FORMAT = "<64s64s32s512s32s12f12fd"
EXPECTED_SIZE = 808

# Global handle for DLL linkage
DLL_LIBRARY_HANDLE = None

# =============================================================================
# 1. PLATFORM-IMMUNE LIFE-CYCLE STABILIZER
# =============================================================================
def clean_exit_handler(*args, **kwargs):
    sys.stderr.write('\n' + "[LMS LIFECYCLE] Exit triggered. Flushing system streams..." + '\n')
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write("[LMS LIFECYCLE] Active Ray session detected. Disconnecting..." + '\n')
            ray.shutdown()
    except Exception:
        pass
    if args and isinstance(args[0], int):
        sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)

# =============================================================================
# 2. BARE-METAL C++ DLL STRUCT & INTERFACE
# =============================================================================
class NativeSwarmNodeState(ctypes.Structure):
    _fields_ = [
        ("task_id", ctypes.c_char * 64),
        ("node_name", ctypes.c_char * 64),
        ("status", ctypes.c_char * 32),
        ("user_query", ctypes.c_char * 512),
        ("tool_target", ctypes.c_char * 32),
        ("dsp_features", ctypes.c_float * 12),
        ("output_scores", ctypes.c_float * 12),
        ("execution_time_us", ctypes.c_double),
    ]

class FlatSovereignState(BaseModel):
    task_id: bytes = Field(..., max_length=64)
    node_name: bytes = Field(..., max_length=64)
    status: bytes = Field(..., max_length=32)
    user_query: bytes = Field(..., max_length=512)
    tool_target: bytes = Field(..., max_length=32)
    dsp_features: list[float] = Field(..., min_length=12, max_length=12)
    output_scores: list[float] = Field(..., min_length=12, max_length=12)
    execution_time_us: float

    @field_validator("task_id", "node_name", "status", "user_query", "tool_target", mode="before")
    @classmethod
    def strip_null_padding(cls, value: bytes) -> bytes:
        if isinstance(value, bytes):
            return value.split(b"\x00", 1)[0]
        return value

    @classmethod
    def from_binary_buffer(cls, buffer: bytes) -> "FlatSovereignState":
        """Unpacks raw, un-serialized memory blocks directly into the Pydantic schema."""
        unpacked = struct.unpack(STRUCT_FORMAT, buffer)
        return cls(
            task_id=unpacked[0],
            node_name=unpacked[1],
            status=unpacked[2],
            user_query=unpacked[3],
            tool_target=unpacked[4],
            dsp_features=list(unpacked[5:17]),
            output_scores=list(unpacked[17:29]),
            execution_time_us=unpacked[29]
        )

    def to_binary_buffer(self) -> bytes:
        """Packs the flat schema back to C++-compatible raw bytes."""
        return struct.pack(
            STRUCT_FORMAT,
            self.task_id.ljust(64, b"\x00"),
            self.node_name.ljust(64, b"\x00"),
            self.status.ljust(32, b"\x00"),
            self.user_query.ljust(512, b"\x00"),
            self.tool_target.ljust(32, b"\x00"),
            *self.dsp_features,
            *self.output_scores,
            self.execution_time_us
        )

def load_sovereign_library(dll_path=None):
    if dll_path is None:
        dll_path = os.environ.get("SOVEREIGN_DLL_PATH", r"C:\WEB CASE STUDY\sovereign_kernel.dll")
    
    if not os.path.exists(dll_path):
        return None, f"{YELLOW}[-] Sovereign DLL not found on disk at: {dll_path} (Using simulated loopback fallback){RESET}"
        
    try:
        lib = ctypes.CDLL(dll_path)
        
        if hasattr(lib, "load_state_agent"):
            lib.load_state_agent.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
            lib.load_state_agent.restype = ctypes.c_bool
            msg = f"{GREEN}[+] Sovereign C++ DLL fully loaded and bound from: {dll_path}{RESET}"
        else:
            msg = f"{GREEN}[+] Sovereign C++ DLL loaded from: {dll_path} (Bypassed optional load_state_agent hook){RESET}"
            
        lib.step_state_agent.argtypes = [NativeSwarmNodeState]
        lib.step_state_agent.restype = NativeSwarmNodeState
        return lib, msg
    except Exception as e:
        return None, f"{RED}[-] Error linking to Sovereign C++ DLL: {e} (Falling back to local simulation mode){RESET}"

# =============================================================================
# 3. DIRECT REST INFERENCE HANDLER
# =============================================================================
def query_model(prompt, system_prompt="You are a helpful assistant.", use_cloud=False, api_key=None, model=None):
    headers = {"Content-Type": "application/json"}
    
    if use_cloud:
        url = DEFAULT_NVIDIA_URL
        selected_model = model or DEFAULT_NVIDIA_MODEL
        key = api_key or NVIDIA_API_KEY
        if not key:
            print(f"{RED}[-] Error: NVIDIA_API_KEY is not set. Toggling off cloud mode.{RESET}")
            return None
        headers["Authorization"] = f"Bearer {key}"
    else:
        url = DEFAULT_LM_STUDIO_URL
        selected_model = model or DEFAULT_LOCAL_MODEL
        
    payload = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            return res_json["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"{RED}[-] REST API request failed: {e}{RESET}")
        return None

# =============================================================================
# 4. FULL Python-Based LangGraph State Machine Bridge
# =============================================================================

# State Schema Definitions
from typing import Annotated, Sequence, TypedDict, List

def merge_messages(left: list, right: list) -> list:
    return left + right

class CouncilState(TypedDict):
    messages: List[dict]
    active_node: str
    use_cloud: bool
    task_id: str
    status: str
    dsp_features: List[float]
    output_scores: List[float]
    execution_time_us: float

# Attempt dynamic load of genuine LangGraph components with absolute safety fallback
try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH_SDK = True
except ImportError:
    HAS_LANGGRAPH_SDK = False

    # Standalone, zero-dependency replica of the compiled StateGraph State Machine
    class END:
        pass

    class StateGraphReplica:
        def __init__(self, state_schema):
            self.nodes = {}
            self.edges = []
            self.entry_point = None

        def add_node(self, name: str, action):
            self.nodes[name] = action

        def add_edge(self, source: str, target: str):
            self.edges.append((source, target))

        def set_entry_point(self, name: str):
            self.entry_point = name

        def compile(self):
            return self

        def invoke(self, state: dict) -> dict:
            """Executes compiled routing nodes sequentially in-process."""
            current_node = self.entry_point
            current_state = state.copy()
            
            # Simple linear loop for council state mapping
            while current_node and current_node is not END:
                # Run the node
                node_output = self.nodes[current_node](current_state)
                # Merge outputs
                for k, v in node_output.items():
                    current_state[k] = v
                
                # Direct lookup next routing edge
                next_node = None
                for src, dest in self.edges:
                    if src == current_node:
                        next_node = dest
                        break
                current_node = next_node
                
            return current_state


# --- LANGGRAPH NODE IMPLEMENTATIONS ---

def preprocessor_node(state: CouncilState) -> dict:
    """Queries LM Studio or NVIDIA Cloud to extract the 12 DSP features."""
    prompt = state["messages"][-1]["content"] if state["messages"] else ""
    use_cloud = state["use_cloud"]
    active_node = state["active_node"]
    
    system_prompt = (
        "You are the Sovereign DSP Preprocessor. Analyze the user's audio calibration instruction "
        "and extract exactly 12 floating-point features representing target frequencies and coefficients. "
        "Return ONLY a flat JSON list of 12 floats. No markdown, no preambles.\n"
        "Example: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]"
    )
    
    print(f"\n{CYAN}📡 [LANGGRAPH NODE: preprocessor] Querying {'NVIDIA Cloud' if use_cloud else 'Local GGUF (LM Studio)'}...{RESET}")
    start_time_inference = time.perf_counter()
    inference_response = query_model(prompt, system_prompt, use_cloud=use_cloud)
    latency_inference_ms = (time.perf_counter() - start_time_inference) * 1000.0
    
    features = [1.0] * 12
    if not inference_response:
        print(f"{RED}[-] Prompt preprocessing aborted. Using safety flat array fallback.{RESET}")
    else:
        try:
            cleaned_resp = inference_response.strip()
            if cleaned_resp.startswith("```"):
                lines = cleaned_resp.splitlines()
                if len(lines) > 2:
                    cleaned_resp = "".join(lines[1:-1])
                else:
                    cleaned_resp = cleaned_resp.replace("```json", "").replace("```", "")
            
            features = json.loads(cleaned_resp.strip())
            if not isinstance(features, list) or len(features) != 12:
                raise ValueError("Payload must comprise exactly 12 float points.")
            features = [float(f) for f in features]
            print(f"{GREEN}📥 [LANGGRAPH NODE: preprocessor] Received features in {latency_inference_ms:.1f}ms: {features}{RESET}")
        except Exception as e:
            print(f"{YELLOW}[!] Regex-extraction failed: {e}. Defaulting to aligned calibration features.{RESET}")
            
    return {
        "dsp_features": features,
        "status": "PREPROCESSED"
    }

def silicon_memory_node(state: CouncilState) -> dict:
    """Interacts with the precompiled C++ DLL via ctypes mapping."""
    features = state["dsp_features"]
    active_node = state["active_node"]
    task_id = state["task_id"]
    
    flat_state = FlatSovereignState(
        task_id=task_id.encode("utf-8"),
        node_name=active_node.encode("utf-8"),
        status=b"PENDING_IN_MEMORY",
        user_query=state["messages"][-1]["content"].encode("utf-8") if state["messages"] else b"",
        tool_target=b"CPP_NATIVE",
        dsp_features=features,
        output_scores=[0.0] * 12,
        execution_time_us=0.0
    )
    
    binary_payload = flat_state.to_binary_buffer()
    assert len(binary_payload) == EXPECTED_SIZE, "Memory layout corruption check failed!"

    output_scores = [0.0] * 12
    execution_time_us = 0.0
    status_str = "COMPLETED_SIMULATION"
    
    if not DLL_LIBRARY_HANDLE:
        output_scores = [f * 1.58 for f in features]
        execution_time_us = 12.45
        print(f"{YELLOW}ℹ️  [LANGGRAPH NODE: silicon_memory] Virtual simulation loop modified flat struct in-place (no DLL loaded).{RESET}")
    else:
        try:
            native_struct = NativeSwarmNodeState()
            native_struct.task_id = flat_state.task_id.ljust(64, b"\x00")
            native_struct.node_name = flat_state.node_name.ljust(64, b"\x00")
            native_struct.status = flat_state.status.ljust(32, b"\x00")
            native_struct.user_query = flat_state.user_query.ljust(512, b"\x00")
            native_struct.tool_target = flat_state.tool_target.ljust(32, b"\x00")
            for i, val in enumerate(flat_state.dsp_features):
                native_struct.dsp_features[i] = float(val)
                
            start_t = time.perf_counter_ns()
            result_struct = DLL_LIBRARY_HANDLE.step_state_agent(native_struct)
            end_t = time.perf_counter_ns()
            
            bridge_latency = (end_t - start_t) / 1000.0
            output_scores = list(result_struct.output_scores[:12])
            execution_time_us = result_struct.execution_time_us
            status_str = result_struct.status.decode('utf-8', errors='ignore').strip()
            print(f"{GREEN}⚡ [LANGGRAPH NODE: silicon_memory] Direct DLL Pointer modified. Bridge Latency: {bridge_latency:.2f} µs{RESET}")
        except Exception as e:
            print(f"{RED}[-] C++ DLL call crashed: {e}. Falling back to simulation.{RESET}")
            output_scores = [f * 1.58 for f in features]
            execution_time_us = 12.45
            status_str = "FAILED_DLL_FALLBACK"

    return {
        "output_scores": output_scores,
        "execution_time_us": execution_time_us,
        "status": status_str
    }

def postprocessor_node(state: CouncilState) -> dict:
    """Evaluates output scores and compiles the final telemetry block."""
    output_scores = state["output_scores"]
    features = state["dsp_features"]
    
    print(f"\n{BOLD}{MAGENTA}" + "-" * 80)
    print("📈 ACTIVE COGNITIVE LANGGRAPH CYCLE OUTCOMES:")
    print("-" * 80 + RESET)
    print(f"📄 Task ID:          {GREEN}{state['task_id']}{RESET}")
    print(f"⚙️  Active Node:      {CYAN}{state['active_node']}{RESET}")
    print(f"🟢 State Status:     {YELLOW}{state['status']}{RESET}")
    print(f"📊 Extracted Feats:  {list(round(x, 4) for x in features[:4])}...")
    print(f"📈 Output Scores:    {list(round(x, 4) for x in output_scores[:4])}...")
    print(f"🕰️  C++ DLL Execution: {GREEN}{state['execution_time_us']:.2f} µs{RESET}")
    print(f"{BOLD}{MAGENTA}" + "-" * 80 + RESET + "\n")
    
    return {
        "status": "COMPLETED_GRAPH_CYCLE"
    }

def compile_sovereign_langgraph() -> StateGraph:
    """Assembles and compiles the full LangGraph state machine flow."""
    if HAS_LANGGRAPH_SDK:
        workflow = StateGraph(CouncilState)
    else:
        workflow = StateGraphReplica(CouncilState)
        
    workflow.add_node("preprocessor", preprocessor_node)
    workflow.add_node("silicon_memory", silicon_memory_node)
    workflow.add_node("postprocessor", postprocessor_node)
    
    workflow.set_entry_point("preprocessor")
    workflow.add_edge("preprocessor", "silicon_memory")
    workflow.add_edge("silicon_memory", "postprocessor")
    workflow.add_edge("postprocessor", END)
    
    return workflow.compile()

# =============================================================================
# 5. CORE INTERACTIVE CONSOLE CHAT RUNNER
# =============================================================================
def main():
    os.system("cls" if os.name == "nt" else "clear")
    print(BOLD + CYAN + "=" * 80)
    print("🏛️  SOVEREIGN COUNCIL: TERMINAL COGNITIVE MEMORY-MAPPED CHAT - V2")
    print("   Dual-Channel Silicon Processing & Continuous Multi-Turn LangGraph Machine")
    print("=" * 80 + RESET)
    
    # Parse initial startup args
    import argparse
    parser = argparse.ArgumentParser(description="Sovereign Council Chat Console")
    parser.add_argument("--dll", help="Path to sovereign_kernel.dll")
    parser.add_argument("--cloud", action="store_true", help="Initiate with cloud-first preprocessor routing")
    parser.add_argument("--node", default="AcousticRouter", help="Starting state agent node name")
    args = parser.parse_args()

    # Load initial resources globally
    global DLL_LIBRARY_HANDLE
    DLL_LIBRARY_HANDLE, status_msg = load_sovereign_library(args.dll)
    print(status_msg)
    
    # State tracking variables
    use_cloud = args.cloud
    active_node = args.node
    task_count = 100
    
    # Compile the LangGraph engine
    print(f"⚙️  [INITIALIZATION] Compiling unified Sovereign Council LangGraph StateGraph...")
    compiled_graph = compile_sovereign_langgraph()
    
    if HAS_LANGGRAPH_SDK:
        print(f"✅ {GREEN}LangGraph StateGraph compiled with full native Python LangGraph library.{RESET}")
    else:
        print(f"✅ {YELLOW}LangGraph StateGraph compiled in standalone replica mode (no dependencies needed).{RESET}")
    
    print("\n" + BOLD + "Active Command Sensory Plugs:" + RESET)
    print(f"  {YELLOW}/node <name>{RESET}  : Switches the C++ state agent routing node (Current: {active_node})")
    print(f"  {YELLOW}/cloud{RESET}        : Toggles preprocessor between local GGUF and NVIDIA Titan Cloud")
    print(f"  {YELLOW}/info{RESET}         : Prints physical telemetry, commit limit metrics, and active ports")
    print(f"  {YELLOW}/exit{RESET}         : Powers down the active memory sessions safely")
    print("-" * 80)

    while True:
        try:
            # Custom input prompt
            prompt_indicator = f"{CYAN}[SOVEREIGN - {active_node}]{RESET} "
            if use_cloud:
                prompt_indicator = f"{MAGENTA}[CLOUD_TITAN - {active_node}]{RESET} "
                
            user_input = input(f"👤 {prompt_indicator}>> ").strip()
            if not user_input:
                continue

            # Command Routing
            if user_input.lower() in ["/exit", "exit", "quit"]:
                print(f"\n{CYAN}🛸 De-registering process lifecycles. Stay sovereign.{RESET}")
                break
                
            elif user_input.lower() == "/cloud":
                use_cloud = not use_cloud
                target_str = "NVIDIA Cloud (Nemotron-3.3-Super-49B)" if use_cloud else "Local LM Studio (Nemotron-3-Nano)"
                print(f"{GREEN}[v] Preprocessor successfully toggled to: {target_str}{RESET}")
                continue
                
            elif user_input.lower().startswith("/node"):
                parts = user_input.split(" ", 1)
                if len(parts) < 2:
                    print(f"{YELLOW}[!] Usage: /node <node_name_string> (e.g. SovereignSieve){RESET}")
                    continue
                active_node = parts[1].strip()
                print(f"{GREEN}[v] State agent node reconfigured. Target: {active_node}{RESET}")
                continue
                
            elif user_input.lower() == "/info":
                print(f"\n{BOLD}{CYAN}📟 PHYSICAL WORKSTATION DIAGNOSTICS:{RESET}")
                print(f"  - Active State Node : {active_node}")
                print(f"  - Preprocessor API  : {'NVIDIA Cloud Integration' if use_cloud else 'Local LM Studio REST Port'}")
                print(f"  - Memory Commits    : 16 GB Physical / 64 GB Pagefile Ceiling (80 GB Total Event 2004 crash guard)")
                print(f"  - Virtual Sandbox   : WSL2 Cap @ 6 GB Auto-Reclaim")
                print(f"  - Target Binary DLL : {args.dll if args.dll else 'C:\\\\WEB CASE STUDY\\\\sovereign_kernel.dll'}")
                print(f"  - DLL Memory Link   : {GREEN}BOUND & ACTIVE{RESET}" if DLL_LIBRARY_HANDLE else f"{YELLOW}SIMULATED BYPASS ACTIVE{RESET}")
                print(f"  - State Machine     : {'Native Python LangGraph Graph' if HAS_LANGGRAPH_SDK else 'Zero-Dependency LangGraph Engine'}")
                print("-" * 80 + "\n")
                continue

            # Run via the LangGraph State Machine
            task_count += 1
            task_id_str = f"t-{task_count}-council-validation"
            
            # Initial LangGraph state block
            initial_state = {
                "messages": [{"role": "user", "content": user_input}],
                "active_node": active_node,
                "use_cloud": use_cloud,
                "task_id": task_id_str,
                "status": "INITIATED",
                "dsp_features": [1.0] * 12,
                "output_scores": [0.0] * 12,
                "execution_time_us": 0.0
            }
            
            # Dispatch state machine run
            compiled_graph.invoke(initial_state)

        except KeyboardInterrupt:
            print(f"\n{CYAN}🛸 Terminal session interrupted cleanly. Shutting down loops...{RESET}")
            break
        except Exception as e:
            print(f"{RED}[- ] Runtime exception encountered: {e}{RESET}")

if __name__ == "__main__":
    main()
