import os
import sys
import duckdb
from duckdb import DuckDBPyConnection

# Core database paths as established in your local master catalog
DB_PATH = r"C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb"

def create_duckdb_view(con: DuckDBPyConnection, view_name: str, query: str) -> None:
    """
    Autonomously creates or heals a view inside your local DuckDB catalog.
    If a BinderException occurs due to legacy 'source_type' references, it self-heals
    the query structure by mapping to the verified 'asset_type' column.
    """
    print(f"🛠️ Attempting to compile view: {view_name}...")
    try:
        # Standard creation block
        con.execute(f"CREATE OR REPLACE VIEW {view_name} AS {query}")
        print(f"🟢 SUCCESS: View '{view_name}' compiled cleanly.")
    except duckdb.BinderException as e:
        error_msg = str(e)
        print(f"⚠️ Binder Error caught: {error_msg}")
        
        # Self-healing logic for the source_type / asset_type mapping conflict
        if 'referenced column "source_type" not found' in error_msg.lower() or '"source_type"' in error_msg.lower():
            print("🧬 Self-healing active: Remapping legacy 'source_type' -> 'asset_type'...")
            healed_query = query.replace("source_type", "asset_type")
            try:
                con.execute(f"CREATE OR REPLACE VIEW {view_name} AS {healed_query}")
                print(f"🟢 SUCCESS: Healed view '{view_name}' successfully compiled using 'asset_type'!")
            except Exception as inner_err:
                print(f"❌ Failed compile on healed query: {inner_err}")
                raise inner_err
        else:
            raise e

def heal_audio_lanes():
    print("=" * 70)
    print("🏛️  AUTONOMOMIC LANE HEALER: REPAIRING SCHEMAS & VIEWS")
    print("=" * 70)
    
    if not os.path.exists(DB_PATH):
        print(f"⚠️ Warning: Database file not found at local path: {DB_PATH}")
        print("Creating an in-memory test database for validation...")
        con = duckdb.connect(database=":memory:")
        # Seed dummy audio_features table to validate compiling logic
        con.execute("""
            CREATE TABLE audio_features (
                filepath VARCHAR,
                filename VARCHAR,
                asset_type VARCHAR,
                drum_type VARCHAR,
                tempo FLOAT,
                crest_factor FLOAT
            )
        """)
    else:
        print(f"🔌 Connecting to local DuckDB database: {DB_PATH}")
        con = duckdb.connect(database=DB_PATH, read_only=False)

    # 1. Test Query exhibiting the legacy source_type BinderError
    broken_query = """
        SELECT filepath, filename, source_type, drum_type, tempo, crest_factor 
        FROM audio_features 
        WHERE crest_factor < 5.69
    """
    
    # 2. Compile view (this triggers the self-healing block)
    try:
        create_duckdb_view(con, "ableton_audio_matched", broken_query)
    except Exception as err:
        print(f"❌ Autonomic Lane Healer failed to resolve view compile: {err}")
        sys.exit(1)
        
    print("\n[ VIEW SCHEMA VERIFICATION ]")
    try:
        schema_info = con.execute("DESCRIBE ableton_audio_matched").fetchdf()
        print(schema_info[['column_name', 'column_type']].to_string(index=False))
        print("=" * 70)
        print("🟢 AUTONOMOUS HEALING SEQUENCE SECURED: DATABASE VIEWS COMPILED CLEANLY")
        print("=" * 70)
    except Exception as verify_err:
        print(f"❌ Verification failed: {verify_err}")

if __name__ == "__main__":
    heal_audio_lanes()
