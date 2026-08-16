import re, os

md_file = r"C:\WEB CASE STUDY\antigravity_codegen_output_1.md"
with open(md_file, "r", encoding="utf-8") as f:
    content = f.read()

pattern = re.compile(r'###\s+.*?:?\s+`([^`]+)`.*?\n.*?```(?:python|typescript|ts|py)\n(.*?)```', re.DOTALL | re.IGNORECASE)
matches = pattern.findall(content)

file_mapping = {
    "dynamic_segment_master.py": r"C:\WEB CASE STUDY\dynamic_segment_master.py",
    "common_types.ts": r"C:\WEB CASE STUDY\antigravity_vscode_ext\src\common_types.ts",
    "extension.ts": r"C:\WEB CASE STUDY\antigravity_vscode_ext\src\extension.ts",
    "api_bridge.py": r"C:\WEB CASE STUDY\antigravity_vscode_ext\api_bridge.py",
    "legion_langgraph_brain.py": r"C:\WEB CASE STUDY\legion_langgraph_brain.py"
}

for filename, code in matches:
    clean_name = filename.strip()
    if clean_name in file_mapping:
        out_path = file_mapping[clean_name]
        print(f"Writing {out_path}...")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(code.strip() + "\n")
    else:
        print(f"Skipping unknown file: {clean_name}")
