import os
import sys
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

API_KEY = "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"
BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL_NAME = "meta/llama-3.1-70b-instruct"

paper1_path = r"C:\WEB CASE STUDY\mastered_output\paper1_eval.json"
paper2_path = r"C:\WEB CASE STUDY\mastered_output\paper2_eval.json"

with open(paper1_path, "r", encoding="utf-8") as f:
    paper1_data = json.load(f)

with open(paper2_path, "r", encoding="utf-8") as f:
    paper2_data = json.load(f)

llm = ChatOpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
    model=MODEL_NAME,
    temperature=0.1,
    max_tokens=2000
)

prompt = f"""
You are an expert NVIDIA Deep Learning Engineer & Performance Optimizer.

Here is the exact empirical evaluation data from our Audio-Visual Neural Pipeline:

PAPER 1 EVALUATION DATA:
{json.dumps(paper1_data, indent=2)}

PAPER 2 EVALUATION DATA:
{json.dumps(paper2_data, indent=2)}

DIAGNOSIS & GOAL:
1. In Paper 1 §4.2, the Adam optimization convergence improvement was only 0.59% (loss 0.3400 -> 0.3380) because standard Adam with constant lr=0.01 gets stuck on high-dimensional acoustic DNA vectors.
2. We need a higher optimization learning rate (e.g. lr=0.05), cosine annealing learning rate scheduler (`torch.optim.lr_scheduler.CosineAnnealingLR`), and proper DNA vector z-score normalization (`(dna - mean)/std`).
3. Write the EXACT Python code block for Paper 1 (§4) and Paper 2 (§5) that fixes these optimization issues, achieves strong convergence improvement (>15%), and handles Warden governance cleanly.

Return ONLY Python code blocks that can be executed directly.
"""

print(f"📡 Querying NVIDIA NIM ({MODEL_NAME}) via LangChain for optimized Python fixes...")

response = llm.invoke([
    SystemMessage(content="You are an expert NVIDIA Deep Learning Engineer. Provide optimized Python code solutions for PyTorch audio-visual pipelines."),
    HumanMessage(content=prompt)
])

print("\n=================== NVIDIA OPTIMIZED CODE SOLUTION ===================")
print(response.content)
print("======================================================================")

# Save response for application
with open(r"C:\WEB CASE STUDY\nvidia_fixes.py", "w", encoding="utf-8") as f:
    f.write(response.content)
