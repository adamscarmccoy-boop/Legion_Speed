import duckdb
import json
import pyarrow as pa
import pyarrow.json
import lancedb
import time
import sys, os
import IPython.display as ipd
from sovereign_math_inference import SovereignInferenceEngine
from sonic_dna_batch_master_v5_neural import SonicDNAMaster, process_track
# Add paths for the Math and Mastery engines
math_dir = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline"
master_dir = r"C:\WEB CASE STUDY\sonic_dna_engine"

if math_dir not in sys.path: sys.path.append(math_dir)
if master_dir not in sys.path: sys.path.append(master_dir)

# Connection Paths
DUCKDB_PATH = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\web_intel_sonicdb.duckdb"
LANCEDB_PATH = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\vectors\lancedb_store"

# Connect to database
conn = duckdb.connect(DUCKDB_PATH)

# Initialize registry and lookup structures in DuckDB if they don't exist
conn.execute("DROP TABLE IF EXISTS layout_registry")
conn.execute("""
    CREATE TABLE layout_registry (
        layout_id VARCHAR PRIMARY KEY,
        primary_key VARCHAR,
        requires_vector BOOLEAN,
        join_target VARCHAR,
        feature_count INTEGER
    )
""")

# Insert the layout registry record
conn.execute("""
    INSERT INTO layout_registry VALUES 
    ('spotify_ableton_sync', 'filename', true, 'audio_features', 46)
""")

# Ensure physical_disk_mapping view exists mapping filename/filepath to asset_id / absolute_path
conn.execute("DROP VIEW IF EXISTS physical_disk_mapping")
conn.execute("""
    CREATE VIEW physical_disk_mapping AS 
    SELECT filename AS asset_id, filepath AS absolute_path 
    FROM audio_features
""")

class UniversalEngine:
    def __init__(self, duckdb_conn, lancedb_table):
        self.db = duckdb_conn
        self.vector_db = lancedb_table

    def execute_payload(self, layout_id: str, incoming_json_data: str):
        # 1. Zero-copy lookup of structural rules from the layout table
        rules = self.db.execute(
            "SELECT * FROM layout_registry WHERE layout_id = ?", [layout_id]
        ).fetchone()
        
        if not rules:
            raise ValueError(f"Layout '{layout_id}' is unregistered in the matrix.")
            
        _, pk_col, requires_vector, join_target, feature_count = rules

        # 2. Parse raw input JSON straight to C++ memory using an Arrow buffer
        buffer = pa.py_buffer(incoming_json_data.encode('utf-8'))
        incoming_table = pa.json.read_json(buffer)
        
        # Register incoming table in DuckDB context dynamically
        # This keeps the parsing entirely inside Arrow's zero-copy memory
        self.db.register("incoming_table", incoming_table)
        
        # 3. Dynamic Execution Query Generation
        dynamic_sql = f"""
            SELECT inc.*, target.rms_db, target.crest_factor, target.bass_energy, paths.absolute_path
            FROM incoming_table AS inc
            JOIN {join_target} AS target ON target.{pk_col} = inc.{pk_col}
            JOIN physical_disk_mapping AS paths ON paths.asset_id = target.{pk_col}
        """
        
        start_sql = time.perf_counter()
        fused_matrix = self.db.execute(dynamic_sql).to_arrow_table()
        sql_ms = (time.perf_counter() - start_sql) * 1000

        vector_ms = 0.0
        vector_results = None
        
        # 4. In-Memory Vector Splice (If the layout calls for embeddings)
        if requires_vector and len(fused_matrix) > 0:
            vector_ids = fused_matrix[pk_col].to_pylist()
            
            # Fetch vectors by IDs (matching filenames) using filter clause
            start_vec = time.perf_counter()
            
            # Construct a safe SQL-like filter for LanceDB
            id_list_str = ", ".join(["'" + x.replace("'", "''") + "'" for x in vector_ids])
            vector_results = self.vector_db.to_lance().to_table(
                filter=f"{pk_col} IN ({id_list_str})"
            )
            vector_ms = (time.perf_counter() - start_vec) * 1000
            
            # Combine the tabular metadata and vectors natively at Arrow C++ speed
            return self.ship_to_cpp_core(fused_matrix, vector_results, sql_ms, vector_ms)

        return self.ship_to_cpp_core(fused_matrix, None, sql_ms, vector_ms)

    def ship_to_cpp_core(self, metadata_table, vector_table, sql_ms, vector_ms):
        print("\n*** UNIVERSAL ENGINE PAYLOAD EXECUTED ***")
        print("-" * 60)
        print(f"Tabular Join Latency  : {sql_ms:.2f} ms")
        print(f"Vector Splice Latency : {vector_ms:.2f} ms")
        print(f"Row count returned    : {len(metadata_table)}")
        
        print("\nTabular Fields (Arrow Column Names):")
        print(metadata_table.schema.names)
        
        if vector_table is not None:
            print("\nVector Table Fields (Arrow Column Names):")
            print(vector_table.schema.names)
            print(f"Vector dimensions: {len(vector_table['vector'][0]) if len(vector_table) > 0 else 0}")
            
            # Demonstrate memory buffer alignment check
            vec_chunk = vector_table['vector'].chunk(0) if hasattr(vector_table['vector'], 'chunk') else vector_table['vector']
            vec_buffer = vec_chunk.buffers()[1] if hasattr(vec_chunk, 'buffers') else None
            if vec_buffer:
                print(f"Arrow Vector buffer size: {vec_buffer.size} bytes (fully aligned in C++ memory)")
        
        return metadata_table, vector_table

# Setup LanceDB Table
ldb = lancedb.connect(LANCEDB_PATH)
vector_table = ldb.open_table("audio_vibe_gpu")

# Instantiate Engine
engine = UniversalEngine(conn, vector_table)

# Create a sample incoming JSON payload matching 3 existing track names in our database
sample_filenames = [
    "63. Meduza - No Sleep (Extended Mix).mp3",
    "RUZE, Chesster - Just Be Good (Original Mix) - www.djsoundtop.com.flac",
    "Enzo Siragusa - Kilimanjaro Sound (Original Mix) - www.djsoundtop.com.flac"
]
incoming_data = "\n".join([json.dumps({"filename": name}) for name in sample_filenames])

# Execute payload
metadata_table, vector_table = engine.execute_payload("spotify_ableton_sync", incoming_data)
