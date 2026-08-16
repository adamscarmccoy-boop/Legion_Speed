# fix_with_lmstudio.py - Uses YOUR LM Studio to solve YOUR problems
import os
from openai import OpenAI

# 1️⃣ Connect to YOUR LM Studio (same as in montytest4.py)
client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"  # LM Studio doesn't validate this, but requires a string
)

# 2️⃣ Define the problem (paste your error or question here)
problem = """
I'm getting this error when trying to run my inspection script in C:\WEB CASE STUDY:
FileNotFoundError: Could not find module 'C:\WEB CASE STUDY\.venv\Lib\site-packages\ray\_raylet.pyd' (or one of its dependencies). Try using the full path with constructor syntax.

I activated my virtual environment with `& "C:\WEB CASE STUDY\.venv\Scripts\Activate.ps1"` but still get this error. 
My project structure shows a .venv folder, and I'm trying to run: python "11# inspect_acp.py"
How do I fix this using ONLY tools already in my environment (Ray, LM Studio, Python)?
"""

# 3️⃣ Ask YOUR LM Studio for a solution
response = client.chat.completions.create(
    model="nvidia/nemotron-3-nano-4b",  # or whatever model you loaded in LM Studio
    messages=[
        {"role": "system", "content": "You are a senior Python/Ray/Windows debugging expert. Give precise, actionable steps. Assume the user has: Ray, LM Studio (OpenAI-compatible), Python venv, and access to standard Windows CLI tools. Never suggest installing new packages—use what's already available."},
        {"role": "user", "content": problem}
    ],
    temperature=0.1,  # Low temp for factual, consistent advice
    max_tokens=50000
)

# 4️⃣ Print the AI-generated solution
print("💡 LM STUDIO'S SOLUTION FOR YOU:\n")
print(response.choices[0].message.content)