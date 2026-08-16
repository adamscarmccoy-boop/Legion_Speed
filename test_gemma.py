import sys
sys.stdout.reconfigure(encoding="utf-8")
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

print("🧠 Loading Gemma-2-2B-Instruct from local safetensors cache with device_map='auto'...")
model_id = "google/gemma-2-2b-it"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    device_map="auto",          # Automatically split across GPU and system RAM!
    torch_dtype=torch.bfloat16, # Keep it lightweight
    use_safetensors=True        # The security firewall!
)

print("\n✅ Gemma is online! Running test inference...\n")

chat_history = [{"role": "user", "content": "Hello! Are you online?"}]
prompt = tokenizer.apply_chat_template(chat_history, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

outputs = model.generate(**inputs, max_new_tokens=30, temperature=0.7, do_sample=True)
response_text = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

print(f"\nGemma: {response_text}\n")
print("TEST SUCCESSFUL")
