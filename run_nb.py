import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
path = r'C:\.genkit\Sovereign_Audio_Intelligence_Generative_WhitePaper.ipynb'

print(f"Loading notebook: {path}")
with open(path, 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

print("Executing notebook cells...")
ep = ExecutePreprocessor(timeout=600, kernel_name='python3')

try:
    ep.preprocess(nb, {'metadata': {'path': r'C:\WEB CASE STUDY'}})
    print("Execution complete! Writing outputs back to the notebook...")
    with open(path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)
    print("Done. Outputs and visuals are now embedded in the notebook.")
except Exception as e:
    print(f"Error during notebook execution: {e}")
    # Still write back the notebook so we can see which cell failed
    with open(path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)
