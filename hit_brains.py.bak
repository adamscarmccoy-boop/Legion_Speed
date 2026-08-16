import ray
from ray import serve
import time

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


print("Connecting to Ray cluster...")
ray.init(address="auto", namespace="legion", ignore_reinit_error=True)

print("\n--- Hitting the Sovereign DNA Engine ---")
try:
    # Get a handle to the DNA Engine deployment
    dna_handle = serve.get_app_handle("SovereignDNAEngine")
    
    # Send a payload directly to the deployment
    payload = "c:/WEB CASE STUDY/test_audio/chris_lake_somebody_clip.wav"
    print(f"Sending audio path to DNA Engine: {payload}")
    
    # Remote call
    future = dna_handle.remote(payload)
    result = future.result() # or ray.get(future) depending on Ray version
    
    print("\n[DNA Engine Response]")
    print(f"Extracted a {len(result.get('dna_vector', []))}-dimensional DNA Vector.")
    print("First 5 values of the latent audio vector:")
    print(result.get('dna_vector', [])[:5])
    
except Exception as e:
    print(f"Error hitting DNA Engine: {e}")

print("\n--- Hitting the Full Sovereign Neural Relay ---")
try:
    relay_handle = serve.get_app_handle("SovereignNeuralRelay")
    
    payload = {"filepath": "c:/WEB CASE STUDY/test_audio/chris_lake_somebody_clip.wav"}
    print(f"Sending full extraction & parameter request: {payload}")
    
    future = relay_handle.remote(payload)
    result = future.result()
    
    print("\n[Neural Relay Response]")
    print(result)
except Exception as e:
    print(f"Error hitting Neural Relay: {e}")