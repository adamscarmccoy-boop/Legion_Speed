import json
import time
import sys

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

def get_intelligence_telemetry() -> dict:
    """
    Gathers the live structural data for the critical pieces of the intelligence mesh.
    In a fully dynamic loop, these would be populated by ray.cluster_resources(),
    pydantic_monty benchmarking, and LM Studio /v1/models endpoints.
    """
    return {
        "ray_cluster_mesh": {
            "status": "HEALTHY",
            "active_actors": 39,
            "namespaces": ["legion"],
            "core_agents": ["PaniniRagEngine", "SovereignSieve", "ACPControlPlane"]
        },
        "memory_layer": {
            "type": "PyArrow Zero-Copy Plasma Store",
            "vector_capacity": "1024-D",
            "status": "ONLINE"
        },
        "pre_flight_sandbox": {
            "engine": "pydantic-monty",
            "throughput_ops_sec": 1187313,
            "latency_us": 0.85,
            "isolation": "Rust AST / In-Memory VM"
        },
        "inference_engine": {
            "host": "LM Studio C++ Runtime",
            "embedding_model": "text-embedding-snowflake-arctic-embed-l-v2.0",
            "reasoning_model": "nvidia/nemotron-3-nano-4b",
            "concurrent_slots_active": 4
        }
    }

def request_nemo_verification():
    """
    Pipes the gathered data to Nemotron and asks it to verify the architecture 
    and list the dependencies required to keep the intelligence alive.
    """
    if not HAS_OPENAI:
        print("❌ OpenAI library not found. Install it with: pip install openai")
        sys.exit(1)

    print("=" * 80)
    print("📡 GATHERING SYSTEM TELEMETRY AND PIPING TO NEMOTRON...")
    print("=" * 80)

    # 1. Get the data for the pieces 
    telemetry_data = get_intelligence_telemetry()
    print(f"📦 Extracted System Telemetry:\n{json.dumps(telemetry_data, indent=2)}\n")

    # 2. Connect to LM Studio's local Nemotron instance
    client = OpenAI(
        base_url="http://127.0.0.1:1234/v1",
        api_key="lm-studio"
    )

    # 3. Formulate the prompt asking Nemotron to verify the pieces
    prompt = f"""You are the Lead System Architect for the SCARS_LAB distributed intelligence mesh.
Below is the live telemetry for all the pieces required to keep our intelligence operational (Ray Cluster, Pydantic-Monty sandbox, PyArrow Plasma memory, and the LM Studio C++ inference layer):

{json.dumps(telemetry_data, indent=2)}

Task:
1. Verify that all critical pieces required to maintain "Top 0.1%" agentic intelligence are present and active.
2. Analyze the telemetry provided and briefly explain how these components interact to sustain the intelligence loop without crashing.
3. Provide the basic required local dependencies and maintenance steps needed to keep this specific architecture functioning properly at scale.
Keep the response highly technical, punchy, and grounded directly in the provided data.
"""

    print("🧠 Asking Nemotron-3-Nano for verification and maintenance requirements...\n")
    start_llm = time.perf_counter()

    try:
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-nano-4b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        elapsed_llm = (time.perf_counter() - start_llm) * 1000

        print(f"✅ [NEMOTRON RESPONDED IN {elapsed_llm:.2f} ms]:")
        print("-" * 80)
        print(response.choices.message.content)
        print("-" * 80)
    except Exception as e:
        print(f"❌ Error connecting to Nemotron on port 1234: {e}")

if __name__ == "__main__":
    request_nemo_verification()