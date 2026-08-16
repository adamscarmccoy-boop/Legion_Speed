import os
import shutil

SOURCE_DIR = r"C:\WEB CASE STUDY"
DEST_DIR = r"E:\OmniCond_Production_Backup"

FILES_TO_COPY = [
    "upgraded_dynamic_batch_master_complete.ipynb",
    "train_omni_v3_generation.py",
    "upgraded_dynamic_batch_master.py",
    "deploy_engine.cpp",
    "OmniCondVAE_v3_Engineering_PostMortem.md",
    "sonic_dna_output/fretflow_omni_v3.pt",
    "sonic_dna_output/fretflow_proper_v2.pt",
    "sonic_dna_output/fretflow_v1.pt",
    "sonic_dna_output/fretflow_v2.pt",
    "sonic_dna_output/sonic_dna_master_v2.onnx",
    "sonic_dna_output/sonic_dna_mini_v1.onnx",
    "web_intel_sonicdb.duckdb",
    "data/enriched_samples_only.json"
]

LANCEDB_SRC = r"C:\STUDIES_BACKUP\vectors\lancedb_omni_snowflake_rag"
LANCEDB_DEST_REL = "lancedb_omni_snowflake_rag"

TEXT_EXTENSIONS = ('.py', '.ipynb', '.md', '.json', '.cpp', '.txt', '.html', '.csv')

def remap_paths_in_file(file_path, old_base, new_base):
    if not file_path.lower().endswith(TEXT_EXTENSIONS):
        return
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        new_content = content.replace(old_base, new_base)
        lancedb_target = os.path.join(new_base, LANCEDB_DEST_REL).replace('', '/')
        new_content = new_content.replace(LANCEDB_SRC, lancedb_target)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  [REMAP] {os.path.basename(file_path)}")
    except Exception as e:
        print(f"  [ERROR] Remapping {os.path.basename(file_path)}: {str(e)}")

def main():
    print(f"STARTING BACKUP TO {DEST_DIR}")
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)

    print("STEP 1: COPYING FILES")
    for rel_path in FILES_TO_COPY:
        src = os.path.join(SOURCE_DIR, rel_path)
        dst = os.path.join(DEST_DIR, rel_path)
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  [OK] {rel_path}")
        else:
            print(f"  [MISSING] {rel_path}")

    print("STEP 2: COPYING LANCE DB")
    if os.path.exists(LANCEDB_SRC):
        dst_lancedb = os.path.join(DEST_DIR, LANCEDB_DEST_REL)
        if os.path.exists(dst_lancedb):
            shutil.rmtree(dst_lancedb)
        shutil.copytree(LANCEDB_SRC, dst_lancedb)
        print(f"  [OK] LanceDB -> {dst_lancedb}")
    else:
        print(f"  [MISSING] LanceDB source")

    print("STEP 3: REMAPPING PATHS")
    for rel_path in FILES_TO_COPY:
        dst_file = os.path.join(DEST_DIR, rel_path)
        if os.path.exists(dst_file):
            remap_paths_in_file(dst_file, SOURCE_DIR, DEST_DIR)

    print("BACKUP COMPLETE.")

if __name__ == "__main__":
    main()
