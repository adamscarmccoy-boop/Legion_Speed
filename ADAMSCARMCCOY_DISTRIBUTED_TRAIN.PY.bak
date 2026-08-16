import ray
import ray.train.torch
from ray.train import ScalingConfig
import torch
import torchaudio
import io
import os
import sys

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


# ---------------------------------------------------------------------------
# 1. Define the distributed training loop
# ---------------------------------------------------------------------------
def train_loop_per_worker(config):
    # Setup local PyTorch distributed environment
    device = ray.train.torch.get_device()
    print(f"Worker running on device: {device}")
    
    # Placeholder: Replace this with your actual PyTorch model class
    # e.g., from your VAE model definitions
    class YourAudioGenModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            # Dummy linear layer for training pipeline structure
            self.linear = torch.nn.Linear(100, 100)
        def forward(self, x):
            # Dummy loss calculation
            return torch.mean(self.linear(x))
            
    model = YourAudioGenModel().to(device)
    
    # Load your base generative weights if they exist
    base_weights_path = config.get("base_weights_path", "base_audio_gen.pt")
    if os.path.exists(base_weights_path):
        model.load_state_dict(torch.load(base_weights_path, map_location=device))
        print("Successfully loaded base audio model weights.")
    else:
        print(f"Base weights not found at {base_weights_path}. Initializing with random weights.")
        
    model = ray.train.torch.prepare_model(model)
    
    # Get the data shard allocated to this specific worker
    data_shard = ray.train.get_dataset_shard("train_dataset")
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
    
    epochs = config.get("epochs", 5)
    print(f"Starting training loop for {epochs} epochs...")
    
    for epoch in range(epochs):
        batch_count = 0
        for batch in data_shard.iter_torch_batches(batch_size=16):
            # Batch shape conversion depends on model inputs
            # Here we assume a dummy shape for pipeline demonstration
            inputs = batch["audio"].to(device)
            # Ensure shape matches linear model expectation (dummy: batch_size, 100)
            if inputs.shape[-1] != 100:
                inputs = inputs[:, :100]
                
            optimizer.zero_grad()
            loss = model(inputs)
            loss.backward()
            optimizer.step()
            batch_count += 1
            
        print(f"Epoch {epoch} complete. Processed {batch_count} batches. Loss: {loss.item():.4f}")
            
    # Save your updated, hyper-stylized sovereign weights
    if ray.train.get_context().get_world_rank() == 0:
        output_weights = config.get("output_weights_path", "sovereign_custom_stems.pt")
        torch.save(model.state_dict(), output_weights)
        print(f"Successfully saved updated weights to: {output_weights}")

# ---------------------------------------------------------------------------
# 2. Ingest raw downloads directory using Ray Data
# ---------------------------------------------------------------------------
def load_and_preprocess(audio_dir):
    print(f"Loading binary files from: {audio_dir}...")
    # Stream binary audio from local storage
    ds = ray.data.read_binary_files(audio_dir)
    
    def decode_audio(batch):
        # Parallelized audio decoding using torchaudio
        tensors = []
        for b in batch["bytes"]:
            try:
                # Load audio data from memory buffer
                waveform, sr = torchaudio.load(io.BytesIO(b))
                # Flatten or downmix to mono to ensure shape consistency
                if waveform.shape[0] > 1:
                    waveform = torch.mean(waveform, dim=0, keepdim=True)
                tensors.append(waveform.squeeze().numpy())
            except Exception as e:
                # Append a dummy tensor on parsing failure to keep shapes aligned
                tensors.append(np.zeros(1000, dtype=np.float32))
                
        # Pad sequences to ensure matching lengths in the batch
        max_len = max(len(t) for t in tensors)
        padded_tensors = [np.pad(t, (0, max_len - len(t))) for t in tensors]
        
        return {"audio": padded_tensors}
        
    return ds.map_batches(decode_audio)

# ---------------------------------------------------------------------------
# 3. Trigger the Cluster Execution
# ---------------------------------------------------------------------------
def main():
    # Connect to your running Ray cluster
    try:
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        print("Connected to active Ray cluster.")
    except ConnectionError:
        print("Error: Could not connect to Ray cluster. Ensure Ray is running.")
        sys.exit(1)
        
    # Configure directories
    audio_dir = r"C:/Users/adams/Downloads/"
    if not os.path.exists(audio_dir):
        print(f"Error: Target audio directory '{audio_dir}' does not exist.")
        sys.exit(1)
        
    dataset = load_and_preprocess(audio_dir)
    
    # -----------------------------------------------------------------------
    # CRITICAL: Resource tuning for single-GPU systems
    # -----------------------------------------------------------------------
    # On a single-GPU machine (like your GTX 1650), setting num_workers > 1 
    # with use_gpu=True will result in GPU allocation starvation and crash.
    # We restrict to 1 GPU worker, utilizing CPU parallelization for Ray Data.
    # -----------------------------------------------------------------------
    scaling_config = ScalingConfig(
        num_workers=1, 
        use_gpu=True
    )
    
    trainer = ray.train.torch.TorchTrainer(
        train_loop_per_worker=train_loop_per_worker,
        train_loop_config={
            "epochs": 5,
            "base_weights_path": "base_audio_gen.pt",
            "output_weights_path": "sovereign_custom_stems.pt"
        },
        scaling_config=scaling_config,
        datasets={"train_dataset": dataset}
    )
    
    print("\nStarting distributed training run on Ray...")
    results = trainer.fit()
    print("Custom sovereign weights compiled successfully.")

if __name__ == "__main__":
    main()