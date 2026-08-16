import sys, os, json, time
sys.stdout.reconfigure(encoding='utf-8')
# Force flush every print
import functools
print = functools.partial(print, flush=True)

import ray

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

ray.init(address='auto', namespace='legion', ignore_reinit_error=True)

for actor_name in ['SwarmKnowledgeRegistry', 'CodeSwarmKnowledgeRegistry']:
    print(f"\n=== {actor_name} ===")
    try:
        reg = ray.get_actor(actor_name, namespace='legion')
        summary = ray.get(reg.get_registered_tables_summary.remote())
        print(f"Tables: {len(summary)}")
        
        # Just list table names and flag any with "chat" 
        chat_tables = []
        for name in sorted(summary.keys()):
            row_count = summary[name].get('rows', 0)
            cols = summary[name].get('columns', [])
            marker = " <<< CHAT" if 'chat' in name.lower() else ""
            print(f"  {name} ({row_count} rows, cols: {cols[:4]}){marker}")
            if 'chat' in name.lower():
                chat_tables.append(name)
        
        # If we found chat tables, dump them
        for ct in chat_tables:
            print(f"\n--- Dumping table: {ct} ---")
            tbl = ray.get(reg.get_table.remote(ct))
            for row in tbl.to_pylist()[:10]:
                print(f"  {str(row)[:400]}")
                
    except ValueError:
        print(f"  NOT RUNNING")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\nDone.")