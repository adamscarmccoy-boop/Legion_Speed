import ray
import pandas as pd

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
registry = ray.get_actor('SwarmKnowledgeRegistry', namespace='legion')
summary = ray.get(registry.get_registered_tables_summary.remote())

results = []
print(f'Searching {    len(summary)} tables...')
for name in summary.keys():
    tbl = ray.get(registry.get_table.remote(name))
    df = tbl.to_pandas()
    string_cols = df.select_dtypes(include=['object']).columns
    for col in string_cols:
        mask = df[col].astype(str).str.contains('DNA ADAMSCARMCCOY', case=False, na=False)
        if mask.any():
            matched_texts = df[mask][col].astype(str).tolist()
            for text in matched_texts:
                results.append((name, col, text[:300]))

if results:
    print('\nFound mentions in:')
    # Deduplicate print
    seen = set()
    for t in results:
        if t[2] not in seen:
            print(f'Table: {t[0]}, Col: {t[1]}\nSnippet: {t[2]}...\n')
            seen.add(t[2])
else:
    print('Not found')