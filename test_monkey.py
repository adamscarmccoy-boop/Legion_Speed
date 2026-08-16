import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import torch
import transformers.modeling_utils
from safetensors.torch import load as safe_load

# Monkey patch transformers to bypass mmap in safetensors!
original_load_state_dict = transformers.modeling_utils.load_state_dict
def custom_load_state_dict(checkpoint_file, *args, **kwargs):
    if checkpoint_file.endswith('.safetensors'):
        print(f"Bypassing mmap for {checkpoint_file}...")
        with open(checkpoint_file, 'rb') as f:
            data = f.read()
            return safe_load(data)
    return original_load_state_dict(checkpoint_file, *args, **kwargs)

transformers.modeling_utils.load_state_dict = custom_load_state_dict
transformers.modeling_utils.safe_open = None # Force it to use our patched load

from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "google/gemma-2-2b-it"
tokenizer = AutoTokenizer.from_pretrained(model_id)

try:
    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        device_map="auto",
        torch_dtype=torch.bfloat16,
        use_safetensors=True
    )
    print("Monkey patch successful!")
except Exception as e:
    print(f"FAILED: {e}")
