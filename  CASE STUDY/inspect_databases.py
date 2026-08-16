import os
import sys
import json

# Disable version check to allow connecting to existing cluster with different Ray version
os.environ["RAY_DISABLE_VERSION_CHECK"] = "1"

try:
    import ray
except ImportError:
    print("Error: Ray is not installed. Please install it by running: pip install ray")
    sys.exit(1)

# Shutdown any existing Ray instance and start a new one to avoid version conflicts
ray.shutdown()
ray.init(namespace="legion", ignore_reinit_error=True)

print("=" * 80)
RAY CLUSTER CONNECTION INFO
print("=" * 80)
print(f"Connected to Ray cluster: {ray.is_initialized}")
print(f"Dashboard URL: http://127.0.0.1:8265")
print()

# List actors in the legion namespace
try:
    actors = ray.list_actors(namespace="legion")
    print(f"Active actors in 'legion' namespace: {len(actors)}")
    for actor in actors:
        print(f"  - {actor.name} (ID: {actor.actor_id.hex()})")
except Exception as e:
    print(f"Error listing actors: {e}")
print()

# Check if SwarmKnowledgeRegistry exists (mentioned as LIVE in manifest)
try:
    registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
    print("✓ Found SwarmKnowledgeRegistry actor")
    
    # Try to get some info from it
    try:
        # This is speculative - we don't know what methods it has
        info = ray.get(registry.get_info.remote()) if hasattr(registry, 'get_info') else "No get_info method"
        print(f"  Registry info: {info}")
    except:
        print("  Could not retrieve detailed info from registry (method may not exist)")
        
except Exception as e:
    print(f"✗ Could not find SwarmKnowledgeRegistry actor: {e}")
print()

# Define database paths to check
DUCKDB_PATHS = [
    r"C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb",
    r"C:\WEB CASE STUDY\web_intel_sonicdb.duckdb",
    r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\web_intel_sonicdb.duckdb"
]

LANCE_DB_PATHS = [
    r"C:\STUDIES_BACKUP\vectors\lancedb_store",
    r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag",
    r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_highres_audio_rag",
    r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_omni_snowflake_rag",
    r"C:\WEB CASE STUDY\lancedb_memory",
    r"C:\WEB CASE STUDY\lancedb_store",
    r"C:\WEB CASE STUDY\lancedb_data"
]

print("=" * 80)
DUCKDB DATABASE INFORMATION
print("=" * 80)

for db_path in DUCKDB_PATHS:
    if os.path.exists(db_path):
        print(f"\n📊 Database: {db_path}")
        print("-" * 60)
        
        @ray.remote
        def inspect_duckdb(path):
            import duckdb
            try:
                con = duckdb.connect(path, read_only=True)
                
                # Get tables
                tables = con.execute("SHOW TABLES").fetchall()
                table_names = [t[0] for t in tables]
                
                result = {
                    "path": path,
                    "tables": table_names,
                    "table_info": {}
                }
                
                # Get info for each table
                for table in table_names[:5]:  # Limit to first 5 tables to avoid too much output
                    try:
                        # Get row count
                        count = con.execute(f"SELECT COUNT(*) FROM \"{table}\"").fetchone()[0]
                        
                        # Get column info
                        columns = con.execute(f"DESCRIBE \"{table}\"").fetchall()
                        column_info = [{"name": c[0], "type": c[1]} for c in columns]
                        
                        # Get sample data (first 2 rows)
                        sample = None
                        try:
                            sample_df = con.execute(f"SELECT * FROM \"{table}\" LIMIT 2").fetchdf()
                            sample = sample_df.to_dict('records') if not sample_df.empty else []
                        except:
                            sample = "Could not retrieve sample"
                        
                        result["table_info"][table] = {
                            "row_count": count,
                            "columns": column_info,
                            "sample": sample
                        }
                    except Exception as e:
                        result["table_info"][table] = {"error": str(e)}
                
                con.close()
                return result
            except Exception as e:
                return {"error": str(e), "path": path}
        
        # Execute the inspection
        try:
            result_ref = inspect_duckdb.remote(db_path)
            result = ray.get(result_ref, timeout=30)
            
            if "error" in result:
                print(f"  ❌ Error: {result['error']}")
            else:
                print(f"  ✓ Successfully connected")
                print(f"  Tables found: {len(result['tables'])}")
                if result['tables']:
                    print(f"  Table names: {', '.join(result['tables'][:10])}{'...' if len(result['tables']) > 10 else ''}")
                    
                    # Show details for first few tables
                    for table_name, info in list(result['table_info'].items())[:3]:
                        if "error" not in info:
                            print(f"\n    Table: {table_name}")
                            print(f"      Rows: {info['row_count']:,}")
                            print(f"      Columns: {len(info['columns'])}")
                            for col in info['columns'][:3]:  # Show first 3 columns
                                print(f"        - {col['name']}: {col['type']}")
                            if len(info['columns']) > 3:
                                print(f"        ... and {len(info['columns']) - 3} more columns")
                            
                            if isinstance(info['sample'], list) and info['sample']:
                                print(f"      Sample rows: {json.dumps(info['sample'], indent=2)[:200]}...")
                            elif info['sample'] != "Could not retrieve sample":
                                print(f"      Sample: {info['sample']}")
                        else:
                            print(f"\n    Table: {table_name} - ERROR: {info['error']}")
                else:
                    print("  No tables found")
                    
        except Exception as e:
            print(f"  ❌ Error during inspection: {e}")
    else:
        print(f"\n📊 Database: {db_path}")
        print("  ❌ File not found")
