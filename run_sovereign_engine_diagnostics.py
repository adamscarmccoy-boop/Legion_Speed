import sys
import os
import json

# Add repository to sys.path
sys.path.append(r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline")

from sovereign_engine import SovereignEngine

DB_PATH = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\AI_Logs\sonic_core_v2.duckdb"

def run_diagnostics():
    print("=== DEPLOYING SOVEREIGN CATALOG INTELLIGENCE ENGINE ===")
    print("Loading sonic_core_v2 database...")
    
    # Initialize Engine
    engine = SovereignEngine(DB_PATH)
    print(f"Engine booted successfully in {engine.boot_ms:.1f} ms!")
    print(f"Catalog contains: {len(engine.af)} tracks | {len(engine.numeric)} physics features")
    print(f"Current Catalog Health Score: {engine.catalog_stats()['health_score']}/100")
    print("-" * 60)
    
    # Target tracks to analyze
    target_queries = [
        "Somebody (2024)",
        "Lorenzo",
        "Stussy"
    ]
    
    for q in target_queries:
        print(f"\n[DIAGNOSING QUERY: '{q}']")
        res = engine.analyze(q, depth=41)
        
        if "error" in res:
            print(f"  [ERROR] {res['error']}")
            continue
            
        print(f"  Track Matched : {res['filename']}")
        print(f"  Severity Group: {res['severity']} (Confidence: {res['confidence']*100:.1f}%)")
        print(f"  Loudness (RMS): {res['rms_db']:.2f} dB (Delta from target: {res['rms_delta']:+.2f} dB)")
        print(f"  Crest Factor  : {res['crest_factor']:.2f} (Delta from target: {res['crest_delta']:+.2f})")
        print(f"  Key/Tempo     : {res['key']} | {res['tempo']} BPM")
        print(f"  Outlier Status: {'ANOMALY DETECTED' if res['is_outlier'] else 'NORMAL RANGE'}")
        
        print("\n  Nearest Neighbors in Feature Space:")
        for idx, n in enumerate(res["neighbors"][:3]):
            print(f"    {idx+1}. {n['filename'][:50]} (Distance: {n['distance']:.3f} | Align: {n['alignment']:.1f}%)")
            
        print("\n  Engine Mixing & Mastering Recommendations:")
        for rec in res["fx_recommendation"]:
            print(f"    -> {rec}")
        print("-" * 60)
        
    print("\n[GROUP DIAGNOSIS FOR ALL 'BASS' TRACKS]")
    bass_diag = engine.diagnose("BASS")
    print(f"  Total Bass tracks: {bass_diag['count']}")
    print(f"  Prescriptions:")
    for p in bass_diag["prescription"]:
        print(f"    -> {p}")
        
if __name__ == "__main__":
    run_diagnostics()
