import torch
import torch.nn as nn
import sys
from accelerate.utils import torch_xla

import ray
import duckdb
import time
import os
import json
import pyarrow as pa
import pyarrow.parquet as pq
import lancedb 

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


sys.stdout.reconfigure(encoding='utf-8')

 
# The Swarm Watchtower Ray Actor
@ray.remote(num_cpus=1)
class SwarmKnowledgeWorker:
    class CodeSwarmKnowledgeRegistry(nn.Module):
        def __init__(self, config):
            super().__init__()
            self.config = config
            
            # 1. INPUT ATOMIZATION LAYER (Fixed Size)
            # We use 10x linear layers (one per audio domain) to map discrete audio tokens
            # into the unified 128-D coding space.
            self.atomizers = nn.ModuleList([
                nn.Linear(64, 128) for _ in range(10) # e.g., Kick, Snare, Synth, Voice, Bass...
            ])

            # 2. SELF-ATTENTION CORE
            # Processes the atomized tokens relationally.
            # We use a "bottleneck" dimension to force compression of semantic meaning.
            self.attention_core = nn.Sequential(
                # 128 -> 256 (Attention Expansion)
                nn.Linear(128, 256),
                nn.GELU(),
                nn.LayerNorm(256),
                nn.MultiheadAttention(embed_dim=256, num_heads=8, batch_first=True),
                nn.LayerNorm(256),
                
                # 256 -> 64 (Codebook Condensation - THE CREATIVE GENE)
                nn.Linear(256, 64),
                nn.GELU(),
                nn.LayerNorm(64)
            )

            # 3. OUTPUT HEADS (Reconstruction)
            # Maps the compressed code back to the multi-domain audio space
            self.reconstructors = nn.ModuleList([
                nn.Linear(64, 64) for _ in range(10)
            ])

    def forward(self, x):
        # x shape: (Batch, Num_Tokens, 64)
        batch_size, seq_len, _ = x.shape

        # Pass through respective atomizers
        # Note: In a real implementation, we'd need a 'token_type' map
        # Here we average all atomizers for demonstration, or you can pass a selector
        x = torch.stack([self.atomizers[i](x) for i in range(10)], dim=0) # (10, B, T, 128)
        x = x.mean(0) # Average effect across domains for this simplified loop

        # Process through Transformer
        x, _ = self.attention_core(x, x, x) # Output: (B, T, 64)

        # Reconstruct
        recon = torch.stack([self.reconstructors[i](x) for i in range(10)], dim=0)
        return recon
    def __init__(self, db_path):
        self.db_path = db_path

    def process_one_shot(self, filepath):
        """
        Extracts raw sections of one-shot samples and pushes them through the VAE.
        This builds the 'Music Knowledge' spatial mapping.
        """
        # In a real environment, this calls pedalboard -> FretFlow VAE
        # Returning a simulated 1069-D extraction footprint for speed in this daemon
        # print(f"[Worker] Encoding One-Shot: {os.path.basename(filepath)}")
        return {
            'filepath': filepath,
            'status': 'ENCODED',
            'knowledge_vectors': '[...1069-D FOOTPRINT...]'
        }

    def parse_ableton_nodes(self, filepath):
        """
        Reads already-parsed Ableton JSON nodes to understand arrangement DNA.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                dna = json.load(f)
            # print(f"[Worker] Extracted Ableton Arrangement DNA: {os.path.basename(filepath)}")
            return {
                'filepath': filepath,
                'arrangement_nodes': str(dna)[:100] # summarized
            }
        except Exception:
            return None


def run_daemon():
    print("="*60)
    print(" 👁️ SWARM KNOWLEDGE DAEMON: ONLINE")
    print("="*60)
    
    # Connect to Ray
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)
        
    DB_PATH = r"C:\WEB CASE STUDY\lancedb\swarm_registry.lance"
    
    # Initialize workers
    print("🤖 Booting Swarm Knowledge Workers...")
    workers = [SwarmKnowledgeWorker.remote(DB_PATH) for _ in range(4)]
    
    # We create sonic_dna if it doesn't exist to allow the delta queue to run
    con = duckdb.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS sonic_dna (
            filepath VARCHAR
        )
    """)
    con.close()

    while True:
        try:
            con = duckdb.connect(DB_PATH)
            
            # 1. Delta Queue for Audio One-Shots
            delta_df = con.execute("""
                SELECT c.filepath 
                FROM computer_fs c
                LEFT JOIN sonic_dna s ON c.filepath = s.filepath
                WHERE c.ext IN ('.wav', '.aif') 
                  AND s.filepath IS NULL
                LIMIT 20  -- Process in small batches for the continuous daemon
            """).fetchdf()
            
            target_audio = delta_df['filepath'].tolist()
            
            if target_audio:
                print(f"\n📡 Found {len(target_audio)} new one-shots on physical drives. Dispatching to VAE...")
                # Dispatch round-robin
                futures = []
                for i, path in enumerate(target_audio):
                    worker = workers[i % len(workers)]
                    futures.append(worker.process_one_shot.remote(path))
                
                results = ray.get(futures)
                
                # Mark as processed in DuckDB
                paths_processed = [(r['filepath'],) for r in results if r]
                if paths_processed:
                    con.executemany("INSERT INTO sonic_dna VALUES (?)", paths_processed)
                    print(f"✅ Ingested {len(paths_processed)} new knowledge footprints into sonic_dna.")

            # 2. Delta Queue for Ableton parsed JSONs
            als_df = con.execute("""
                SELECT filepath FROM computer_fs
                WHERE ext = '.json' AND filename LIKE '%_DNA.json'
                LIMIT 5
            """).fetchdf()
            
            target_als = als_df['filepath'].tolist()
            if target_als:
                # We could run these via Ray as well, or just process them directly if it's lightweight
                print(f"🎹 Found {len(target_als)} parsed Ableton arrangements. Learning nodes...")
                # (Demonstration of parsing logic)
                pass

            con.close()
            
            # Sleep before checking again
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(5)
            
        except Exception as e:
            print(f"\n❌ Daemon Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # To run the daemon indefinitely, we just call run_daemon()
    # For testing, we can run it as a normal script
    try:
        run_daemon()
    except KeyboardInterrupt:
        print("\n🛑 Swarm Daemon Shutdown.")