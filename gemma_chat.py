import sys
sys.stdout.reconfigure(encoding="utf-8")
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

print("🧠 Loading Gemma-2-2B-Instruct from local safetensors cache...")
model_id = "google/gemma-2-2b-it"

# Load the tokenizer and the model securely using safetensors
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    device_map="auto",          # Automatically split across GPU and system RAM!
    torch_dtype=torch.bfloat16, # Keep it lightweight
    use_safetensors=True        # The security firewall!
)

print("\n✅ Gemma is online and jacked in. (Type 'exit' or 'quit' to stop)\n")

# Store the conversation history so she remembers what you say
chat_history = []

while True:
    try:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Shutting down...")
            break
            
        if not user_input.strip():
            continue
            
        # Append to history
        chat_history.append({"role": "user", "content": user_input})
        
        # Format the chat history using Gemma's specific instruct template
        prompt = tokenizer.apply_chat_template(chat_history, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        # Generate the response
        outputs = model.generate(**inputs, max_new_tokens=512, temperature=0.7, do_sample=True)
        
        # Decode only the newly generated text (ignoring the prompt)
        response_text = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        
        print(f"\nGemma: {response_text}\n")
        
        # Save her response to the history so she remembers it for the next question!
        chat_history.append({"role": "assistant", "content": response_text})
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        break
