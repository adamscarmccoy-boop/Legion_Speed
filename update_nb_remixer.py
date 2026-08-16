import nbformat
import sys

nb_path = r'C:\WEB CASE STUDY\sovereign_bridge_analysis.ipynb'
script_path = r'C:\WEB CASE STUDY\omni_remixer_visualizer.py'

try:
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)
except Exception as e:
    print(f"Error reading notebook: {e}")
    sys.exit(1)

with open(script_path, 'r', encoding='utf-8') as f:
    code_content = f.read()

md_cell = nbformat.v4.new_markdown_cell("## Step 3: Sovereign Omni-Remixer (Refined Version)\nIncludes the foreground isolation, scaled-down PyTorch background effects (hue/rotation/invert), and no HUD overlays.")
nb.cells.append(md_cell)

code_cell = nbformat.v4.new_code_cell(code_content)
nb.cells.append(code_cell)

with open(nb_path, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print("Notebook successfully updated.")
