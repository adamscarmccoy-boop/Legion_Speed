
import pandas as pd
import numpy as np

path = r"C:\WEB CASE STUDY\notebook_knowledge_audit.parquet"
df = pd.read_parquet(path)

print("Vector-ish columns:")
for c in df.columns:
    sample = df[c].dropna().head(5).tolist()
    if not sample:
        continue

    s = sample[0]
    is_vector = isinstance(s, (list, tuple, np.ndarray))
    print(c, "=>", type(s), "VECTOR" if is_vector else "")
PY