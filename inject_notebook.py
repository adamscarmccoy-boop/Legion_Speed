import json
import os

notebook_path = r'C:\.genkit\Sovereign_Audio_Intelligence_WhitePaper.ipynb'
script_path = r'C:\WEB CASE STUDY\AISTUDIO_ASK_GEMMA.py'

print(f"Reading notebook: {notebook_path}")
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Reading Python script: {script_path}")
with open(script_path, 'r', encoding='utf-8') as f:
    # readlines keeps the trailing \n for each line, which matches jupyter format
    code_lines = f.readlines() 

markdown_cell = {
    'cell_type': 'markdown',
    'metadata': {},
    'source': [
        '## 🤖 Gemma 26B Orchestration & Jinja Prompt Injection\n',
        'This cell implements dynamic LangGraph state mapping (via Hijack placeholders) and uploads the target files directly to AI Studio, dynamically rendering the prompt with Jinja2.'
    ]
}

code_cell = {
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': code_lines
}

nb['cells'].append(markdown_cell)
nb['cells'].append(code_cell)

print(f"Saving updated notebook...")
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Successfully injected cells into the notebook!")
