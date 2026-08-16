
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

"""
ONNX Orchestrator Training Pipeline — Ray-Accelerated
=====================================================
Trains a lightweight ONNX model from your Antigravity IDE conversation transcripts
to replace LLM calls for routing decisions (which tool to call, which node to invoke).

Data sources:
  - Antigravity IDE brain/ JSONL transcripts (user prompt → tool call → result)
  - Ray execution logs
  - Code knowledge parquets

Output: sovereign_orchestrator_v1.onnx
  - Input: 384D Snowflake Arctic embedding of user prompt
  - Output: action_id (which tool/node to route to)
  - Inference: < 1ms on CPU, free, no API calls

Usage:
  python train_onnx_orchestrator.py --brain-dir "path/to/brain" --output "sovereign_orchestrator_v1.onnx"
"""

import os
import sys
import json
import glob
import time
import logging
import argparse
from typing import List, Dict, Tuple, Optional
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("onnx_orchestrator_trainer")


# ---------------------------------------------------------------------------
# Stage 1: Harvest training pairs from JSONL transcripts
# ---------------------------------------------------------------------------
ACTION_LABELS = {
    "analyze_audio_structure": 0,
    "apply_dynamic_mastering": 1,
    "search_tracks": 2,
    "query_neural_core": 3,
    "pipeline_health_summary": 4,
    "start_ray_code_swarm": 5,
    "read_file": 6,
    "write_file": 7,
    "execute_command": 8,
    "get_asset_grid": 9,
    "get_artist_dna": 10,
    "extract_stems": 11,
    "generate_music_track": 12,
    "general_chat": 13,  # No tool call — just conversation
}
NUM_ACTIONS = len(ACTION_LABELS)


