import nbformat
import sys

nb_path = r'C:\WEB CASE STUDY\sovereign_bridge_analysis.ipynb'
try:
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)
except Exception as e:
    print(f"Error reading notebook: {e}")
    sys.exit(1)

md_cell = nbformat.v4.new_markdown_cell("## Bonus: Talk to Gemma (Safetensors)\nThis will boot up the local 2B model securely into an interactive chat loop right here in the terminal output.")
nb.cells.append(md_cell)

code_cell = nbformat.v4.new_code_cell("!python gemma_chat.py")
nb.cells.append(code_cell)

with open(nb_path, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print("Notebook successfully updated.")
