import os
import unittest
import numpy as np
import torch
import torchaudio
import librosa
from scipy.signal import butter, lfilter
import pyloudnorm as ln

from pedalboard import Pedalboard, Gain, HighpassFilter, Compressor
from pedalboard.io import AudioFile # Needed for pedalboard to manage files

from legion_sonic_engine.utils import (
    calculate_lufs_and_lra, calculate_spectral_centroid, calculate_mfcc_embedding,
    calculate_band_energies, ensure_utf8_output
)

ensure_utf8_output()

class TestAudioMath(unittest.TestCase):

    def setUp(self):
        """Set up common test parameters and generate dummy audio for tests."""
        self.sr = 44100
        self.duration = 5 # seconds
        self.num_samples = self.sr * self.duration
        self.dummy_signal_mono = np.random.randn(self.num_samples).astype(np.float32) * 0.5
        self.dummy_signal_stereo = np.stack([self.dummy_signal_mono, self.dummy_signal_mono], axis=0) * 0.5
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"\n--- Running tests on device: {self.device} ---")

        # Create a temporary dummy WAV file for pedalboard.io.AudioFile tests
        self.temp_input_wav = "test_input_temp.wav"
        self.temp_output_wav = "test_output_temp.wav"
        torchaudio.save(self.temp_input_wav, torch.from_numpy(self.dummy_signal_stereo), self.sr)

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_input_wav):
            os.remove(self.temp_input_wav)
        if os.path.exists(self.temp_output_wav):
            os.remove(self.temp_output_wav)

    def test_stft_consistency(self):
        """Verify STFT calculations on CPU match expected sizes and properties."""
        print("  Testing STFT consistency...")
        n_fft = 2048
        hop_length = 512

        # Librosa STFT (CPU)
        stft_librosa = librosa.stft(self.dummy_signal_mono, n_fft=n_fft, hop_length=hop_length)
        
        # Torchaudio STFT (CPU)
        stft_torchaudio = torchaudio.transforms.Spectrogram(
            n_fft=n_fft, hop_length=hop_length, power=None, return_complex=True
        )(torch.from_numpy(self.dummy_signal_mono))

        # Check shapes
        self.assertEqual(stft_librosa.shape, stft_torchaudio.shape, "STFT shapes should match.")
        
        # Check if values are close (due to windowing differences, they won't be identical)
        # We'll compare magnitude for a looser check
        self.assertTrue(np.allclose(np.abs(stft_librosa), np.abs(stft_torchaudio.numpy()), atol=1e-3),
                        "STFT magnitudes should be close between Librosa and Torchaudio (CPU).")
        print("  ✅ STFT consistency (Librosa vs Torchaudio CPU) passed.")
        
        # Test GPU offloading for Torchaudio
        if self.device.type == 'cuda':
            stft_torchaudio_gpu = torchaudio.transforms.Spectrogram(
                n_fft=n_fft, hop_length=hop_length, power=None, return_complex=True
            )(torch.from_numpy(self.dummy_signal_mono).to(self.device))
            
            self.assertEqual(stft_librosa.shape, stft_torchaudio_gpu.cpu().shape, "STFT shapes should match on GPU.")
            self.assertTrue(np.allclose(np.abs(stft_librosa), np.abs(stft_torchaudio_gpu.cpu().numpy()), atol=1e-3),
                            "STFT magnitudes should be close (Librosa CPU vs Torchaudio GPU).")
            print("  ✅ STFT consistency (Librosa CPU vs Torchaudio GPU) passed.")


    def test_stereo_phase_cancellation(self):
        """Verify phase cancellation: inverted stereo channels should result in near zero output."""
        print("  Testing stereo phase cancellation...")
        # Create a stereo signal where right channel is inverted
        inverted_stereo = np.stack([self.dummy_signal_mono, -self.dummy_signal_mono], axis=0)

        # Summing these to mono should result in near zero
        summed_to_mono = np.mean(inverted_stereo, axis=0)

        # RMS of the summed signal should be very small
        rms_summed = np.sqrt(np.mean(summed_to_mono ** 2))
        self.assertLess(rms_summed, 1e-5, "Summing inverted stereo channels should result in near zero RMS.")
        print("  ✅ Stereo phase cancellation detection passed.")

    def test_gain_boost_accuracy(self):
        """Verify that gain boosts are mathematically exact on float32 waveforms."""
        print("  Testing gain boost accuracy...")
        gain_db = 6.0 # +6dB means doubling amplitude
        expected_multiplier = 10**(gain_db / 20)
        
        pedalboard_gain = Gain(gain_db=gain_db)
        
        # Apply gain using Pedalboard
        processed_mono = pedalboard_gain(self.dummy_signal_mono, self.sr)
        
        # Compare with manual multiplication
        expected_mono = self.dummy_signal_mono * expected_multiplier
        
        self.assertTrue(np.allclose(processed_mono, expected_mono, atol=1e-6),
                        f"Pedalboard Gain({gain_db}dB) should accurately multiply amplitude.")
        print("  ✅ Gain boost accuracy passed.")

    def test_lufs_lra_calculation(self):
        """Verify LUFS and LRA calculations for known loud/quiet signals."""
        print("  Testing LUFS and LRA calculations...")
        # Create a very quiet signal
        quiet_signal = np.random.randn(self.num_samples).astype(np.float32) * 0.001
        quiet_lufs, quiet_lra = calculate_lufs_and_lra(quiet_signal, self.sr)
        
        # A very quiet signal should have a very low LUFS value (e.g., below -40 LUFS)
        self.assertLess(quiet_lufs, -40.0, "Quiet signal should have low integrated LUFS.")
        
        # Create a moderately loud signal (e.g., -10 dBFS peak, -15 LUFS integrated)
        loud_signal_peak = 0.5
        loud_signal = np.sin(2 * np.pi * 440 * np.arange(self.num_samples) / self.sr).astype(np.float32) * loud_signal_peak
        loud_lufs, loud_lra = calculate_lufs_and_lra(loud_signal, self.sr)
        
        # Check if LUFS is within a reasonable range for a loud signal (e.g., -20 to -5 LUFS)
        self.assertGreater(loud_lufs, -25.0, "Loud signal should have higher integrated LUFS.")
        self.assertLess(loud_lufs, 0.0, "Loud signal LUFS should be below 0 dBFS.")
        
        # LRA should be non-negative
        self.assertGreaterEqual(quiet_lra, 0.0, "LRA should be non-negative.")
        self.assertGreaterEqual(loud_lra, 0.0, "LRA should be non-negative.")
        print("  ✅ LUFS and LRA calculation sanity checks passed.")

    def test_spectral_centroid_calculation(self):
        """Verify spectral centroid behaves as expected for low vs. high frequency signals."""
        print("  Testing spectral centroid calculation...")
        # Create a low-frequency sine wave (e.g., 100 Hz)
        low_freq_signal = np.sin(2 * np.pi * 100 * np.arange(self.num_samples) / self.sr).astype(np.float32) * 0.5
        low_centroid = calculate_spectral_centroid(low_freq_signal, self.sr)
        
        # Create a high-frequency sine wave (e.g., 5000 Hz)
        high_freq_signal = np.sin(2 * np.pi * 5000 * np.arange(self.num_samples) / self.sr).astype(np.float32) * 0.5
        high_centroid = calculate_spectral_centroid(high_freq_signal, self.sr)
        
        # High frequency signal should have a higher spectral centroid
        self.assertGreater(high_centroid, low_centroid, "High frequency signal should have higher spectral centroid.")
        print("  ✅ Spectral centroid calculation passed.")
        
    def test_mfcc_embedding_properties(self):
        """Verify MFCC embedding output dimensions and non-zero values."""
        print("  Testing MFCC embedding properties...")
        n_mfcc = 128
        embedding = calculate_mfcc_embedding(self.dummy_signal_mono, self.sr, n_mfcc=n_mfcc)
        
        self.assertEqual(len(embedding), n_mfcc, f"MFCC embedding should have {n_mfcc} dimensions.")
        self.assertTrue(any(e != 0 for e in embedding), "MFCC embedding should not be all zeros for a non-silent signal.")
        print("  ✅ MFCC embedding properties passed.")

    def test_pedalboard_continuous_processing(self):
        """
        Verify Pedalboard's `reset=False` for continuous processing
        without clicks/phase issues across chunks.
        """
        print("  Testing Pedalboard continuous processing (no clicks)...")
        # Define a simple pedalboard with a compressor and gain
        board = Pedalboard([
            Compressor(threshold_db=-20.0, ratio=2.0, attack_ms=10.0, release_ms=100.0),
            Gain(gain_db=3.0)
        ])

        # Load audio from file
        with AudioFile(self.temp_input_wav) as infile:
            sr = infile.samplerate
            channels = infile.num_channels
            total_frames = infile.frames
            chunk_size = sr # 1-second chunks

            output_chunks = []
            
            while infile.tell() < total_frames:
                audio_chunk = infile.read(chunk_size)
                if audio_chunk.shape[1] == 0:
                    break
                
                # Process with reset=False for continuous operation
                processed_chunk = board(audio_chunk, sample_rate=sr, reset=False)
                output_chunks.append(processed_chunk)
            
            # Concatenate all processed chunks
            if output_chunks:
                full_processed_audio = np.concatenate(output_chunks, axis=1)
                torchaudio.save(self.temp_output_wav, torch.from_numpy(full_processed_audio), sr)
                print(f"  Processed audio saved to {self.temp_output_wav}")
                
                # A qualitative check for clicks would involve listening or more complex analysis.
                # For automated testing, we'll check if output size matches input.
                self.assertEqual(full_processed_audio.shape[1], total_frames, "Output frames should match input frames.")
                # We can't easily quantify "no clicks" without a specific metric or human ear.
                # The primary test is that the pipeline runs without errors and state is maintained.
                self.assertFalse(np.array_equal(self.dummy_signal_stereo, full_processed_audio), 
                                 "Processed audio should be different from original.")
                print("  ✅ Pedalboard continuous processing completed without errors.")
            else:
                self.fail("No audio chunks processed by Pedalboard.")


if __name__ == '__main__':
    unittest.main()