print()

print("=" * 80)
LANCEDB STORE INFORMATION
print("=" * 80)

for db_path in LANCE_DB_PATHS:
    if os.path.exists(db_path):
        print(f"\n🗄️  LanceDB Store: {db_path}")
        print("-" * 60)
        
        @ray.remote
        def inspect_lancedb(path):
            try:
                import lancedb
                db = lancedb.connect(path)
                table_names = db.table_names()
                
                result = {
                    "path": path,
                    "tables": table_names,
                    "table_info": {}
                }
                
                # Get info for each table
                for table_name in table_names[:5]:  # Limit to first 5 tables
                    try:
                        tbl = db.open_table(table_name)
                        count = tbl.count_rows()
                        
                        # Get schema
                        schema = tbl.schema
                        fields = [{"name": f.name, "type": str(f.type)} for f in schema]
                        
                        # Get sample data (first 2 rows as pandas DF, then convert)
                        try:
                            df = tbl.to_pandas().head(2)
                            sample = df.to_dict('records') if not df.empty else []
                        except:
                            sample = "Could not retrieve sample as pandas DF"
                            
                        result["table_info"][table_name] = {
                            "row_count": count,
                            "schema": fields,
                            "sample": sample
                        }
                    except Exception as e:
                        result["table_info"][table_name] = {"error": str(e)}
                
                return result
            except Exception as e:
                return {"error": str(e), "path": path}
        
        # Execute the inspection
        try:
            result_ref = inspect_lancedb.remote(db_path)
            result = ray.get(result_ref, timeout=30)
            
            if "error" in result:
                print(f"  ❌ Error: {result['error']}")
            else:
                print(f"  ✓ Successfully connected")
                print(f"  Tables found: {len(result['tables'])}")
                if result['tables']:
                    print(f"  Table names: {', '.join(result['tables'])}")
                    
                    # Show details for first few tables
                    for table_name, info in list(result['table_info'].items())[:3]:
                        if "error" not in info:
                            print(f"\n    Table: {table_name}")
                            print(f"      Rows: {info['row_count']:,}")
                            print(f"      Schema fields: {len(info['schema'])}")
                            for field in info['schema'][:3]:  # Show first 3 fields
                                print(f"        - {field['name']}: {field['type']}")
                            if len(info['schema']) > 3:
                                print(f"        ... and {len(info['schema']) - 3} more fields")
                            
                            if isinstance(info['sample'], list) and info['sample']:
                                print(f"      Sample rows (first 2): {json.dumps(info['sample'], indent=2)[:200]}...")
                            elif info['sample'] != "Could not retrieve sample as pandas DF":
                                print(f"      Sample: {info['sample']}")
                        else:
                            print(f"\n    Table: {table_name} - ERROR: {info['error']}")
                else:
                    print("  No tables found")
                    
        except Exception as e:
            print(f"  ❌ Error during inspection: {e}")
    else:
        print(f"\n🗄️  LanceDB Store: {db_path}")
        print("  ❌ Directory not found")
print()

# Shutdown Ray
ray.shutdown()
print("=" * 80)
INSPECTION COMPLETE
print("=" * 80)