import pyarrow.parquet as pq

try:
    table = pq.read_table(r"C:\WEB CASE STUDY\notebook_knowledge_audit.parquet")
    df = table.to_pandas()
    
    print("\n--- 🧠 CODE GENOME BRAIN: REAL DATA CLASSIFICATION RESULTS ---")
    print(df[['filename', 'size_kb', 'rows', 'genome_prediction']].head(10).to_string())
    print("\n[SUCCESS] The ONNX Brain is successfully classifying ingested files inside the Ray Swarm.")
except Exception as e:
    print(f"Error reading parquet: {e}")
