"""
Stem Mastering Orchestrator
===========================
This script acts as the "glue" between the stem separation tool and the
dynamic segment mastering logic. It does not contain any audio processing
itself, but rather orchestrates the calls to the existing, unmodified tools.
"""
import os
import sys
import argparse

# Ensure we can import from the parent directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from legion_mcp_client import SyncLegionMCPClient
from dynamic_segment_master import dynamic_segment_master

# The directory where the `extract_stems` tool saves its output
STEMS_OUTPUT_DIR = r"C:\STUDIES_BACKUP\separated_stems"

def get_stem_from_gap(intelligence_gap: str, demucs_output_dir: str) -> (str, str):
    """
    Selects the appropriate stem file based on keywords in the intelligence gap.
    Returns the stem name and the full path to the stem file.
    """
    gap = intelligence_gap.lower()
    
    stem_map = {
        "bass.wav": ["bass", "sub"],
        "drums.wav": ["drum", "rhythm", "transient", "percussion"],
        "vocals.wav": ["vocal", "lead", "melody"],
        "other.wav": ["synth", "harmony", "pads"]
    }

    for stem_file, keywords in stem_map.items():
        if any(keyword in gap for keyword in keywords):
            # The demucs tool creates a subdirectory named after the input file
            # e.g., input.mp3 -> separated/htdemucs/input/bass.wav
            # We need to find this nested path.
            
            # Let's find the subdirectory created by demucs
            possible_dirs = [d for d in os.listdir(demucs_output_dir) if os.path.isdir(os.path.join(demucs_output_dir, d))]
            if not possible_dirs:
                raise FileNotFoundError(f"No subdirectories found in demucs output path: {demucs_output_dir}")

            # Assume the newest directory is the one we want
            latest_dir = max([os.path.join(demucs_output_dir, d) for d in possible_dirs], key=os.path.getmtime)
            
            stem_path = os.path.join(latest_dir, stem_file)
            if os.path.exists(stem_path):
                return os.path.splitext(stem_file)[0], stem_path
            else:
                 raise FileNotFoundError(f"Could not find expected stem file at {stem_path}")

    # Default to processing the 'other' stem if no keywords match
    return "other", os.path.join(latest_dir, "other.wav")


def main(input_file: str, intelligence_gap: str):
    print("======================================================")
    print("    Stem-Based Mastering Workflow Initiated ")
    print("======================================================")
    print(f"Input File: {input_file}")
    print(f"Guiding Intelligence: {intelligence_gap}\n")

    # 1. Connect to MCP and extract stems
    mcp = SyncLegionMCPClient()
    mcp.connect()
    
    print("Step 1: Extracting stems via MCP...")
    # Demucs needs the full path
    full_input_path = os.path.join(r"C:\Users\adams\Downloads", input_file)
    result = mcp.call_tool("extract_stems", filepath=full_input_path)
    print(f"MCP Response: {result}\n")

    # 2. Select the target stem based on intelligence
    print("Step 2: Selecting target stem...")
    stem_name, stem_path = get_stem_from_gap(intelligence_gap, STEMS_OUTPUT_DIR)
    print(f"Targeted Stem: '{stem_name}' at {stem_path}\n")

    # 3. Run dynamic mastering on the selected stem
    print("Step 3: Running dynamic segment mastering on the stem...")
    # The dynamic master function needs just the filename, not the full path
    # and it assumes the file is in the Downloads directory. We need to adapt.
    # For now, let's copy the stem to the Downloads dir to use the script as-is.
    temp_stem_name = f"STEM_{stem_name}_{os.path.basename(input_file)}"
    temp_stem_path = os.path.join(r"C:\Users\adams\Downloads", temp_stem_name)
    import shutil
    shutil.copy(stem_path, temp_stem_path)

    # Define a custom output name for the mastered stem
    mastered_output_filename = f"MASTERED_{temp_stem_name}"
    
    # Call the unmodified mastering function
    dynamic_segment_master(temp_stem_name, custom_output=mastered_output_filename)

    # 4. Clean up
    mcp.disconnect()
    os.remove(temp_stem_path) # Clean up the temporary copied stem
    
    print("\n======================================================")
    print("          Stem Mastering Workflow Complete ")
    print("======================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stem-based mastering workflow orchestrator.")
    parser.add_argument("input_file", type=str, help="The name of the input audio file (must be in Downloads).")
    parser.add_argument("intelligence_gap", type=str, help="The reason/intelligence guiding the mastering.")
    args = parser.parse_args()
    
    main(args.input_file, args.intelligence_gap)
