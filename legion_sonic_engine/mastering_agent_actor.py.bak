import os
import time
import torch
import torchaudio
import numpy as np
import ray
import soundfile as sf # For reading/writing via pedalboard.io.AudioFile
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import euclidean

from pedalboard import Pedalboard, Compressor, HighpassFilter, Gain, Limiter, LowpassFilter
from pedalboard.io import AudioFile

from legion_sonic_engine.utils import (
    ensure_utf8_output, SectionMetrics, MasterTrackStructuralProfile, MasteringJobConfig
)
from legion_sonic_engine.audio_analysis_actor import AudioAnalysisActor
from legion_sonic_engine.lancedb_manager import LanceDBManager

# Initialize Ray if not already done
if not ray.is_initialized():
    ray.init(log_to_stdout=False)

ensure_utf8_output()

@ray.remote(num_gpus=1 if torch.cuda.is_available() else 0)
class MasteringAgentActor:
    def __init__(self, lancedb_path: str, lancedb_table_name: str):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.lancedb_manager = LanceDBManager(lancedb_path, lancedb_table_name)
        self.lancedb_manager.connect()
        self.lancedb_manager.create_table_if_not_exists()
        
        self.audio_analysis_actor = AudioAnalysisActor.remote()
        
        print(f"🎛️ MasteringAgentActor initialized on {self.device} with LanceDB at {lancedb_path}")

    async def adaptive_master_track(self, job_config_dict: dict) -> dict:
        """
        Orchestrates the entire adaptive mastering pipeline for a single track.
        
        Args:
            job_config_dict: A dictionary representing a MasteringJobConfig.
        
        Returns:
            A dictionary containing the mastering outcome and metrics.
        """
        try:
            job_config = MasteringJobConfig(**job_config_dict)
        except Exception as e:
            return {"status": "error", "message": f"Invalid job configuration: {e}"}

        input_path = job_config.input_filepath
        output_path = job_config.output_filepath
        baseline_track_name = job_config.baseline_track_name
        segment_length_sec = job_config.segment_length_sec

        if not os.path.exists(input_path):
            return {"status": "error", "message": f"Input file not found: {input_path}"}

        start_mastering_time = time.perf_counter()
        print(f"\n--- 🚀 INITIATING ADAPTIVE MASTERING: {os.path.basename(input_path)} ---")
        print(f"    Target Baseline: '{baseline_track_name}' | Output: {os.path.basename(output_path)}")

        # 1. Get baseline track profile from LanceDB
        baseline_profile_data = self.lancedb_manager.get_baseline_by_name(baseline_track_name)
        if not baseline_profile_data:
            return {"status": "error", "message": f"Baseline track '{baseline_track_name}' not found in LanceDB."}
        
        baseline_segments = baseline_profile_data.segment_data
        if not baseline_segments:
            return {"status": "error", "message": f"Baseline '{baseline_track_name}' has no segment data."}

        # For matching, we'll use a subset of key metrics and MFCCs
        # Scale numerical values for distance calculation
        baseline_features_raw = []
        baseline_mfcc_embeddings = []
        for seg in baseline_segments:
            baseline_features_raw.append([
                seg.rms_db, seg.crest_factor, seg.integrated_lufs, seg.loudness_range_lra,
                seg.spectral_centroid, seg.sub_bass_energy, seg.bass_energy, seg.mid_energy, seg.high_energy
            ])
            baseline_mfcc_embeddings.append(seg.mfcc_embedding)
        
        baseline_feature_matrix = np.array(baseline_features_raw, dtype=np.float32)
        baseline_mfcc_matrix = np.array(baseline_mfcc_embeddings, dtype=np.float32)
        
        baseline_segment_names = [seg.segment_name for seg in baseline_segments]
        
        print(f"✅ Loaded {len(baseline_segments)} segments from baseline '{baseline_track_name}'.")

        # 2. Load target track, slice into uniform segments, and extract features
        print("🎵 Loading target track and extracting features for alignment...")
        
        target_segments_features = []
        target_segments_mfccs = []
        audio_chunks = [] # Store raw audio chunks for processing
        
        with AudioFile(input_path) as f:
            sr = f.samplerate
            channels = f.num_channels
            frames_per_seg = int(segment_length_sec * sr)
            
            while True:
                audio_chunk_raw = f.read(frames_per_seg)
                if audio_chunk_raw.shape[1] == 0:
                    break
                
                # Check if chunk is too short to be meaningful
                if audio_chunk_raw.shape[1] < frames_per_seg // 2 and audio_chunk_raw.shape[1] < sr * 0.5:
                    break # Don't process very small residual chunks
                
                audio_chunks.append(audio_chunk_raw)
                
                # Create a temporary Pydantic model to leverage calculation functions
                # Note: This is a simplified analysis per uniform segment, not structural
                mono_np = audio_chunk_raw.mean(axis=0) if channels > 1 else audio_chunk_raw[0]
                
                rms_lin = float(np.sqrt(np.mean(mono_np ** 2)))
                rms_db = float(20 * np.log10(rms_lin)) if rms_lin > 1e-9 else -100.0
                peak = float(np.max(np.abs(mono_np)))
                crest = float(peak / rms_lin) if rms_lin > 1e-9 else 0.0
                
                integrated_lufs, loudness_range_lra = calculate_lufs_and_lra(audio_chunk_raw, sr)
                spectral_centroid = calculate_spectral_centroid(mono_np, sr)
                sub_bass_energy, bass_energy, mid_energy, high_energy = \
                    calculate_band_energies(mono_np, sr, mono_np.shape[0])
                mfcc_embedding = calculate_mfcc_embedding(mono_np, sr)
                
                target_segments_features.append([
                    rms_db, crest, integrated_lufs, loudness_range_lra,
                    spectral_centroid, sub_bass_energy, bass_energy, mid_energy, high_energy
                ])
                target_segments_mfccs.append(mfcc_embedding)

        if not audio_chunks:
            return {"status": "error", "message": "No audio chunks could be processed from the target track."}

        target_feature_matrix = np.array(target_segments_features, dtype=np.float32)
        target_mfcc_matrix = np.array(target_segments_mfccs, dtype=np.float32)
        
        print(f"  Extracted features for {len(target_feature_matrix)} uniform segments.")

        # 3. Scale features for distance calculation
        # Combine feature matrices and scale once to avoid bias
        scaler = StandardScaler()
        combined_features = np.vstack([baseline_feature_matrix, target_feature_matrix])
        scaler.fit(combined_features)
        
        scaled_baseline_features = scaler.transform(baseline_feature_matrix)
        scaled_target_features = scaler.transform(target_feature_matrix)
        
        # MFCCs are already normalized, but we can also scale them if desired (optional)
        mfcc_scaler = StandardScaler()
        combined_mfccs = np.vstack([baseline_mfcc_matrix, target_mfcc_matrix])
        mfcc_scaler.fit(combined_mfccs)
        
        scaled_baseline_mfccs = mfcc_scaler.transform(baseline_mfcc_matrix)
        scaled_target_mfccs = mfcc_scaler.transform(target_mfcc_matrix)

        # 4. Perform dynamic segment alignment (Euclidean distance on features + MFCCs)
        print("🎯 Aligning target segments to baseline reference segments...")
        aligned_target_info = []
        for i in range(len(scaled_target_features)):
            targ_combined_vec = np.concatenate([scaled_target_features[i], scaled_target_mfccs[i]])
            
            # Combine baseline features and MFCCs for matching
            baseline_combined_vectors = np.array([
                np.concatenate([scaled_baseline_features[j], scaled_baseline_mfccs[j]])
                for j in range(len(scaled_baseline_features))
            ])
            
            dists = cdist(targ_combined_vec.reshape(1, -1), baseline_combined_vectors, metric="euclidean")[0]
            best_idx = int(np.argmin(dists))
            
            # Look up matched baseline physical targets
            matched_baseline_seg = baseline_segments[best_idx]
            
            aligned_target_info.append({
                "targ_idx": i,
                "matched_base_seg": matched_baseline_seg,
                "distance": float(dists[best_idx])
            })
            print(f"  Segment {i:03d} -> matched '{matched_baseline_seg.segment_name}' | Dist: {dists[best_idx]:.3f}")

        # 5. Dynamic block-by-block mastering processing
        print("\n🎛️ Processing audio dynamically block-by-block with adaptive DSP...")
        
        # Initialize the effect nodes with default values
        # These will be dynamically updated
        hp = HighpassFilter(cutoff_frequency_hz=30.0)
        comp = Compressor(threshold_db=-20.0, ratio=3.0, attack_ms=10.0, release_ms=100.0)
        gain = Gain(gain_db=0.0)
        lim = Limiter(threshold_db=-0.3)
        
        board = Pedalboard([hp, comp, gain, lim])
        
        with AudioFile(output_path, 'w', samplerate=sr, num_channels=channels) as outfile:
            for seg_idx, audio_chunk_raw in enumerate(audio_chunks):
                # Get current segment's target values from the alignment
                match_info = aligned_target_info[seg_idx]
                target_seg_metrics = match_info["matched_base_seg"]
                
                target_rms_db = target_seg_metrics.rms_db
                target_crest_factor = target_seg_metrics.crest_factor
                target_lufs = target_seg_metrics.integrated_lufs
                target_sub_bass = target_seg_metrics.sub_bass_energy # Use for HPF adjustment
                
                # Analyze the raw chunk to calculate current values
                mono_chunk_np = audio_chunk_raw.mean(axis=0) if channels > 1 else audio_chunk_raw[0]
                current_rms_lin = float(np.sqrt(np.mean(mono_chunk_np ** 2)))
                current_rms_db = float(20 * np.log10(current_rms_lin)) if current_rms_lin > 1e-9 else -100.0
                current_peak = float(np.max(np.abs(mono_chunk_np)))
                current_crest_factor = float(current_peak / current_rms_lin) if current_rms_lin > 1e-9 else 0.0
                
                current_lufs, _ = calculate_lufs_and_lra(audio_chunk_raw, sr)
                current_sub_bass, _, _, _ = calculate_band_energies(mono_chunk_np, sr, mono_chunk_np.shape[0])
                
                # --- Dynamic DSP Parameter Adjustment Logic ---
                
                # Highpass Filter Adjustment: Reduce muddy sub-bass if target has less
                # Simple heuristic: If target sub-bass is significantly lower, raise HPF slightly.
                if current_sub_bass > target_sub_bass * 1.5 and hp.cutoff_frequency_hz < 60:
                    hp.cutoff_frequency_hz += 5 # Gently increase HPF
                    hp.cutoff_frequency_hz = min(hp.cutoff_frequency_hz, 80.0) # Cap HPF
                elif current_sub_bass < target_sub_bass * 0.8 and hp.cutoff_frequency_hz > 20:
                    hp.cutoff_frequency_hz -= 2 # Gently decrease HPF
                    hp.cutoff_frequency_hz = max(hp.cutoff_frequency_hz, 20.0) # Floor HPF
                
                # Compressor Adjustment: Match Crest Factor & RMS
                crest_delta = current_crest_factor - target_crest_factor
                if crest_delta > 0.1: # Current is spikier than target
                    comp.ratio = max(2.0, min(6.0, comp.ratio + crest_delta * 0.5))
                    comp.threshold_db = current_rms_db - (target_crest_factor * 0.5) # Dynamic threshold
                    comp.attack_ms = max(5.0, comp.attack_ms - 2.0)
                    comp.release_ms = max(50.0, comp.release_ms - 5.0)
                else: # Current is less spiky or matches target
                    comp.ratio = max(1.0, min(3.0, comp.ratio - 0.1)) # Relax compression
                    comp.threshold_db = 0.0 # Effectively bypass if no significant delta
                    comp.attack_ms = min(30.0, comp.attack_ms + 1.0)
                    comp.release_ms = min(200.0, comp.release_ms + 5.0)
                
                # Gain Adjustment: Match Integrated LUFS
                # Calculate gain needed to push current LUFS towards target
                lufs_delta = target_lufs - current_lufs
                gain.gain_db = max(-15.0, min(15.0, gain.gain_db + lufs_delta * 0.5))
                
                # Limiter: Always set to a safe commercial ceiling
                lim.threshold_db = -0.3 # Hard brickwall for final output
                lim.release_ms = max(50.0, min(200.0, abs(lufs_delta) * 5 + 50)) # Adaptive release

                # Run the chunk through the board with reset=False to preserve envelope states
                mastered_chunk = board(audio_chunk_raw, sample_rate=sr, reset=False)
                
                # Write to file
                outfile.write(mastered_chunk)
                
                # Log telemetry
                print(f"⚡ [SEG {seg_idx:03d}] Current LUFS: {current_lufs:.2f} (Target: {target_lufs:.2f}) | "
                      f"Gain: {gain.gain_db:+.2f}dB | Comp Ratio: {comp.ratio:.1f}:1 | HPF: {hp.cutoff_frequency_hz:.1f}Hz")
                
        total_mastering_latency_ms = (time.perf_counter() - start_mastering_time) * 1000
        
        print(f"\n======================================================")
        print(f"✅ Adaptive Mastering Complete! File saved to:\n   -> {output_path}")
        print(f"   Total Mastering Time: {total_mastering_latency_ms:.2f} ms")
        print(f"======================================================")

        return {
            "status": "success",
            "message": "Track mastered successfully.",
            "input_file": input_path,
            "output_file": output_path,
            "total_mastering_time_ms": total_mastering_latency_ms
        }

