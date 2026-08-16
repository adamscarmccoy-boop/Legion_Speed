import importlib
for mod in ['hunt_signal_v2', 'downloads_premaster_audit', 'fire_test', 'marketing_scorer']:
    try:
        m = importlib.import_module(mod)
        attrs = []
        for fn in ['scrape_prospects', 'download_pack', 'run_fire_test', 'score_alignment']:
            if hasattr(m, fn):
                attrs.append(fn)
        print(f"OK   {mod:35s} -> {','.join(attrs)}")
    except Exception as e:
        print(f"FAIL {mod:35s} -> {e}")

# Also check renderer + preflight
import os
for f in ['renderer.py', 'preflight.py']:
    print(f"{f}: exists={os.path.exists(f)} size={os.path.getsize(f) if os.path.exists(f) else 0}")