def harvest_transcripts(brain_dir: str) -> List[Dict]:
    """
    Crawl Antigravity IDE brain/ directory for JSONL transcripts.
    Extract (user_prompt, action_taken) pairs.
    """
    training_pairs = []
    transcript_files = glob.glob(os.path.join(brain_dir, "**", "transcript.jsonl"), recursive=True)
    
    logger.info(f"Found {len(transcript_files)} transcript files in {brain_dir}")
    
    for tf in transcript_files:
        try:
            with open(tf, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                try:
                    step = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                
                # Look for user inputs followed by tool calls
                if step.get("type") == "USER_INPUT" and step.get("content"):
                    user_prompt = step["content"]
                    
                    # Look ahead for the model's response with tool calls
                    for j in range(i + 1, min(i + 5, len(lines))):
                        try:
                            next_step = json.loads(lines[j].strip())
                        except (json.JSONDecodeError, IndexError):
                            continue
                        
                        if next_step.get("tool_calls"):
                            for tc in next_step["tool_calls"]:
                                tool_name = tc.get("name", "") if isinstance(tc, dict) else ""
                                # Strip MCP prefixes like "mcp_legion-architect_"
                                clean_name = tool_name.split("_", 2)[-1] if "mcp_" in tool_name else tool_name
                                
                                if clean_name in ACTION_LABELS:
                                    training_pairs.append({
                                        "prompt": user_prompt[:512],  # Truncate
                                        "action": clean_name,
                                        "action_id": ACTION_LABELS[clean_name],
                                        "source": tf,
                                    })
                            break
                        elif next_step.get("type") == "PLANNER_RESPONSE" and not next_step.get("tool_calls"):
                            # Model responded without tool calls — general chat
                            training_pairs.append({
                                "prompt": user_prompt[:512],
                                "action": "general_chat",
                                "action_id": ACTION_LABELS["general_chat"],
                                "source": tf,
                            })
                            break
        except Exception as e:
            logger.warning(f"Error processing {tf}: {e}")
    
    logger.info(f"Harvested {len(training_pairs)} training pairs from transcripts")
    return training_pairs


def harvest_mcp_sessions(sessions_dir: str) -> List[Dict]:
    """
    Harvest training pairs from MCP session JSONL files (like the Gemini CLI sessions).
    """
    training_pairs = []
    session_files = glob.glob(os.path.join(sessions_dir, "session-*.jsonl"))
    
    logger.info(f"Found {len(session_files)} MCP session files")
    
    for sf in session_files:
        try:
            with open(sf, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                    except json.JSONDecodeError:
                        continue
                    
                    # Look for user messages followed by tool calls in the same entry
                    if isinstance(entry, dict) and "toolCalls" in str(entry):
                        # This is a model response with tool calls
                        tool_calls = entry.get("toolCalls", [])
                        if not tool_calls and "content" in entry:
                            content = entry.get("content", "")
                            if isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and "functionCall" in item:
                                        tool_calls.append(item["functionCall"])
                        
                        for tc in tool_calls:
                            if isinstance(tc, dict):
                                name = tc.get("name", "")
                                clean_name = name.split("_", 2)[-1] if "mcp_" in name else name
                                if clean_name in ACTION_LABELS:
                                    # Try to find the preceding user message
                                    # (simplified — in practice, pair with the user message above)
                                    training_pairs.append({
                                        "prompt": f"[MCP session tool call: {clean_name}]",
                                        "action": clean_name,
                                        "action_id": ACTION_LABELS[clean_name],
                                        "source": sf,
                                    })
        except Exception as e:
            logger.warning(f"Error processing session {sf}: {e}")
    
    logger.info(f"Harvested {len(training_pairs)} pairs from MCP sessions")
    return training_pairs


# ---------------------------------------------------------------------------
# Stage 2: Embed prompts using Snowflake Arctic
# ---------------------------------------------------------------------------
def embed_prompts(prompts: List[str], batch_size: int = 32) -> np.ndarray:
    """
    Embed prompts using Snowflake Arctic Embed (384D vectors).
    Falls back to a simple hash-based embedding if the model isn't available.
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("Snowflake/snowflake-arctic-embed-l-v2.0")
        
        embeddings = []
        for i in range(0, len(prompts), batch_size):
            batch = prompts[i:i + batch_size]
            batch_embeddings = model.encode(batch, show_progress_bar=False)
            embeddings.append(batch_embeddings)
        
        return np.vstack(embeddings)
    
    except ImportError:
        logger.warning("sentence-transformers not available. Using hash-based fallback embeddings.")
        # Deterministic hash-based embedding as fallback
        embeddings = np.zeros((len(prompts), 384), dtype=np.float32)
        for i, prompt in enumerate(prompts):
            # Use hash of prompt words to create a pseudo-embedding
            words = prompt.lower().split()
            for j, word in enumerate(words[:384]):
                embeddings[i, j % 384] += hash(word) % 1000 / 1000.0
            # Normalize
            norm = np.linalg.norm(embeddings[i])
            if norm > 0:
                embeddings[i] /= norm
        return embeddings


# ---------------------------------------------------------------------------
# Stage 3: Train the orchestrator model
# ---------------------------------------------------------------------------
class OrchestratorDataset(Dataset):
    def __init__(self, embeddings: np.ndarray, labels: np.ndarray):
        self.embeddings = torch.tensor(embeddings, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.long)
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        return self.embeddings[idx], self.labels[idx]


class OrchestratorNet(nn.Module):
    """
    Small MLP that maps 384D Arctic embeddings to action IDs.
    Fast enough for < 1ms inference on CPU via ONNX Runtime.
    """
    def __init__(self, input_dim: int = 384, hidden_dim: int = 256, num_classes: int = NUM_ACTIONS):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, num_classes),
        )
    
    def forward(self, x):
        return self.net(x)


def train_model(
    embeddings: np.ndarray,
    labels: np.ndarray,
    epochs: int = 50,
    batch_size: int = 32,
    lr: float = 0.001,
) -> OrchestratorNet:
    """Train the orchestrator model."""
    dataset = OrchestratorDataset(embeddings, labels)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = OrchestratorNet().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    
    logger.info(f"Training on {len(dataset)} samples, {epochs} epochs, device: {device}")
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        correct = 0
        total = 0
        
        for batch_x, batch_y in dataloader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            correct += (predicted == batch_y).sum().item()
            total += batch_y.size(0)
        
        if (epoch + 1) % 10 == 0:
            acc = 100 * correct / total
            logger.info(f"Epoch {epoch+1}/{epochs} — Loss: {total_loss/len(dataloader):.4f}, Accuracy: {acc:.1f}%")
    
    return model


# ---------------------------------------------------------------------------
# Stage 4: Export to ONNX
# ---------------------------------------------------------------------------
def export_to_onnx(model: OrchestratorNet, output_path: str):
    """Export trained PyTorch model to ONNX format."""
    model.eval()
    model.cpu()
    
    dummy_input = torch.randn(1, 384)
    
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        input_names=["prompt_embedding"],
        output_names=["action_logits"],
        dynamic_axes={
            "prompt_embedding": {0: "batch_size"},
            "action_logits": {0: "batch_size"},
        },
        opset_version=14,
    )
    
    # Save action labels mapping alongside the ONNX model
    labels_path = output_path.replace(".onnx", "_labels.json")
    reverse_labels = {v: k for k, v in ACTION_LABELS.items()}
    with open(labels_path, "w") as f:
        json.dump(reverse_labels, f, indent=2)
    
    logger.info(f"Exported ONNX model to {output_path}")
    logger.info(f"Exported action labels to {labels_path}")
    
    # Verify with ONNX Runtime
    try:
        import onnxruntime as ort
        session = ort.InferenceSession(output_path)
        test_input = np.random.randn(1, 384).astype(np.float32)
        
        start = time.perf_counter()
        result = session.run(None, {"prompt_embedding": test_input})
        latency_ms = (time.perf_counter() - start) * 1000
        
        predicted_action = reverse_labels[int(np.argmax(result[0]))]
        logger.info(f"ONNX verification: inference in {latency_ms:.2f}ms, predicted action: {predicted_action}")
    except ImportError:
        logger.warning("onnxruntime not installed — skipping verification")


# ---------------------------------------------------------------------------
# Ray-accelerated version (optional — use when you have large datasets)
# ---------------------------------------------------------------------------
def train_with_ray(brain_dir: str, sessions_dir: str, output_path: str):
    """Run the full pipeline distributed across Ray actors."""
    import ray
    
    if not ray.is_initialized():
        ray.init(namespace="legion")
    
    @ray.remote(num_cpus=1)
    def harvest_remote(path, harvest_fn_name):
        if harvest_fn_name == "transcripts":
            return harvest_transcripts(path)
        else:
            return harvest_mcp_sessions(path)
    
    @ray.remote(num_cpus=1, num_gpus=0.5 if torch.cuda.is_available() else 0)
    def embed_remote(prompts):
        return embed_prompts(prompts)
    
    # Parallel harvest
    futures = []
    if os.path.exists(brain_dir):
        futures.append(harvest_remote.remote(brain_dir, "transcripts"))
    if os.path.exists(sessions_dir):
        futures.append(harvest_remote.remote(sessions_dir, "sessions"))
    
    all_pairs = []
    for result in ray.get(futures):
        all_pairs.extend(result)
    
    if not all_pairs:
        logger.error("No training data found!")
        return
    
    # Embed
    prompts = [p["prompt"] for p in all_pairs]
    labels = np.array([p["action_id"] for p in all_pairs])
    
    embeddings = ray.get(embed_remote.remote(prompts))
    
    # Train (on head node with GPU if available)
    model = train_model(embeddings, labels)
    export_to_onnx(model, output_path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Train ONNX Orchestrator from conversation transcripts")
    parser.add_argument("--brain-dir", default=r"C:\Users\adams\.gemini\antigravity-ide\brain",
                        help="Path to Antigravity IDE brain directory")
    parser.add_argument("--sessions-dir", default=r"C:\Users\adams\.gemini\tmp\skills\chats",
                        help="Path to MCP session JSONL files")
    parser.add_argument("--output", default=r"C:\WEB CASE STUDY\sovereign_orchestrator_v1.onnx",
                        help="Output path for ONNX model")
    parser.add_argument("--use-ray", action="store_true",
                        help="Use Ray for distributed training")
    parser.add_argument("--epochs", type=int, default=50,
                        help="Number of training epochs")
    args = parser.parse_args()
    
    if args.use_ray:
        train_with_ray(args.brain_dir, args.sessions_dir, args.output)
    else:
        # Sequential pipeline
        logger.info("=== Stage 1: Harvesting training data ===")
        pairs = []
        
        if os.path.exists(args.brain_dir):
            pairs.extend(harvest_transcripts(args.brain_dir))
        else:
            logger.warning(f"Brain directory not found: {args.brain_dir}")
        
        if os.path.exists(args.sessions_dir):
            pairs.extend(harvest_mcp_sessions(args.sessions_dir))
        else:
            logger.warning(f"Sessions directory not found: {args.sessions_dir}")
        
        if not pairs:
            logger.error("No training data found! Check your --brain-dir and --sessions-dir paths.")
            sys.exit(1)
        
        # Print distribution
        from collections import Counter
        dist = Counter(p["action"] for p in pairs)
        logger.info(f"Action distribution: {dict(dist)}")
        
        logger.info("=== Stage 2: Embedding prompts ===")
        prompts = [p["prompt"] for p in pairs]
        labels = np.array([p["action_id"] for p in pairs])
        embeddings = embed_prompts(prompts)
        
        logger.info("=== Stage 3: Training model ===")
        model = train_model(embeddings, labels, epochs=args.epochs)
        
        logger.info("=== Stage 4: Exporting to ONNX ===")
        export_to_onnx(model, args.output)
        
        logger.info("=== Done! ===")
        logger.info(f"Your orchestrator is at: {args.output}")
        logger.info(f"Use it with: onnxruntime.InferenceSession('{args.output}')")


if __name__ == "__main__":
    main()