print("✅ MasteringAgentActor validated and ready.")

# Example usage (for local testing of the actor)
# if __name__ == "__main__":
#     # Configure LanceDB paths
#     LANCEDB_PATH = "C:\\STUDIES_BACKUP\\vectors\\lancedb_omni_snowflake_rag" # Your LanceDB path
#     LANCEDB_TABLE_NAME = "sonic_engine_baselines"
    
#     # Ensure baseline exists (run lancedb_manager.py example first or cli ingest_baseline)
#     # For this example, let's assume "Chris Lake - Somebody" is a baseline
#     # Create dummy baseline for quick test if not exists
#     manager_local = LanceDBManager(LANCEDB_PATH, LANCEDB_TABLE_NAME)
#     manager_local.connect()
#     manager_local.create_table_if_not_exists()
    
#     chris_lake_baseline = manager_local.get_baseline_by_name("Chris Lake - Somebody (2024)")
#     if not chris_lake_baseline:
#         print("⚠️ 'Chris Lake - Somebody (2024)' baseline not found. Creating a dummy for testing.")
#         dummy_mfcc = [float(i % 128) / 128.0 for i in range(128)]
#         dummy_seg = SectionMetrics(
#             segment_name="Drop/Main High-Energy Groove [Sect 1]", start_time_sec=0.0, end_time_sec=6.0, duration_sec=6.0,
#             rms_db=-7.7, crest_factor=2.5, integrated_lufs=-7.5, loudness_range_lra=2.0,
#             sub_bass_energy=8997.0, bass_energy=34839.0, mid_energy=965.0, high_energy=1296.0,
#             spectral_centroid=2061.0, mfcc_embedding=dummy_mfcc
#         )
#         dummy_profile = MasterTrackStructuralProfile(
#             filename="Somebody (2024).mp3", original_filepath="C:\\path\\to\\Somebody (2024).mp3", # Update with real path if known
#             total_sections_found=1, processing_time_ms=100.0, segment_data=[dummy_seg]
#         )
#         manager_local.add_baseline_profile(dummy_profile, "Chris Lake - Somebody (2024)")
#         print("Dummy baseline added.")
        
#     # Test file (replace with your actual audio file)
#     TEST_INPUT_FILE = r"C:\Users\adams\Downloads\putting in the work.wav" 
#     TEST_OUTPUT_FILE = r"C:\Users\adams\Downloads\putting in the work_MASTERED.wav"

#     if not os.path.exists(TEST_INPUT_FILE):
#         print(f"Test input file not found: {TEST_INPUT_FILE}")
#         exit()
    
#     mastering_agent = MasteringAgentActor.remote(LANCEDB_PATH, LANCEDB_TABLE_NAME)
    
#     job_config = MasteringJobConfig(
#         input_filepath=TEST_INPUT_FILE,
#         output_filepath=TEST_OUTPUT_FILE,
#         baseline_track_name="Chris Lake - Somebody (2024)",
#         segment_length_sec=6.0
#     )
    
#     import asyncio
#     async def run_mastering():
#         result = await mastering_agent.adaptive_master_track.remote(job_config.model_dump())
#         print("\nMastering Result:")
#         print(result)

#     asyncio.run(run_mastering())
