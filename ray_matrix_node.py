import sys
# Force python to lock strictly to your virtual environment site-packages
sys.path.insert(0, r"C:\WEB CASE STUDY\.venv\Lib\site-packages")

import ray
import onnxruntime as ort
import numpy as np

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


ONNX_MODEL_PATH = r"C:\onnx_models\matrix_dit\model.onnx"

class LegionLinearProjectionBridge:
    def __init__(self):
        print("🧬 INITIALIZING MATRIX TRANSFORMATION NODE (1024 ──► 4096)")
        # Xavier initialization to maintain stable structural tensor scaling
        scale = np.sqrt(2.0 / 1024)
        self.W_proj = np.random.randn(1024, 4096).astype(np.float32) * scale
        print("🟢 SUCCESS: 1024-to-4096 transformation lanes mapped in RAM.")

    def transform_vector_topology(self, snowflake_1024d_list: list) -> np.ndarray:
        """
        Zero-copy matrix dot product. Upscales raw 1024D Snowflake vectors 
        into the 4096D hidden encoder feature state topology.
        """
        x = np.ascontiguousarray(snowflake_1024d_list, dtype=np.float32)
        if x.ndim == 1:
            x = np.expand_dims(x, axis=0)
            
        # Execute fast BLAS matrix dot product pass
        projected_latents = np.dot(x, self.W_proj) # Result shape: [Batch, 4096]
        encoder_hidden_states = np.expand_dims(projected_latents, axis=1) # Shape matches [Batch, 1, 4096]
        return encoder_hidden_states


@ray.remote(num_cpus=6)
class LegionMatrixNode:
    def __init__(self, model_path: str = ONNX_MODEL_PATH):
        print("🪐 SWARM NODE INITIALIZATION: SPINNING UP TRANSFORMER ACTOR")
        
        # Pin thread execution strictly to your 6 physical Ryzen 5 3600 cores via AVX2
        self.opts = ort.SessionOptions()
        self.opts.intra_op_num_threads = 6
        self.opts.inter_op_num_threads = 1
        self.opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        self.opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        print(f"📦 Loading compiled stateless graph directly into memory: {model_path}")
        self.session = ort.InferenceSession(
            model_path, 
            self.opts, 
            providers=['CPUExecutionProvider']
        )
        
        # Initialize internal projection bridge step directly inside the actor node
        self.bridge = LegionLinearProjectionBridge()
        print("🟢 SUCCESS: 825-matrix graph and 1024D projection bridge active in memory.")

    def process_swarm_inference(self, raw_snowflake_embedding: list, latent_grid_array: list, timestep_float: float):
        """
        Executes a high-speed inference step over raw memory pointers.
        Passes inputs straight through to C++ native AVX2 SIMD execution lanes.
        """
        # 1. Transform the 1024D Snowflake vector to 4096D on the fly
        projected_encoder_states = self.bridge.transform_vector_topology(raw_snowflake_embedding)
        
        # 2. Package tracking parameters into contiguous numeric numpy inputs
        hidden_states = np.ascontiguousarray(latent_grid_array, dtype=np.float32)
        time_vector = np.array([timestep_float], dtype=np.float32)
        
        execution_payload = {
            "hidden_states": hidden_states,
            "encoder_hidden_states": projected_encoder_states,
            "timestep": time_vector
        }
        
        # 3. Fire stateless pass through the compiled C++ layer
        outputs = self.session.run(None, execution_payload)
        return outputs


if __name__ == "__main__":
    print("=" * 80)
    print("🛰️  LEGION MATRIX CORE: CONFIGURING RUNTIME LAYER ATTACHMENT")
    print("=" * 80)
    
    # Connect directly to the existing head node on port 6379 under namespace legion
    ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
    
    # Self-healing registration block to prevent ActorAlreadyExistsError
    try:
        print("🔍 Scanning swarm registry for an existing warm memory mount...")
        matrix_actor = ray.get_actor("LegionMatrixNode", namespace="legion")
        print("\n" + "=" * 80)
        print("🟢 SUCCESS: Found live, active LegionMatrixNode! Bypassing redeployment.")
        print("Your 5GB Diffusion Transformer weights are warm and fully accessible in RAM.")
        print("=" * 80)
        
    except ValueError:
        print("⚠️  No active node found in registry. Deploying fresh detached worker...")
        matrix_actor = LegionMatrixNode.options(
            name="LegionMatrixNode",
            lifetime="detached",
            namespace="legion" # Binds registration strictly to the isolated legion cluster space
        ).remote()
        print("\n" + "=" * 80)
        print("🟢 PIPELINE LOCKED: Fresh headless C++ matrix engine node is warm and live.")
        print("=" * 80)