import os
import numpy as np
import ray
from ray import serve
from ray import tune
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env



# pyrefly: ignore [missing-import]
import gymnasium as gym
from gym import spaces

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


# pyrefly: ignore [missing-import]
from pedalboard import Pedalboard, Compressor, HighShelfFilter, Limiter
# pyrefly: ignore [missing-import]
import lancedb
import onnxruntime as ort

# =================================================================
# HARD PATHS - EDIT THESE FOR YOUR MACHINE
# =================================================================
MODEL_ONNX_PATH = r"C:\WEB CASE STUDY\sovereign_big_brain_exhaustive.onnx"
LANCEDB_PATH = r"C:\WEB CASE STUDY\lancedb\swarm_registry.lance"
OUTPUT_DIR = r"C:\WEB CASE STUDY\sovereign_onnx_masters_v2"
GPU_ID = 0  # GTX 1650

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =================================================================
# 1. RAY + SERVE INITIALIZATION
# =================================================================
ray.init(address="8265", namespace="legion", GPU_ID=0, include_dashboard=True)
serve.start(detached=True)


@serve.deployment(num_replicas=24, ray_actor_options={"'CPU': 2.0, 'GPU': 1.0, 'special_hardware': 1.0"})
class SovereignCodeBrain:
    def __init__(self, model_path: str):
        self.session = ort.InferenceSession(
            model_path,
            providers=["CUDAExecutionProvider"],
            provider_options=[{"device_id": GPU_ID}],
        )

    def __call__(self, dna_vector: np.ndarray) -> np.ndarray:
        # dna_vector: float32[64]
        ort_inputs = {
            self.session.get_inputs()[0].name: dna_vector.reshape(1, 64).astype(
                np.float32
            )
        }
        outputs = self.session.run(None, ort_inputs)
        return outputs[0].squeeze(0)  # shape (12,)


SovereignCodeBrain.deploy(MODEL_ONNX_PATH)

brain_handle = SovereignCodeBrain.get_handle()


def query_brain(dna_vec: np.ndarray) -> np.ndarray:
    return ray.get(brain_handle.remote(dna_vec))


# =================================================================
# 2. SOVEREIGN ACOUSTIC ENV (RL ENV)
# =================================================================
class SovereignAcousticEnv(gym.Env):
    def __init__(self, config):
        super().__init__()

        # 64-dim DNA Observation, 12-dim DSP Action Space
        self.observation_space = spaces.Box(
            low=-10.0, high=10.0, shape=(64,), dtype=np.float32
        )
        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(12,), dtype=np.float32
        )

        # LanceDB Oracle
        self.db = lancedb.connect(LANCEDB_PATH)
        self.table = self.db.open_table("gold_baselines")

        # Pedalboard (recreated per step to avoid state bleed)
        self.board = Pedalboard()

        self.current_step = 0
        self.max_steps = 100

    def reset(self, *, seed=None, options=None):
        self.current_step = 0
        obs = np.zeros(64, dtype=np.float32)
        return obs, {}

    def _apply_150hz_truth(self, audio: np.ndarray) -> np.ndarray:
        # Placeholder: mono below 150Hz would be implemented with a crossover
        return audio

    def step(self, action: np.ndarray):
        # 1. Generate synthetic DNA (in real system, you'd pull from registry)
        gen_dna = np.random.uniform(-1, 1, 64).astype(np.float32)

        # 2. Query ONNX brain via Ray Serve (generation mode)
        brain_out = query_brain(gen_dna)  # shape (12,)

        # 3. Apply action as delta to brain outputs
        dsp_params = brain_out + action  # still 12-dim

        # 4. Fresh Pedalboard per step to avoid cross-block contamination
        self.board = Pedalboard(
            [
                Compressor(
                    threshold_db=dsp_params[0] * 20.0,
                    ratio=4.0 + dsp_params[1] * 10.0,
                ),
                HighShelfFilter(
                    cutoff_frequency_hz=8000.0, gain_db=dsp_params[2] * 12.0
                ),
                Limiter(threshold_db=-0.3),
            ]
        )

        # (Audio processing omitted; reward is based on DNA proximity)

        # 5. Oracle: nearest gold baseline in LanceDB
        results = self.table.search(gen_dna).limit(1).to_pandas()
        if results.empty:
            l2_distance = 10.0
        else:
            l2_distance = float(results["_distance"][0])

        # Reward: closer to gold baseline is better
        reward = -l2_distance

        # 150Hz mono constraint penalty (placeholder)
        if l2_distance > 5.0:
            reward -= 5.0

        self.current_step += 1
        terminated = self.current_step >= self.max_steps
        truncated = False

        info = {}
        return gen_dna, reward, terminated, truncated, info


