import sys
import os

modules_to_check = [
    "ray_code_swarm",
    "ray_arrow_swarm",
    "cell_30_clean",
    "fretflow_ray_gen",
    "dsp_alignment_actor",
    "intelligence_bridge",
    "ollama_rag_indexer",
    "omni_vae_generator",
    "sovereign_engine",
    "starlette_exporter",
    "sovereign_serve_app"
]

print("--- Checking Module Existence ---")
for mod in modules_to_check:
    try:
        # We use importlib to check existence without polluting the current process namespace
        import importlib
        importlib.import_module(mod)
        print(f"✅ {mod}: OK")
    except ImportError as e:
        print(f"❌ {mod}: NOT FOUND ({e})")
    except SyntaxError as e:
        print(f"❌ {mod}: SYNTAX ERROR ({e})")
    except Exception as e:
        print(f"⚠️ {mod}: ERROR ({type(e).__name__}: {e})")

print("\n--- Checking Module Syntax via Compile ---")
for mod in modules_to_check:
    try:
        # This is a safer way to check syntax without executing code
        # We find the file first
        found = False
        for root, dirs, files in os.walk("C:\WEB CASE STUDY"):
            if f"{mod}.py" in files:
                path = os.path.join(root, f"{mod}.py")
                with open(path, 'r', encoding='utf-8') as f:
                    source = f.read()
                compile(source, path, 'exec')
                print(f"✅ {mod}: SYNTAX OK")
                found = True
                break
        if not found:
            print(f"❌ {mod}: FILE NOT FOUND")
    except SyntaxError as e:
        print(f"❌ {mod}: SYNTAX ERROR at line {e.lineno}")
    except Exception as e:
        print(f"⚠️ {mod}: ERROR ({type(e).__name__}: {e})")
