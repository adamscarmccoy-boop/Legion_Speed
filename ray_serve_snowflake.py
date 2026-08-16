import ray
from ray import serve
from transformers import AutoModel, AutoTokenizer
import torch
import os

# We ensure we don't trip up Ray's python version strictness
os.environ["RAY_ALLOW_SLOW_PYTHON_VERSION_CHECK"] = "1"

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 4})
class SnowflakeEmbeddingAgent:
    def __init__(self, model_id: str = "Snowflake/snowflake-arctic-embed-m"):
        print(f"\n[INIT] Loading {model_id} natively via Safetensors...")
        
        # Initialize the tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        
        # CRITICAL: Force safetensors for zero-copy memory mapping
        self.model = AutoModel.from_pretrained(
            model_id, 
            use_safetensors=True, 
            torch_dtype=torch.float16 # Use half-precision for speed/memory efficiency
        )
        
        # Move to GPU if available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.model.eval()
        
        print(f"[READY] Snowflake loaded successfully on {self.device}!\n")

    def __call__(self, request):
        # Ray serve passes in a Starlette Request object
        text = request.query_params.get("text", "Hello from Ray Serve!")
        
        print(f"[EMBED] Generating embedding for: '{text}'")
        
        # Tokenize and move to the correct device
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate the embedding
        with torch.no_grad():
            outputs = self.model(**inputs)
            
            # Extract the CLS token embedding (standard for Snowflake Arctic Embed)
            embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy().tolist()
            
        return {"embedding": embeddings[0]}

# Build the Ray Serve application
app = SnowflakeEmbeddingAgent.bind()

if __name__ == "__main__":
    print("[BOOT] Starting Ray Serve locally...")
    
    # Run the Ray Serve application
    serve.run(app, route_prefix="/snowflake")
    
    print("\n[READY] Server is live! You can test it in another terminal with:")
    print('   curl "http://127.0.0.1:8000/snowflake?text=Hello+World"\n')
    
    # Keep the main thread alive so Ray Serve keeps running
    import time
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n[STOP] Shutting down Ray Serve...")
            break
