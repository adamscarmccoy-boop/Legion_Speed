import json
import numpy as np

with open(r'C:\WEB CASE STUDY\Acoustic-DNA-Audio-Engine\assets\market_score_audit_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

deltas = {}
for entry in data:
    if 'deltas' in entry:
        for k, v in entry['deltas'].items():
            if k not in deltas:
                deltas[k] = []
            deltas[k].append(v)

print("=== REVERSE ENGINEERED DSP DELTAS ===")
for k, v in deltas.items():
    print(f"{k}: Mean = {np.mean(v):.2f}, Std = {np.std(v):.2f}")
