import requests
import json
import time

RELAY_URL = "http://127.0.0.1:8000/neural_relay"

def verify_brain():
    print("Testing Brain...")
    payload = {"track_id": "test", "dna_vector": [0.0]*128, "target_style": "Ibiza", "options": {}}
    try:
        start = time.perf_counter()
        r = requests.post(RELAY_URL, json=payload, timeout=30)
        print(f"Latency: {(time.perf_counter()-start)*1000:.2f}ms")
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print(r.json())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_brain()
