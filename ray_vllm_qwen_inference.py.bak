import ray
from ray import serve
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.sampling_params import SamplingParams
from fastapi import FastAPI
from pydantic import BaseModel
import asyncio

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


app = FastAPI()

class Query(BaseModel):
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7

@serve.deployment(
    ray_actor_options={"num_gpus": 1}, # Adjust based on hardware
    max_ongoing_requests=50
)
@serve.ingress(app)
class VLLMQwenDeployment:
    def __init__(self, model_id: str):
        print(f"Loading {model_id} into vLLM...")
        # EngineArgs optimized for Qwen 7B
        engine_args = AsyncEngineArgs(
            model=model_id,
            trust_remote_code=True,
            max_model_len=4096, # Reduce if hitting OOM (Qwen can have huge context)
            gpu_memory_utilization=0.9, # Maximize VRAM usage
            tensor_parallel_size=1, # Change to 2 or 4 if you have multiple GPUs
            dtype="auto", # or "half" if getting errors
            enforce_eager=False, # Use CUDA graphs for speed
            disable_log_requests=True
        )
        self.engine = AsyncLLMEngine.from_engine_args(engine_args)

    @app.post("/generate")
    async def generate(self, query: Query):
        request_id = f"req-{asyncio.get_running_loop().time()}"
        sampling_params = SamplingParams(
            temperature=query.temperature,
            max_tokens=query.max_tokens,
            stop=["<|im_end|>", "<|endoftext|>"]
        )
        
        # Async generation
        results_generator = self.engine.generate(
            query.prompt, 
            sampling_params, 
            request_id
        )
        
        final_output = None
        async for request_output in results_generator:
            final_output = request_output
            
        text = final_output.outputs[0].text
        return {"response": text}

if __name__ == "__main__":
    # Start local Ray cluster
    ray.init(ignore_reinit_error=True)
    
    print("Starting Ray Serve...")
    serve.start(http_options={"host": "0.0.0.0", "port": 8000})
    
    # Deploy Qwen 7B (You can change this to your local path or HF repo)
    model_name = "Qwen/Qwen2.5-7B-Instruct" 
    serve.run(VLLMQwenDeployment.bind(model_name), name="qwen_7b", route_prefix="/qwen")
    
    print("\n✅ Deployment Live!")
    print("Test it via: curl -X POST http://localhost:8000/qwen/generate -H 'Content-Type: application/json' -d '{\"prompt\": \"<|im_start|>user\\nHello\\n<|im_end|>\\n<|im_start|>assistant\\n\"}'")
    
    # Keep alive
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        serve.shutdown()