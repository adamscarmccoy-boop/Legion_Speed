import os
import json

def count_model_bins(target_directory):
    # The target libraries you are looking for in the file paths
    keywords = ['torch', 'sentence_transformer', 'sentence-transformer', 'sentence transformer', 'torchvision']
    total_bins = 0
    bin_paths = []

    # Recursive function to walk through nested JSON dictionaries and lists
    def extract_paths(data):
        nonlocal total_bins
        if isinstance(data, dict):
            for value in data.values():
                extract_paths(value)
        elif isinstance(data, list):
            for item in data:
                extract_paths(item)
        elif isinstance(data, str):
            lower_str = data.lower()
            
            # Check if the string is a .bin path and contains your target libraries
            if lower_str.endswith('.bin') and any(kw in lower_str for kw in keywords):
                total_bins += 1
                bin_paths.append(data)

    # Walk through the specified directory to find all JSON files
    for root, _, files in os.walk(target_directory):
        for file in files:
            if file.endswith('.json'):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        json_content = json.load(f)
                        extract_paths(json_content)
                except (json.JSONDecodeError, UnicodeDecodeError, IOError):
                    # Silently skip files that are corrupted or not valid JSON
                    continue
    
    return total_bins, bin_paths

if __name__ == "__main__":
    # Replace with the path to your data lake or workspace
    search_dir = r"C:\WEB CASE STUDY" 
    
    print(f"Scanning all JSONs in {search_dir}...")
    total, paths = count_model_bins(search_dir)
    
    print(f"\nTotal Target .bin Files Found: {total}")
    
    # Optional: Print the first 20 paths to verify what it found
    if total > 0:
        print("\nSample paths found:")
        for p in paths[:20]: 
            print(f" - {p}")