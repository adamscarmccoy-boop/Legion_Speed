import os
os.environ["MAX_JOBS"] = "1"
os.environ["SAFETENSORS_FAST_GPU"] = "1"

import sys
sys.stdout.reconfigure(encoding='utf-8')
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "google/gemma-2-2b-it"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    device_map="auto",
    torch_dtype=torch.float16,
    use_safetensors=True,
    low_cpu_mem_usage=True,
    max_memory={0: "2500MiB", "cpu": "1500MiB"},
    offload_folder="offload_weights"
)

print("\nREADY")
sys.stdout.flush()

for line in sys.stdin:
    line = line.strip()
    if not line: continue
    if line == "exit": break
    
    chat_history = [{"role": "user", "content": line}]
    prompt = tokenizer.apply_chat_template(chat_history, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=30, temperature=0.7)
    response_text = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    print(f"\nGemma: {response_text}\nREADY")
    sys.stdout.flush()
