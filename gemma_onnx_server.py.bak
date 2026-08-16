import os
import sys
import time
import json
import traceback
import ray
from typing import List, Dict

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


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ─── GEMMA ONNX ACTOR DEFINITION ───

@ray.remote(num_cpus=4)
class GemmaONNXAgent:
    """
    Durable, detached Ray Actor that runs the local google/gemma-2-2b-it ONNX model on CPU.
    Robustly handles initialization and generation errors.
    """
    def __init__(self):
        print("[*] Starting GemmaONNXAgent inside Ray worker...")
        import onnxruntime_genai as og
        model_path = r"C:\WEB CASE STUDY\gemma_onnx"
        self.model = og.Model(model_path)
        self.tokenizer = og.Tokenizer(self.model)
        print("[+] GemmaONNXAgent initialized successfully.")

    def ping(self) -> str:
        return "GemmaONNXAgent is online."

    def generate(self, messages: List[Dict[str, str]], system_prompt: str) -> str:
        """Runs local generation on the cached model weights with strict error boundaries."""
        if self.model is None or self.tokenizer is None:
            return "ERROR: Agent model/tokenizer not loaded."

        try:
            import onnxruntime_genai as og
            print(f"[*] Generating response for {len(messages)} messages...")
            prompt_parts = []
            
            # Inject system prompt + schema instructions
            first_user_injected = False
            for m in messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                
                if role == "system":
                    continue # Handled by system_prompt parameter prefix
                elif role == "user":
                    if not first_user_injected:
                        content = f"{system_prompt}\n\nUser Question: {content}"
                        first_user_injected = True
                    prompt_parts.append(f"<start_of_turn>user\n{content}<end_of_turn>\n")
                elif role == "assistant":
                    prompt_parts.append(f"<start_of_turn>model\n{content}<end_of_turn>\n")

            prompt_parts.append("<start_of_turn>model\n")
            full_prompt = "".join(prompt_parts)

            # Tokenize input safely
            try:
                input_tokens = self.tokenizer.encode(full_prompt)
            except Exception as tokenize_err:
                print(f"[ERROR] Tokenization failed: {tokenize_err}")
                print(traceback.format_exc())
                return f"ERROR: Prompt tokenization failed: {tokenize_err}"

            # Create generator parameters safely
            try:
                params = og.GeneratorParams(self.model)
                params.set_search_options(max_length=1024, temperature=0.1)
                generator = og.Generator(self.model, params)
                generator.append_tokens(input_tokens)
            except Exception as gen_init_err:
                print(f"[ERROR] Generator setup failed: {gen_init_err}")
                print(traceback.format_exc())
                return f"ERROR: Generator initialization failed: {gen_init_err}"

            # Generate tokens loop with safety catch
            print("[*] Generating tokens...")
            try:
                while not generator.is_done():
                    generator.generate_next_token()
                    # Explicit check for EOS token (1) to prevent CPU infinite loop hangs
                    if generator.get_last_token_id() == 1:
                        break
            except Exception as loop_err:
                print(f"[ERROR] Token generation loop failed: {loop_err}")
                print(traceback.format_exc())
                return f"ERROR: Execution loop broke: {loop_err}"

            # Decode output tokens safely
            try:
                output_tokens = generator.get_sequence(0)
                # Ensure we get the actual sequence length, not the batch size (which is 1)
                input_len = 0
                if hasattr(input_tokens, 'size'):
                    input_len = input_tokens.size()
                elif hasattr(input_tokens, '__len__'):
                    if len(input_tokens) > 0 and isinstance(input_tokens[0], (list, tuple)):
                        input_len = len(input_tokens[0])
                    else:
                        input_len = len(input_tokens)
                
                if len(output_tokens) > input_len:
                    response_text = self.tokenizer.decode(output_tokens[input_len:])
                else:
                    response_text = self.tokenizer.decode(output_tokens)
                
                print("[+] Generation completed successfully.")
                return response_text.strip()
            except Exception as decode_err:
                print(f"[ERROR] Token decoding failed: {decode_err}")
                print(traceback.format_exc())
                return f"ERROR: Token decoding failed: {decode_err}"

        except Exception as outer_err:
            print(f"[ERROR] Outer exception in generate: {outer_err}")
            print(traceback.format_exc())
            return f"ERROR: Generation failed: {outer_err}"

# ─── DAEMON BOOT SEQUENCE ───

def main():
    print("=== Initializing Gemma ONNX Ray Swarm Server ===")
    
    if "RAY_ADDRESS" in os.environ:
        del os.environ["RAY_ADDRESS"]
        
    if not ray.is_initialized():
        try:
            ray.init(address="auto", namespace="legion")
            print("[*] Joined existing Ray cluster.")
        except Exception:
            print("[*] Booting fresh local Ray cluster...")
            ray.init(
                namespace="legion", 
                object_store_memory=1500 * 1024 * 1024,
                num_cpus=os.cpu_count() or 4
            )

    try:
        # Check if already running
        agent = ray.get_actor("GemmaONNXAgent", namespace="legion")
        print("[+] GemmaONNXAgent is already running and cached in the cluster.")
    except ValueError:
        print("[*] Spawning GemmaONNXAgent as a detached actor in Ray namespace 'legion'...")
        agent = GemmaONNXAgent.options(
            name="GemmaONNXAgent", 
            namespace="legion", 
            lifetime="detached",
            num_cpus=4
        ).remote()
        
        # Trigger initial loading of weights synchronously
        print("[*] Triggering weight load via ping...")
        try:
            print(ray.get(agent.ping.remote(), timeout=300))
        except Exception as e:
            print(f"[!!!] TIMEOUT/FAILURE during weight load: {str(e)}")

    print("[+] Server ready.")
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("[-] Server exit.")

if __name__ == "__main__":
    main()