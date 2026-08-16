import sys
sys.stdout.reconfigure(encoding='utf-8')
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = r'C:\WEB CASE STUDY\models\gemma-2b-awq'
print(f"Loading {model_id}...")
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    device_map='auto',
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True
)
print("SUCCESS!")
