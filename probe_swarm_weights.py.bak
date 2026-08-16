import ray
import json
import sys

def probe_swarm():
    try:
        # Connect to the existing cluster
        ray.init(address='auto', namespace='legion', ignore_reinit_error=True)
        print("[OK] Connected to Ray cluster.")
        
        # Attempt to find the CodeSwarmKnowledgeRegistry
        try:
            registry = ray.get_actor('CodeSwarmKnowledgeRegistry', namespace='legion')
            print("[OK] Found CodeSwarmKnowledgeRegistry actor.")
            
            # Get the summary of all tables
            summary = ray.get(registry.get_registered_tables_summary.remote())
            print(f"--- Registered Tables ({len(summary)}) ---")
            print(json.dumps(summary, indent=2))
            
            # Now, we look for weight-related paths in any of these tables
            # We'll iterate through the tables and look for common weight extensions
            weight_exts = ['.pt', '.pth', '.onnx', '.bin', '.safetensors', '.ckpt']
            found_weights = []
            
            for table_name in summary.keys():
                try:
                    tbl = ray.get(registry.get_table.remote(table_name))
                    # Check every column for paths
                    for col_name in tbl.schema.names:
                        col_data = tbl.column(col_name).to_pylist()
                        for val in col_data:
                            val_str = str(val)
                            if any(ext in val_str.lower() for ext in weight_exts):
                                found_weights.append(f"[{table_name} | {col_name}] -> {val_str}")
                except Exception as e:
                    print(f"Error scanning table {table_name}: {e}")
            
            if found_weights:
                print("
--- FOUND WEIGHTS IN SWARM ---")
                for w in found_weights:
                    print(w)
            else:
                print("
No weight files found in the registered tables.")
                
        except ValueError:
            print("[ERROR] CodeSwarmKnowledgeRegistry actor not found in 'legion' namespace.")
            # List all actors in the namespace to see what IS there
            try:
                # This is a bit more advanced and might not work in all Ray versions, 
                # but let's try to see what's alive.
                print("Attempting to list all live actors...")
                # Note: ray.list_actors() is not a standard public API in all versions, 
                # but we can try to probe common names.
            except Exception as e:
                print(f"Could not list actors: {e}")
                
    except Exception as e:
        print(f"[CRITICAL] Ray connection failed: {e}")

if __name__ == "__main__":
    probe_swarm()
