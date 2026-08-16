import requests
import time
import json

# The Relay is the entry point for the neural chain
RELAY_URL = "http://127.0.0.1:8000/neural_relay" # Standard Ray Serve endpoint

def test_latency():
    print("=== SOVEREIGN NEURAL RELAY LATENCY TEST ===")
    
    # Sample payload mimicking a track's Sonic DNA
    # In a real run, this comes from the DNAParserActor
    sample_payload = {
        "track_id": "test_asset_001",
        "dna_vector": [0.1] * 128, # Mock DNA vector
        "target_style": "Ibiza Mainstage",
        "options": {"depth": "high", "verify": True}
    }
    
    try:
        start_time = time.perf_counter()
        response = requests.post(RELAY_URL, json=sample_payload, timeout=10)
        end_time = time.perf_counter()
        
        latency_ms = (end_time - start_time) * 1000
        
        if response.status_code == 200:
            print(f"SUCCESS: Response received in {latency_ms:.2f} ms")
            print("\n--- Response Payload ---")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"FAILED: Server returned status {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    test_latency()
