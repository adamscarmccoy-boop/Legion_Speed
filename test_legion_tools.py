import json
import os
from legion_graph import (
    list_available_data,
    analyze_parquet_data,
    search_vibe_vectors,
)

def run_tests():
    print("=" * 60)
    print("1. Testing list_available_data()")
    print("=" * 60)
    try:
        data_inv = list_available_data.invoke({})
        inv_json = json.loads(data_inv)
        print(json.dumps(inv_json, indent=2))
    except Exception as e:
        print(f"Error executing list_available_data: {e}")

    print("\n" + "=" * 60)
    print("2. Testing analyze_parquet_data()")
    print("=" * 60)
    try:
        parquet_res = analyze_parquet_data.invoke({
            "query": "SELECT * FROM data LIMIT 3",
            "parquet_file": "collision_results_final.parquet"
        })
        print(parquet_res)
    except Exception as e:
        print(f"Error executing analyze_parquet_data: {e}")

    print("\n" + "=" * 60)
    print("3. Testing search_vibe_vectors()")
    print("=" * 60)
    try:
        vector_res = search_vibe_vectors.invoke({
            "search_text": "cybernetic synth bassline",
            "table_name": "audio_vibe_gpu",
            "top_k": 3,
            "store": "v1"
        })
        print(vector_res)
    except Exception as e:
        print(f"Error executing search_vibe_vectors: {e}")

if __name__ == "__main__":
    run_tests()