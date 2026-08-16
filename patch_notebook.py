import json
import re

NOTEBOOK_PATH = 'c:/WEB CASE STUDY/MUSIC_AND_VIDEO.ipynb'
ENGINE_PATH   = 'c:/WEB CASE STUDY/deterministic_video_engine.py'

with open(NOTEBOOK_PATH, 'r', encoding='utf-8') as f:
    nb = json.load(f)

with open(ENGINE_PATH, 'r', encoding='utf-8') as f:
    engine_code = f.read()

# ── Extract DifferentiableRenderer + PredGSAdapter classes ────────────────────
match = re.search(
    r'(class DifferentiableRenderer.*?)(?=def build_usable_video|\Z)',
    engine_code, re.DOTALL
)
if not match:
    print("[ERROR] Could not find DifferentiableRenderer in engine file.")
    exit(1)

class_body = match.group(1).strip()

# ── Build the cell source ──────────────────────────────────────────────────────
header_imports = [
    'import sys\n',
    'import torch\n',
    'import torch.nn as nn\n',
    'import kornia as K\n',
    'import kornia.filters as KF\n',
    'import kornia.geometry.transform as KGT\n',
    'from kornia.losses import SSIMLoss\n',
    '\n',
    '# Guard against Jupyter\'s non-reconfigurable stdout\n',
    'if hasattr(sys.stdout, "reconfigure"):\n',
    '    sys.stdout.reconfigure(encoding="utf-8")\n',
    '\n',
]

class_lines = [line + '\n' for line in class_body.split('\n')]

footer = [
    '\n',
    'def perceptual_video_loss(pred, target, lambda_l1=0.5, lambda_ssim=0.5):\n',
    '    """Hybrid L1 + SSIM Loss function"""\n',
    '    ssim_loss = SSIMLoss(window_size=11)\n',
    '    l1 = torch.nn.functional.l1_loss(pred, target)\n',
    '    ssim = ssim_loss(pred, target)\n',
    '    return lambda_l1 * l1 + lambda_ssim * ssim\n',
    '\n',
    'print("[OK] DifferentiableRenderer + PredGSAdapter defined.")\n',
]

new_source = header_imports + class_lines + footer

# ── New cell to inject ─────────────────────────────────────────────────────────
new_cell = {
    "cell_type": "code",
    "execution_count": None,
    "id": "differentiable_renderer_def",
    "metadata": {},
    "outputs": [],
    "source": new_source
}

# ── Strategy 1: update an existing definition cell if present ─────────────────
updated = False
for c in nb['cells']:
    if c['cell_type'] == 'code':
        source = ''.join(c.get('source', []))
        if 'class DifferentiableRenderer' in source or 'class PredGSAdapter' in source:
            c['source'] = new_source
            c['execution_count'] = None
            c['outputs'] = []
            print("Updated existing definition cell!")
            updated = True
            break

# ── Strategy 2: insert BEFORE the first cell that *uses* DifferentiableRenderer
if not updated:
    for i, c in enumerate(nb['cells']):
        if c['cell_type'] == 'code':
            source = ''.join(c.get('source', []))
            if 'DifferentiableRenderer(' in source or 'PredGSAdapter(' in source:
                nb['cells'].insert(i, new_cell)
                print(f"Inserted new definition cell before cell index {i}!")
                updated = True
                break

if not updated:
    # Append at the end as a fallback
    nb['cells'].append(new_cell)
    print("Appended definition cell at end of notebook (no usage site found).")

with open(NOTEBOOK_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("[OK] Notebook patched successfully.")
