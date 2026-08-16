"""
Boot the actors that CAN load right now (no LM Studio dependency).
"""
import sys
import ray
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


ray.init(address="auto", namespace="legion", ignore_reinit_error=True)

print("=" * 60)
print("SOVEREIGN STACK BOOT (SAFE MODE)")
print("=" * 60)
print(f"Connected: {ray.is_initialized()}")
print(f"Resources: {ray.cluster_resources()}")

booted = []
failed = []

def boot_actor(name, cls, **kwargs):
    try:
        try:
            existing = ray.get_actor(name, namespace="legion")
            print(f"  [EXISTING] {name}")
            booted.append(name)
            return existing
        except ValueError:
            pass
        actor = cls.options(
            name=name, 
            lifetime="detached", 
            get_if_exists=True
        ).remote(**kwargs)
        print(f"  [BOOTED]   {name}")
        booted.append(name)
        return actor
    except Exception as e:
        print(f"  [FAILED]   {name}: {e}")
        failed.append((name, str(e)))
        return None

# LAYER 0
print("\n--- LAYER 0: SHARED MEMORY ---")
try:
    from ray_arrow_swarm import SwarmKnowledgeRegistry
    boot_actor("SwarmKnowledgeRegistry", SwarmKnowledgeRegistry)
except ImportError as e:
    print(f"  [SKIP] {e}")
    failed.append(("SwarmKnowledgeRegistry", str(e)))

try:
    from ray_code_swarm import CodeSwarmKnowledgeRegistry
    boot_actor("CodeSwarmKnowledgeRegistry", CodeSwarmKnowledgeRegistry)
except ImportError as e:
    print(f"  [SKIP] {e}")
    failed.append(("CodeSwarmKnowledgeRegistry", str(e)))

# LAYER 2: DSP (CPU-only, no external deps)
print("\n--- LAYER 2: DSP ALIGNMENT ---")
try:
    from dsp_alignment_actor import DSPAlignmentActor
    for i in range(4):
        boot_actor(f"DSP_Align_{i}", DSPAlignmentActor, lancedb_path=r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag", table_name="audio_vibe_gpu")
except ImportError as e:
    print(f"  [SKIP] {e}")
    failed.append(("DSPAlignmentActor", str(e)))

# LAYER 3: INTELLIGENCE BRIDGE
print("\n--- LAYER 3: INTELLIGENCE BRIDGE ---")
try:
    from intelligence_bridge import IntelligenceBridge
    boot_actor("IntelligenceBridge", IntelligenceBridge, market_data_path=r"C:\WEB CASE STUDY\Acoustic-DNA-Audio-Engine\data\acoustic_dna_baselines.json")
except ImportError as e:
    print(f"  [SKIP] {e}")
    failed.append(("IntelligenceBridge", str(e)))

try:
    from ollama_rag_indexer import OllamaEmbeddingWorker
    boot_actor("OllamaEmbeddingWorker", OllamaEmbeddingWorker)
except ImportError as e:
    print(f"  [SKIP] {e}")
    failed.append(("OllamaEmbeddingWorker", str(e)))

# REPORT
print("\n" + "=" * 60)
print(f"RESULT: {len(booted)} booted, {len(failed)} failed")
print("=" * 60)

if booted:
    print("\n✓ Live:")
    for name in booted:
        print(f"  {name}")

if failed:
    print("\n✗ Failed:")
    for name, err in failed:
        print(f"  {name}: {err}")

# Skipped actors that need LM Studio:
print("\n--- SKIPPED (need LM Studio on :1234) ---")
print("  EmbedWorker_0..5 (run_vector_rebuild.py calls embeddings on import)")
print("  GenomeBrain (cell_30_clean needs _typeshed)")

print("\n--- RAY VERIFICATION ---")
all_actors = ray.util.list_named_actors(all_namespaces=True)
print(f"Total named actors: {len(all_actors)}")
for a in all_actors:
    print(f"  → {a}")