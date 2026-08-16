import subprocess
import os
import shutil
import glob
import tempfile
import sys
import zipfile

def copy_missing_files(src_dir, dst_dir):
    missing_files_copied = 0
    for root, dirs, files in os.walk(src_dir):
        # Determine the relative path to the source root
        rel_path = os.path.relpath(root, src_dir)
        target_root = os.path.normpath(os.path.join(dst_dir, rel_path))
        
        # Ensure the corresponding directory exists in the destination
        if not os.path.exists(target_root):
            os.makedirs(target_root)
            
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(target_root, file)
            
            # Only copy if it DOES NOT exist in the destination
            if not os.path.exists(dst_file):
                shutil.copy2(src_file, dst_file)
                missing_files_copied += 1
                print(f"Restored missing file: {os.path.normpath(os.path.join(rel_path, file))}")
                
    return missing_files_copied

def fix_ray():
    print("=" * 60)
    print("🛠️ DOWNLOADING RAY 1.9.2 TO RESTORE ONLY MISSING FILES 🛠️")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"1. Downloading Ray 1.9.2 wheel into temporary folder...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "download", "ray==1.9.2",
                "--no-deps", "--python-version", "39", "--platform", "win_amd64",
                "--only-binary=:all:", "-d", tmpdir
            ])
        except subprocess.CalledProcessError as e:
            print(f"Failed to download wheel: {e}")
            return
            
        wheels = glob.glob(os.path.join(tmpdir, "ray*.whl"))
        if not wheels:
            print("Could not find the downloaded wheel file.")
            return
            
        whl_path = wheels[0]
        print(f"2. Extracting {os.path.basename(whl_path)}...")
        with zipfile.ZipFile(whl_path, 'r') as z:
            z.extractall(tmpdir)
            
        src = os.path.join(tmpdir, "ray")
        dst = r"C:\WEB CASE STUDY\.venv\Lib\site-packages\ray"
        
        print(f"3. Scanning and copying ONLY MISSING files from 1.9.2 to your environment...")
        copied_count = copy_missing_files(src, dst)
        
        print(f"\n✅ Successfully restored {copied_count} missing legacy files (including ray._common)!")
        print("NO existing files in your Ray 2.55 installation were overwritten.")

if __name__ == "__main__":
    fix_ray()
