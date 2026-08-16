import os
import numpy as np
import ray
from ray import serve
from ray import tune
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env

import langgraph.core
import gym
from gym import spaces

from pedalboard import Pedalboard, Compressor, HighShelfFilter, Limiter
import lancedb
import onnxruntime as ort

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
ray.init(address="auto", ignore_reinit_error=True, include_dashboard=False)
serve.start(detached=True)

@serve.deployment(num_replicas=24, ray_actor_options={"num_gpus": 0.1})
class SovereignBrain:
    def __init__(self, model_path):
        self.session = ort.InferenceSession(
            model_path,
            providers=["CUDAExecutionProvider"],
            provider_options=[{"device_id": GPU_ID}],
        )

    def __call__(self, dna_vector):
        ort_inputs = {
            self.session.get_inputs()[0].name:
                dna_vector.reshape(1, 64).astype(np.float32)
        }
        return self.session.run(None, ort_inputs)[0].squeeze(0)

SovereignBrain.deploy(MODEL_ONNX_PATH)
brain_handle = SovereignBrain.get_handle()

def query_brain(dna_vec):
    return ray.get(brain_handle.remote(dna_vec))

# =================================================================
# 2. SOVEREIGN RL ENVIRONMENT
# =================================================================
class SovereignAcousticEnv(gym.Env):
    def __init__(self, config):
        self.observation_space = spaces.Box(
            low=-10.0, high=10.0, shape=(64,), dtype=np.float32
        )
        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(12,), dtype=np.float32
        )

        self.db = lancedb.connect(LANCEDB_PATH)
        self.table = self.db.open_table("gold_baselines")

        self.board = Pedalboard()
        self.current_step = 0
        self.max_steps = 100

    def reset(self, *, seed=None, options=None):
        self.current_step = 0
        obs = np.zeros(64, dtype=np.float32)
        return obs, {}

    def step(self, action):
        gen_dna = np.random.uniform(-1, 1, 64).astype(np.float32)

        brain_out = query_brain(gen_dna)
        dsp_params = brain_out + action

        self.board = Pedalboard([
            Compressor(
                threshold_db=dsp_params[0] * 20.0,
                ratio=4.0 + dsp_params[1] * 10.0
            ),
            HighShelfFilter(
                cutoff_frequency_hz=8000.0,
                gain_db=dsp_params[2] * 12.0
            ),
            Limiter(threshold_db=-0.3)
        ])

        results = self.table.search(gen_dna).limit(1).to_pandas()
        l2_distance = float(results["_distance"][0]) if not results.empty else 10.0

        reward = -l2_distance
        if l2_distance > 5.0:
            reward -= 5.0

        self.current_step += 1
        terminated = self.current_step >= self.max_steps
        truncated = False

        return gen_dna, reward, terminated, truncated, {}

# =================================================================
# 3. RLLIB TRAINING CONFIGURATION
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