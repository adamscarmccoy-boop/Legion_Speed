import argparse
import os
import ray
import asyncio
import json

from legion_sonic_engine.utils import ensure_utf8_output, MasteringJobConfig
from legion_sonic_engine.audio_analysis_actor import AudioAnalysisActor
from legion_sonic_engine.lancedb_manager import LanceDBManager
from legion_sonic_engine.mastering_agent_actor import MasteringAgentActor

# --- Configuration (Paths now strictly local to backend directory)
LANCEDB_PATH = os.path.join(os.path.dirname(__file__), "..", "lancedb_omni_snowflake_rag")
LANCEDB_TABLE_NAME = "sonic_engine_baselines"
DEFAULT_OUTPUT_DIR = r"C:\Users\adams\Downloads" # Default directory for mastered files
DEFAULT_BASELINE_TRACK_NAME = "Chris Lake - Somebody (2024)" # Default baseline


# --- Initialize Ray and Actors ---
if not ray.is_initialized():
    ray.init(log_to_stdout=False) # Suppress Ray logs in CLI

ensure_utf8_output()

# Instantiate global actors
audio_analysis_actor = AudioAnalysisActor.remote()
mastering_agent_actor = MasteringAgentActor.remote(LANCEDB_PATH, LANCEDB_TABLE_NAME)
lancedb_manager_cli = LanceDBManager(LANCEDB_PATH, LANCEDB_TABLE_NAME)
lancedb_manager_cli.connect()
lancedb_manager_cli.create_table_if_not_exists()


# --- CLI Commands ---

async def master_file_command(args):
    """Handles the 'master' command: processes a single audio file."""
    input_filepath = os.path.abspath(args.input_file)
    output_filepath = os.path.abspath(args.output) if args.output else \
                      os.path.join(DEFAULT_OUTPUT_DIR, os.path.basename(input_filepath).replace('.', '_MASTERED.'))
    baseline_name = args.baseline if args.baseline else DEFAULT_BASELINE_TRACK_NAME

    print(f"--- Legion CLI: Mastering Single File ---")
    print(f"Input: {input_filepath}")
    print(f"Output: {output_filepath}")
    print(f"Baseline: {baseline_name}")

    if not os.path.exists(input_filepath):
        print(f"❌ Error: Input file not found at '{input_filepath}'")
        return

    job_config = MasteringJobConfig(
        input_filepath=input_filepath,
        output_filepath=output_filepath,
        baseline_track_name=baseline_name,
        segment_length_sec=args.segment_length
    )

    print("\n⚡ Submitting mastering job to Ray agent...")
    result = await mastering_agent_actor.adaptive_master_track.remote(job_config.model_dump())
    
    print("\n--- Mastering Result ---")
    print(json.dumps(result, indent=2))
    if result.get("status") == "success":
        print(f"\n✅ Mastering complete! Output saved to: {result['output_file']}")
    else:
        print(f"\n❌ Mastering failed: {result.get('message')}")


async def ingest_baseline_command(args):
    """Handles the 'ingest-baseline' command: adds a track to LanceDB as a baseline."""
    input_filepath = os.path.abspath(args.input_file)
    baseline_name = args.name if args.name else os.path.splitext(os.path.basename(input_filepath))[0]

    print(f"--- Legion CLI: Ingesting Baseline ---")
    print(f"Input: {input_filepath}")
    print(f"Baseline Name: {baseline_name}")

    if not os.path.exists(input_filepath):
        print(f"❌ Error: Input file not found at '{input_filepath}'")
        return

    print("\n🔮 Analyzing track to generate structural profile and embeddings...")
    profile_data_dict = await audio_analysis_actor.profile_track_by_sections.remote(input_filepath, max_sections=16)
    profile_data = lancedb_manager_cli.MasterTrackStructuralProfile(**profile_data_dict) # Re-Pydantic validate

    print(f"\n📊 Profile generated in {profile_data.processing_time_ms:.2f} ms. Found {profile_data.total_sections_found} sections.")
    
    print("🗄️ Adding profile to LanceDB as a baseline...")
    lancedb_manager_cli.add_baseline_profile(profile_data, baseline_name)
    print(f"✅ Baseline '{baseline_name}' ingestion process complete.")


