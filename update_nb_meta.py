import json
import nbformat
import os

path = r'C:\.genkit\Sovereign_Audio_Intelligence_Generative_WhitePaper.ipynb'

with open(path, 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

for cell in nb.cells:
    if cell.cell_type == 'code':
        cell.source = cell.source.replace('.data"', '.meta.json"')

with open(path, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print("Updated notebook to use .meta.json")
