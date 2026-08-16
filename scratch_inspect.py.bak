import ray
import os

# ==============================================================================
# SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
# Prevents dangling stdout/stdio pipes and GCS registry locks on Windows exit
# ==============================================================================
import atexit
import signal

def clean_exit_handler(*args, **kwargs):
    import sys
    sys.stderr.write("\n[LMS LIFECYCLE] Exit triggered. Flushing system streams...\n")
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write("[LMS LIFECYCLE] Active Ray session detected. Disconnecting...\n")
            ray.shutdown()
    except Exception:
        pass
    sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


try:
    ray.init(namespace='legion', ignore_reinit_error=True)
    registry = ray.get_actor('SwarmKnowledgeRegistry', namespace='legion')
    tables = ray.get(registry.list_tables.remote())
    
    for tbl_name in ['audio_vibe_gpu', 'chris_lake_fused_raw', 'legion_memory', 'audio_manifest_vectors', 'enriched_audio_dataset']:
        if tbl_name in tables:
            arrow_table = ray.get(registry.get_table.remote(tbl_name))
            print(f'\n--- {tbl_name} ({arrow_table.num_rows} rows) ---')
            print(arrow_table.schema.names)
            # Safe print to avoid unicode terminal errors
            rows = arrow_table.slice(0, 1).to_pylist()
            print(str(rows).encode('ascii', 'replace').decode('ascii'))
except Exception as e:
    print(f"Error: {e}")