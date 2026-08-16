import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, IsolationForest

# Force early UTF-8 configuration to prevent Windows terminal encoding crashes
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Try importing ONNX conversion libraries
try:
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import FloatTensorType
    HAS_ONNX_CONVERTER = True
except ImportError:
    HAS_ONNX_CONVERTER = False

def scan_workspace_directory(workspace_path: str, source_label: str) -> pd.DataFrame:
    """
    Recursively scans the real filesystem of your workstation, capturing actual 
    file sizes, code line counts (rows), extensions, and source paths.
    Bypasses empty directories, virtual environments, and git histories.
    """
    print(f"🔍 [FOREST SCANNER] Actively walking physical disk path: {workspace_path}...")
    records = []
    ignored_patterns = [".venv", "node_modules", ".git", "__pycache__", ".continue", "AppData", "Temp"]
    
    root_path = Path(workspace_path)
    if not root_path.exists():
        print(f"⚠️  [FOREST SCANNER] Path does not exist on disk: {workspace_path}. Skipping physical scan.")
        return pd.DataFrame(columns=['filename', 'size_kb', 'rows', 'source', 'ext'])

    for p in root_path.rglob("*"):
        try:
            # Skip directories and ignored directory branches
            if p.is_dir() or any(ignored in p.parts for ignored in ignored_patterns):
                continue
                
            stat = p.stat()
            size_kb = stat.st_size / 1024.0
            ext = p.suffix.lower() if p.suffix else ".no_ext"
            
            # Programmatically calculate real row count for text/source files
            rows = 0
            if ext in [".py", ".json", ".jsonl", ".csv", ".txt", ".md", ".yaml", ".yml", ".ts", ".tsx"]:
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        rows = sum(1 for _ in f)
                except Exception:
                    pass # Fallback for locked or unreadable files
            
            records.append({
                "filename": p.name,
                "size_kb": size_kb,
                "rows": rows,
                "source": source_label,
                "ext": ext
            })
        except Exception:
            continue # Safe-guard against dynamic Win32 system locks
            
    df = pd.DataFrame(records)
    print(f"✅ [FOREST SCANNER] Scan complete. Found {len(df)} physical file footprints under {source_label}.")
    return df