async def watch_folder_command(args):
    """Handles the 'watch' command: starts the batch mastering watcher."""
    print(f"--- Legion CLI: Starting Folder Watcher ---")
    print(f"Watching: {args.input_folder}")
    print(f"Output: {args.output_folder}")
    print(f"Baseline: {args.baseline if args.baseline else DEFAULT_BASELINE_TRACK_NAME}")
    
    # Update batch_master configuration dynamically
    global WATCH_FOLDER, OUTPUT_FOLDER, DEFAULT_BASELINE_TRACK_NAME, SCAN_INTERVAL_SEC
    WATCH_FOLDER = os.path.abspath(args.input_folder)
    OUTPUT_FOLDER = os.path.abspath(args.output_folder)
    DEFAULT_BASELINE_TRACK_NAME = args.baseline if args.baseline else DEFAULT_BASELINE_TRACK_NAME
    SCAN_INTERVAL_SEC = args.interval

    # Import and run the batch_master directly
    # Note: This is an atypical way to run a daemon from CLI and would usually be a separate process.
    # For simplicity, we directly call its main function. It assumes the global config is updated.
    print("\nStarting batch mastering watcher in this process. Press Ctrl+C to stop.")
    from legion_sonic_engine.batch_master import batch_master_watcher
    batch_master_watcher()


async def main():
    parser = argparse.ArgumentParser(
        description="Legion Sonic Engine CLI: Master audio files using adaptive DSP and LanceDB baselines.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Master single file command
    master_parser = subparsers.add_parser('master', help='Master a single audio file.')
    master_parser.add_argument('input_file', type=str, help='Path to the input audio file (.wav, .mp3, .flac).')
    master_parser.add_argument('--output', '-o', type=str, 
                               help=f'Output file path. Defaults to {DEFAULT_OUTPUT_DIR}/<input_name>_MASTERED.<ext>.')
    master_parser.add_argument('--baseline', '-b', type=str,
                               help=f'Name of the baseline track in LanceDB to match against. Defaults to "{DEFAULT_BASELINE_TRACK_NAME}".')
    master_parser.add_argument('--segment-length', '-s', type=float, default=6.0,
                               help='Length of audio segments for dynamic mastering in seconds. Default: 6.0.')
    master_parser.set_defaults(func=master_file_command)

    # Ingest baseline command
    ingest_parser = subparsers.add_parser('ingest-baseline', help='Analyze an audio track and add its profile to LanceDB as a baseline.')
    ingest_parser.add_argument('input_file', type=str, help='Path to the audio file to ingest as a baseline.')
    ingest_parser.add_argument('--name', '-n', type=str,
                               help='A unique name for this baseline. Defaults to the input filename.')
    ingest_parser.set_defaults(func=ingest_baseline_command)

    # Watch folder command
    watch_parser = subparsers.add_parser('watch', help='Start a watcher that automatically masters new files in a folder.')
    watch_parser.add_argument('input_folder', type=str, 
                              help=f'Folder to watch for new audio files. Default: {WATCH_FOLDER}.')
    watch_parser.add_argument('output_folder', type=str, 
                              help=f'Folder to save mastered files. Default: {OUTPUT_FOLDER}.')
    watch_parser.add_argument('--baseline', '-b', type=str,
                               help=f'Name of the baseline track in LanceDB to match against. Defaults to "{DEFAULT_BASELINE_TRACK_NAME}".')
    watch_parser.add_argument('--interval', '-i', type=int, default=10,
                               help='Scan interval in seconds. Default: 10.')
    watch_parser.set_defaults(func=watch_folder_command)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        await args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    # Fix for Windows paths in argparse (optional, but good practice)
    # Allows paths to be passed with backslashes without issues
    def clean_path(path_str):
        if path_str:
            return os.path.normpath(path_str)
        return path_str
    
    for action in parser._actions:
        if isinstance(action, argparse._StoreAction) and 'file' in action.dest or 'folder' in action.dest:
            action.type = clean_path

    asyncio.run(main())