# =================================================================
# 3. RLLIB TRAINING
# =================================================================
def run_training():
    register_env("SovereignAcousticEnv", lambda config: SovereignAcousticEnv(config))

    config = (
        PPOConfig()
        .environment(env="SovereignAcousticEnv")
        .framework("torch")
        .rollouts(num_rollout_workers=24)
        .resources(num_gpus=1)
        .training(
            lr=5e-5,
            train_batch_size=4000,
            gamma=0.99,
            model={"fcnet_hiddens": [512, 512]},
        )
    )

    print("--- SOVEREIGN CLUSTER ACTIVE: STARTING NEURAL FORGE ---")
    algo = config.build()

    for i in range(100):
        result = algo.train()
        print(
            f"Iteration {i}: "
            f"reward_min={result['episode_reward_min']:.2f}, "
            f"reward_max={result['episode_reward_max']:.2f}, "
            f"reward_mean={result['episode_reward_mean']:.2f}"
        )

        if i % 10 == 0:
            checkpoint_dir = algo.save(OUTPUT_DIR)
            print(f"Checkpoint saved in {checkpoint_dir}")


if __name__ == "__main__":
    try:
        run_training()
    except KeyboardInterrupt:
        print("Shutting down Sovereign Cluster...")
        ray.shutdown()
import ray
from ray import train, tune
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env
import gym
from gym import spaces
import numpy as np

# =================================================================
# HARD PATHS - THE SOVEREIGN REGISTRY
# =================================================================
REGISTRY_NAME = "CodeKnowledgeLedger"

# =================================================================
# THE SOVEREIGN CODE ENVIRONMENT
# =================================================================
class SovereignCodeEnv(gym.Env):
    def __init__(self, config):
        # Observation: 1024-D Code Vector from the Ledger
        self.observation_space = spaces.Box(low=-10.0, high=10.0, shape=(1024,), dtype=np.float32)
        # Action: Adjusting 4 Core Cluster Parameters (e.g., Batch Size, Worker Count, etc.)
        self.action_space = spaces.Box(low=0.1, high=1.0, shape=(4,), dtype=np.float32)
        
        # Connect to the detached Ledger Actor
        try:
            self.ledger = ray.get_actor(REGISTRY_NAME)
        except ValueError:
            print(f"CRITICAL: {REGISTRY_NAME} not found. Ensure it is started with lifetime='detached'.")

    def reset(self):
        # Pull a random code fragment DNA from the Zero-Memory Ledger
        dna = ray.get(self.ledger.get_random_dna.remote())
        return np.array(dna, dtype=np.float32)

    def step(self, action):
        # 1. Action: The RL Agent 'tunes' the cluster (Simulated for training)
        # In production, this would hit Ray Serve's 'update_config'
        
        # 2. Reward: The machine learning 'finds the disconnects'
        # Reward = (1 / Latency) + (Structural Alignment Score)
        # We calculate the L2 distance to the 'Gold Architecture' in the Ledger
        alignment_score = ray.get(self.ledger.calculate_alignment.remote(action))
        
        reward = float(alignment_score)
        done = True # Single-step optimization
        
        # Get next state
        next_dna = ray.get(self.ledger.get_random_dna.remote())
        return np.array(next_dna, dtype=np.float32), reward, done, {}

# =================================================================
# THE RLLIB EXECUTION (ZERO-MEMORY TRAINING)
# =================================================================
def run_sovereign_rl():
    ray.init(address="auto", ignore_reinit_error=True)
    
    # Register the environment that talks to your Ledger
    register_env("SovereignCodeEnv", lambda config: SovereignCodeEnv(config))

    # Configuration for PPO (Proximal Policy Optimization)
    config = (
        PPOConfig()
        .environment(env="SovereignCodeEnv")
        .framework("torch")
        .resources(num_gpus=1) # Saturate the GTX 1650
        .rollouts(num_rollout_workers=8) # Match your CPU cores
        .training(
            model={"fcnet_hiddens": [512, 512, 256]}, # Deep brain for code optimization
            train_batch_size=2048,
            lr=1e-4
        )
    )

    print("--- INITIATING SOVEREIGN RL: TRAINING ON CODEKNOWLEDGELEDGER ---")
    algo = config.build()

    for i in range(50):
        results = algo.train()
        print(f"Iter {i}: Mean Reward (Structural Alignment) = {results['episode_reward_mean']:.4f}")

if __name__ == "__main__":
    run_sovereign_rl()