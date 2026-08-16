import ray
import os
from ray import train
from ray.train import ScalingConfig
from ray.train.huggingface.transformers import RayTrainReportCallback, prepare_trainer
from ray.train.torch import TorchTrainer
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from datasets import load_dataset
from peft import LoraConfig, get_peft_model

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


def train_func(config):
    model_id = config["model_id"]
    dataset_path = config["dataset_path"]
    
    print(f"Loading Tokenizer {model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    # Gemma requires pad token for batching
    tokenizer.pad_token = tokenizer.eos_token
    
    print(f"Loading Model {model_id}...")
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="auto",
        torch_dtype="auto"
    )
    
    print("Applying LoRA...")
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, lora_config)
    
    print("Loading Dataset...")
    # Load the JSONL dataset we generated from the Antigravity Brain
    dataset = load_dataset("json", data_files=dataset_path, split="train")
    
    # Map the chat format to text
    def format_chat(example):
        text = ""
        for msg in example["conversations"]:
            role = msg["from"]
            content = msg["value"]
            text += f"<start_of_turn>{role}\n{content}<end_of_turn>\n"
        return {"text": text}
        
    dataset = dataset.map(format_chat)
    
    # Tokenize
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=1024)
        
    tokenized_datasets = dataset.map(tokenize_function, batched=True)
    
    training_args = TrainingArguments(
        output_dir="./gemma2-antigravity-lora",
        per_device_train_batch_size=2, # Small batch for memory
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        num_train_epochs=3,
        logging_steps=10,
        save_strategy="epoch",
        report_to="none" # Or tensorboard/wandb
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets,
    )
    
    # Ray integration
    trainer.add_callback(RayTrainReportCallback())
    trainer = prepare_trainer(trainer)
    
    print("Starting Training...")
    trainer.train()

if __name__ == "__main__":
    ray.init()
    
    # Configure resources
    scaling_config = ScalingConfig(
        num_workers=1, # Set to > 1 if you have multiple GPUs
        use_gpu=True,
    )
    
    config = {
        "model_id": "google/gemma-2-2b-it", # Or your exact path to QAT weights
        "dataset_path": "antigravity_training_dataset.jsonl"
    }
    
    trainer = TorchTrainer(
        train_loop_per_worker=train_func,
        train_loop_config=config,
        scaling_config=scaling_config,
    )
    
    print("Launching Ray Train Job...")
    result = trainer.fit()
    print(f"Training completed! Checkpoints saved to: {result.checkpoint}")