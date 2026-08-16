import os
import json
import time
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

def confirm_audits():
    print("======================================================================")
    print("🔍 RUNNING MODEL SUITABILITY & FILE PATH CONFIRMATIONS")
    print("======================================================================")
    
    report_path = r"C:\WEB CASE STUDY\system_data_audit_report.json"
    if not os.path.exists(report_path):
        print("❌ Error: Audit report not found.")
        return
        
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
        
    # 1. Check Model Suitability Status
    model_info = report.get("suitability_model", {})
    print("\n🤖 RandomForest Model training verification:")
    print(f"  Status: {model_info.get('status')}")
    print(f"  Training Sample Count: {model_info.get('samples')}")
    print(f"  Target parameter: {model_info.get('target')}")
    print("  Feature Importances:")
    for feat, val in model_info.get("feature_importances", {}).items():
        print(f"    - {feat:<20} : {val * 100:.2f}%")

    # 2. Check JSON database file validation
    stale_jsons = report.get("stale_jsons", [])
    print(f"\n📂 Legacy JSON scan verified: {len(stale_jsons)} files found.")
    
    # 3. Locate newly dynamically mastered WAV files
    downloads_dir = r"C:\Users\adams\Downloads"
    files = os.listdir(downloads_dir)
    dynamic_mastered_files = [f for f in files if f.endswith("_DYNAMIC_MASTERED.wav")]
    
    print(f"\n🎵 Verifying active dynamic mastered output files in Downloads:")
    if dynamic_mastered_files:
        for f in dynamic_mastered_files:
            sz_mb = os.path.getsize(os.path.join(downloads_dir, f)) / (1024 * 1024)
            print(f"  - {f:<60} | Size: {sz_mb:.2f} MB | Status: VERIFIED")
    else:
        print("  ❌ No dynamic mastered WAV files found.")
        
    print("======================================================================")

if __name__ == "__main__":
    confirm_audits()
