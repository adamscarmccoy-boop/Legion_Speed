import os
import math

# The directories to scan
DIRECTORIES = [
    r"c:\WEB CASE STUDY",
    r"c:\STUDIES_BACKUP\Legion-Jacked-Pipeline"
]

# The layers we defined in the architecture
LAYERS = {
    "The DSP Muscle (.pt)": [".pt"],
    "The Semantic Brain (.onnx)": [".onnx"],
    "The Generative Engine (.th, .gguf)": [".th", ".gguf"],
    "The Vectors & Math (.duckdb, .lance)": [".duckdb", ".lance"],
    "The Audio Material (.wav, .mp3, .flac)": [".wav", ".mp3", ".flac"],
}

def format_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def scan_ecosystem():
    stats = {layer: {"count": 0, "size": 0} for layer in LAYERS}
    
    print("\n[🔎] Scanning Sovereign Ecosystem...")
    for directory in DIRECTORIES:
        if not os.path.exists(directory):
            continue
            
        for root, _, files in os.walk(directory):
            # Skip heavy virtual environments and git folders to speed up scanning
            if '.venv' in root or '.git' in root or 'node_modules' in root:
                continue
                
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                
                # Check which layer this belongs to
                for layer_name, extensions in LAYERS.items():
                    if ext in extensions:
                        stats[layer_name]["count"] += 1
                        try:
                            stats[layer_name]["size"] += os.path.getsize(os.path.join(root, file))
                        except Exception:
                            pass
                            
    print("\n" + "="*50)
    print(" 🚀 OMNI-VECTOR ECOSYSTEM STATS")
    print("="*50)
    
    total_size = 0
    total_files = 0
    
    for layer_name, data in stats.items():
        print(f"\n{layer_name}:")
        print(f"  -> Count: {data['count']} files")
        print(f"  -> Size:  {format_size(data['size'])}")
        total_size += data['size']
        total_files += data['count']
        
    print("\n" + "="*50)
    print(f"TOTAL DETECTED FILES: {total_files}")
    print(f"TOTAL SYSTEM MASS:    {format_size(total_size)}")
    print("="*50 + "\n")

if __name__ == "__main__":
    scan_ecosystem()
