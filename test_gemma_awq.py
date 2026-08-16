import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import time

model_id = r"c:\WEB CASE STUDY\models\gemma-2b-awq"

print(f"Loading {model_id}...")
start = time.time()

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype=torch.float16,
)

print(f"Loaded in {time.time() - start:.2f}s")

prompt = "The meaning of life is"
print(f"Prompt: {prompt}")

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

print("Generating...")
outputs = model.generate(**inputs, max_new_tokens=50)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)

print("\n--- RESPONSE ---")
print(response)
print("----------------")
