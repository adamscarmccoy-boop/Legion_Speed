import lancedb
import requests
import sys

sys.stdout.reconfigure(encoding="utf-8")

query = "RLlib vision"
print(f"Querying embedding for: {query}")
resp = requests.post("http://localhost:1234/v1/embeddings", json={
    "model": "text-embedding-snowflake-arctic-embed-l-v2.0",
    "input": query
})
vec = resp.json()["data"][0]["embedding"]

for db_path in [r"C:\WEB CASE STUDY\lancedb_web_intel_rag", r"C:\WEB CASE STUDY\lancedb_data", r"C:\WEB CASE STUDY\lancedb_store"]:
    try:
        db = lancedb.connect(db_path)
        print(f"\n--- Checking DB: {db_path} ---")
        for table_name in db.table_names():
            print(f"Table: {table_name}")
            try:
                tbl = db.open_table(table_name)
                res = tbl.search(vec).limit(2).to_pandas()
                for idx, row in res.iterrows():
                    content = row.get("text", row.get("content", row.get("semantic_text", "")))
                    print(f"\n[Score: {row.get('_distance', 'N/A')}] Match: {str(content)[:1000]}")
            except Exception as e:
                print(f"Error searching {table_name}: {e}")
    except Exception as e:
        pass
