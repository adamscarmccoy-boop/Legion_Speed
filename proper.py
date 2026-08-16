import ast
import glob
import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

t0 = time.perf_counter()

target_files = glob.glob(r"C:\WEB CASE STUDY\*.py")
warden_classes = []

for filepath in target_files:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_name = node.name.lower()
                    if "warden" in class_name or "orchestrator" in class_name:
                        code = ast.get_source_segment(source, node)
                        if code:
                            warden_classes.append({
                                "name": node.name,
                                "file": os.path.abspath(filepath),
                                "length": len(code),
                                "code": code
                            })
    except Exception as e:
        pass

# Sort by biggest codes first (descending length)
warden_classes.sort(key=lambda x: x["length"], reverse=True)

t1 = time.perf_counter()
elapsed = t1 - t0

output = []
output.append("\n========================================================")
output.append("  🛡️ WARDEN & ORCHESTRATOR CODE (SORTED BY BIGGEST CODE FIRST) ")
output.append("========================================================")
output.append(f"⏱️ AST Parse & Scan Speed: {elapsed:.5f} seconds")
output.append(f"📂 Execution Script: {os.path.abspath(__file__)}")
output.append(f"📂 Export Target Log: C:\\WEB CASE STUDY\\Genome-Brain-actively.md")
output.append("========================================================\n")

if not warden_classes:
    output.append("No Warden or Orchestrator models found.")
else:
    for cls in warden_classes:
        output.append(f"📄 HARD PATH: {cls['file']}\n🔹 Model: {cls['name']} | Size: {cls['length']} chars")
        output.append("-" * 100)
        output.append(cls['code'])
        output.append("-" * 100 + "\n")

final_text = "\n".join(output)
print(final_text)

# Append to the user's markdown file
md_path = r"C:\WEB CASE STUDY\Genome-Brain-actively.md"
with open(md_path, "a", encoding="utf-8") as f:
    f.write("\n\n" + final_text)

print(f"\n[SUCCESS] Successfully appended execution results with hard paths and speed metrics to {md_path}")