def main():
    print("=" * 80)
    print("🌲 CODE FOREST ENGINE: PHYSICAL WORKSPACE DATA INGESTION & TRAINING")
    print("=" * 80)

    # 1. Physical Location Defs
    WORKSPACE_C = r"C:\WEB CASE STUDY"
    WORKSPACE_STUDIES = r"C:\STUDIES"
    ONNX_OUTPUT_PATH = r"C:\WEB CASE STUDY\mastered_output\code_genome_brain.onnx"

    # 2. Attempt loading existing parquet audits (pre-compiled metrics)
    df_code = None
    df_nb = None
    
    # Code Audit Parquet Ingestion
    parquet_code_path = Path(WORKSPACE_C) / "code_knowledge_audit.parquet"
    if parquet_code_path.exists():
        try:
            df_code = pd.read_parquet(parquet_code_path)
            df_code['source'] = 'code'
            print(f"📥 Loaded existing Code Audit Parquet: {len(df_code)} records.")
        except Exception as e:
            print(f"⚠️  Could not read code_knowledge_audit.parquet: {e}")
            
    # Notebook Audit Parquet Ingestion
    parquet_nb_path = Path(WORKSPACE_C) / "notebook_knowledge_audit.parquet"
    if parquet_nb_path.exists():
        try:
            df_nb = pd.read_parquet(parquet_nb_path)
            df_nb['source'] = 'notebook'
            print(f"📥 Loaded existing Notebook Audit Parquet: {len(df_nb)} records.")
        except Exception as e:
            print(f"⚠️  Could not read notebook_knowledge_audit.parquet: {e}")

    # 3. Dynamic disk fallback: If parquets are missing or thin, scan physical workspaces
    if df_code is None or len(df_code) == 0:
        df_code = scan_workspace_directory(WORKSPACE_C, "web_case_study")
    if df_nb is None or len(df_nb) == 0:
        df_nb = scan_workspace_directory(WORKSPACE_STUDIES, "studies")

    # Audio Shards Ingestion (JSONL globbing)
    df_shards = pd.DataFrame(columns=['filename', 'size_kb', 'rows', 'source', 'ext'])
    shard_dir = Path(WORKSPACE_C) / "ray_cat_shards"
    if shard_dir.exists():
        print(f"🔍 Loading audio footprints from Ray Cat Shards: {shard_dir}...")
        shard_dfs = []
        for f in shard_dir.glob("*.jsonl"):
            try:
                sdf = pd.read_json(f, lines=True)
                shard_dfs.append(sdf)
            except Exception as e:
                print(f"   [-] Skipping shard {f.name}: {e}")
        if shard_dfs:
            df_shards = pd.concat(shard_dfs, ignore_index=True)
            df_shards['size_kb'] = df_shards.get('size_bytes', 0) / 1024.0
            df_shards['rows'] = 0  # Audio waveforms have no code rows
            df_shards['source'] = 'audio_shard'
            df_shards['ext'] = '.wav' # Target class mapping
            print(f"📥 Loaded {len(df_shards)} audio shard records from JSONL.")

    # 4. Unify physical data frames into one coherent Code Genome Dataset
    all_dfs = [df_code, df_nb, df_shards]
    valid_dfs = [d for d in all_dfs if d is not None and not d.empty]
    
    if not valid_dfs:
        print("❌ ERROR: No physical files or Parquet audits found. Ingestion aborted.")
        sys.exit(1)
        
    df_unified = pd.concat(valid_dfs, ignore_index=True)
    print(f"📊 Dataset Unification Completed. Total records registered in RAM: {len(df_unified)}")

    # Ensure extension column exists
    if 'ext' not in df_unified.columns:
        df_unified['ext'] = df_unified['filename'].apply(lambda x: os.path.splitext(str(x))[1].lower() if '.' in str(x) else '.no_ext')

    # Drop records with invalid extensions or sizes to prevent skew
    df_clean = df_unified.dropna(subset=['size_kb', 'rows', 'ext', 'source']).copy()

    # 5. Label Encoding and Feature Engineering
    print("[*] Encoding categorical system features...")
    le_ext = LabelEncoder()
    le_source = LabelEncoder()
    
    df_clean['encoded_ext'] = le_ext.fit_transform(df_clean['ext'])
    df_clean['encoded_source'] = le_source.fit_transform(df_clean['source'])

    X = df_clean[['size_kb', 'rows', 'encoded_ext', 'encoded_source']].values
    y = df_clean['encoded_ext'].values

    # Fit scaling transforms on actual data limits
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 6. Unsupervised Anomaly Detection (Isolation Forest)
    print("[*] Fitting Isolation Forest on real codebase topology...")
    iso = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
    df_clean['anomaly'] = iso.fit_predict(X_scaled)
    
    anomalies = df_clean[df_clean['anomaly'] == -1]
    print(f"🚨 Isolation Forest flagged {len(anomalies)} structural anomalies (bloated/corrupt files).")
    if not anomalies.empty:
        example = anomalies.iloc[0]
        print(f"   -> Top Anomaly Spot: {example['filename']} | Size: {example['size_kb']:.2f} KB | Rows: {example['rows']} | Source: {example['source']}")

    # 7. Supervised Class Genome Mapping (Random Forest)
    print("[*] Fitting Random Forest Genome Class Classifier...")
    rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    rf.fit(X_scaled, y)
    accuracy = rf.score(X_scaled, y)
    print(f"✅ Training Success. Random Forest accuracy on actual code dataset: {accuracy*100:.2f}%")

    # 8. Export Serialized Model to ONNX Graph
    if HAS_ONNX_CONVERTER:
        print(f"[*] Exporting trained Random Forest to ONNX Code Genome: {ONNX_OUTPUT_PATH}...")
        try:
            os.makedirs(os.path.dirname(ONNX_OUTPUT_PATH), exist_ok=True)
            # Define input node format matching [size_kb, rows, encoded_ext, encoded_source]
            initial_type = [('code_footprint_input', FloatTensorType([None, X_scaled.shape[1]]))]
            onnx_model = convert_sklearn(rf, initial_types=initial_type)
            
            with open(ONNX_OUTPUT_PATH, "wb") as f:
                f.write(onnx_model.SerializeToString())
            print(f"💎 SUCCESS: Real Code Genome model written to disk!")
        except Exception as onnx_err:
            print(f"❌ Failed to compile ONNX graph: {onnx_err}")
    else:
        print("⚠️  Notice: 'skl2onnx' is missing under this runtime environment. Skipping physical ONNX serialization.")
        print("Run 'pip install skl2onnx' to compile the actual .onnx file to disk.")

if __name__ == "__main__":
    main()
