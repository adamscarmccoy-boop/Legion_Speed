import requests
import json
import time

RELAY_URL = "http://127.0.0.1:8000/neural_relay"

def verify_brain():
    print("🧠 Testing Sovereign Neural Relay (LangGraph Orchestration)...")
    
    payload = {
        "track_id": "test_verify_001",
        "dna_vector": [0.0] * 128,
        "target_style": "Ibiza Mainstage",
        "options": {"depth": "high", "verify": True}
    }
    
    try:
        start = time.perf_counter()
        response = requests.post(RELAY_URL, json=payload, timeout=30)
        end = time.perf_counter()
        
        if response.status_code == 200:
            print(f"✅ SUCCESS: Brain responded in {(end-start)*1000:.2f} ms")
            data = response.json()
            print("
--- Orchestration Result ---")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ FAILED: Server returned {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    verify_brain()
