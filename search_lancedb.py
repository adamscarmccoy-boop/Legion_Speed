import lancedb
import requests

def get_embedding(text):
    response = requests.post(
        "http://localhost:1234/v1/embeddings",
        json={"input": [text], "model": "text-embedding-snowflake-arctic-embed-l-v2.0"}
    )
    return response.json()["data"][0]["embedding"]

def search_db(db_path, query):
    print(f"\nScanning Database: {db_path}")
    try:
        db = lancedb.connect(db_path)
        tables = db.table_names()
        for table_name in tables:
            print(f"  -> Searching table: {table_name}")
            try:
                table = db.open_table(table_name)
                query_vec = get_embedding(query)
                results = table.search(query_vec).limit(3).to_pandas()
                for idx, row in results.iterrows():
                    d = row.get('_distance', 999)
                    if d < 1.5: # Print semantic matches
                        print(f"      [Match] Dist: {d:.3f} | {row.to_dict()}")
            except Exception as e:
                pass
    except Exception as e:
        pass

if __name__ == "__main__":
    query = "diffusers"
    dbs = [
        r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag",
        r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_highres_audio_rag",
        r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_omni_snowflake_rag",
        r"C:\WEB CASE STUDY\lancedb_memory",
        r"C:\WEB CASE STUDY\rag-v1",
        r"C:\STUDIES_BACKUP\vectors\lancedb_store"
    ]
    for d in dbs:
        search_db(d, query)
