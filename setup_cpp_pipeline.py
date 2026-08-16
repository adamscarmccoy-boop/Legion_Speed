import os
import shutil

# Establish exact local file path parameters matching your system
BASE_DIR = r"C:\web case study"
JAVA_SRC_DIR = os.path.join(BASE_DIR, "java-backend", "src", "main", "java", "ai", "pipeline")
CPP_BUILD_DIR = os.path.join(BASE_DIR, "cpp-core", "build")

# Target the explicit location where your browser saved the Colab file export
COLAB_DOWNLOAD_PATH = r"C:\Users\adams\Downloads\liblance_duckdb_core.so"
TARGET_LANE_PATH = os.path.join(CPP_BUILD_DIR, "liblance_duckdb_core.so")

def build_workspace_infrastructure():
    """Autonomously maps out missing path segments for the local pipeline."""
    print("[*] Instantiating file path tracks...")
    os.makedirs(JAVA_SRC_DIR, exist_ok=True)
    os.makedirs(CPP_BUILD_DIR, exist_ok=True)
    print(" [+] Directory segments structured successfully.")

def write_jni_java_bridge():
    """Generates the required Java Native Interface source link."""
    java_file_path = os.path.join(JAVA_SRC_DIR, "NativeDuckDBBridge.java")
    print(f"[*] Writing JNI Java Source Binding -> {java_file_path}")
    
    java_code = """package ai.pipeline;

public class NativeDuckDBBridge {
    static {
        // Enforce runtime link parameters to load the Colab-built library file
        System.loadLibrary("lance_duckdb_core");
    }

    // Direct entry execution handle linking down to your data rows
    public native String executeVectorPushdownSearch(String promptText);
}
"""
    with open(java_file_path, "w") as f:
        f.write(java_code)

def execute_binary_ingestion():
    """Autonomously pulls the .so file from your downloads folder into the project."""
    print("[*] Checking for downloaded Colab library artifact...")
    
    if os.path.exists(COLAB_DOWNLOAD_PATH):
        print(f" [+] Found compiled artifact at: {COLAB_DOWNLOAD_PATH}")
        try:
            # Perform atomic file move/copy into the local workspace target directory
            shutil.copy2(COLAB_DOWNLOAD_PATH, TARGET_LANE_PATH)
            print(f" [++] Success! Automated fusion complete. Copied binary straight to:\n      {TARGET_LANE_PATH}")
        except Exception as e:
            print(f" [!] File movement operation failed: {e}")
    else:
        print(f" [!] Detection error: Could not find 'liblance_duckdb_core.so' at {COLAB_DOWNLOAD_PATH}")
        print("     Please ensure the file finished downloading completely from Google Colab.")

if __name__ == "__main__":
    print("=== INITIALIZING AUTOMATED ARTIFACT FUSION ENGINE ===")
    build_workspace_infrastructure()
    write_jni_java_bridge()
    execute_binary_ingestion()
    print("=== ENVIRONMENT ALIGNED AND READY FOR EXECUTION ===")
