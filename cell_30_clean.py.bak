# ============================================================
#  GENOME TRANSFORMER  RAY ACTOR (FULL WORKING CELL)
# ============================================================

import ray
import torch
import torch.nn as nn
import numpy as np
import pydantic_core
import langgraph

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


# ------------------------------------------------------------
# 1. Genome Transformer + Policy (same as before)
# -------------------------------------------------------------------
class GenomeTransformer(nn.Module):
    def __init__(self, dna_dim, hidden_dim=256, num_layers=4, num_heads=8):
        super().__init__()
        self.embedding = nn.Linear(dna_dim, hidden_dim)
        enc_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=0.1,
            batch_first=True
        )
        self.encoder = nn.TransformerEncoder(enc_layer, num_layers=num_layers)
        self.to_genome = nn.Linear(hidden_dim, hidden_dim)

    def forward(self, dna_seq):
        x = self.embedding(dna_seq)
        z = self.encoder(x)
        genome = self.to_genome(z.mean(dim=1))
        return genome

class GenomePolicy(nn.Module):
    def __init__(self, genome_dim, genre_dim=10):
        super().__init__()
        self.genre_head = nn.Linear(genome_dim, genre_dim)
        self.vibe_head = nn.Linear(genome_dim, 128)
        self.mastering_head = nn.Linear(genome_dim, 3)
        self.anomaly_head = nn.Linear(genome_dim, 1)
        self.marketing_head = nn.Linear(genome_dim, 1)

    def forward(self, genome):
        return {
            "genre": self.genre_head(genome),
            "vibe": self.vibe_head(genome),
            "mastering": self.mastering_head(genome),
            "anomaly": self.anomaly_head(genome),
            "marketing": self.marketing_head(genome),
        }

# ------------------------------------------------------------
# 2. Ray Actor: Genome Brain
# -------------------------------------------------------------------
@ray.remote
class GenomeBrain:
    def __init__(self, dna_dim):
        self.transformer = GenomeTransformer(dna_dim)
        self.policy = GenomePolicy(genome_dim=256)
        print(" GenomeBrain Actor is LIVE.")

    def infer(self, dna_sequence):
        """
        dna_sequence: numpy array shaped (batch, seq_len, dna_dim)
        """
        dna_tensor = torch.tensor(dna_sequence, dtype=torch.float32)
        genome = self.transformer(dna_tensor)
        policy = self.policy(genome)
        return {
            "genome": genome.detach().numpy(),
            "genre": policy["genre"].detach().numpy(),
            "vibe": policy["vibe"].detach().numpy(),
            "mastering": policy["mastering"].detach().numpy(),
            "anomaly": policy["anomaly"].detach().numpy(),
            "marketing": policy["marketing"].detach().numpy(),
        }

# ------------------------------------------------------------
# 3. Test with fake DNA (replace with real fused DNA later)
# -------------------------------------------------------------------
if __name__ == "__main__":
    # This block is for local testing only and won't run when imported
    import ray
    ray.init(namespace="legion", ignore_reinit_error=True)

    dna_dim = 256  # your fused DNA dimension
    genome_actor = GenomeBrain.options(name="GenomeBrain", lifetime="detached").remote(dna_dim)

    print("GenomeBrain Actor deployed.")

    # Test with fake DNA
    batch = 4
    seq_len = 10
    dna_sequence = np.random.randn(batch, seq_len, dna_dim).astype(np.float32)

    result = ray.get(genome_actor.infer.remote(dna_sequence))

    print("GENOME:", result["genome"].shape)
    print("GENRE:", result["genre"].shape)
    print("MASTERING:", result["mastering"].shape)