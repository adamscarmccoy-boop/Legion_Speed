# Implementation Plan: True Stereo Sovereign Conductor & Trusting the Brain

## 1. Goal
1. **Fix Stereo Destruction:** `librosa.load(mono=True)` sums Left and Right channels, outputting a mono mix. This completely destroyed the stereo width. We must load, process, and export the true `(2, N)` stereo tensor.
2. **Remove Hardcoded Math Loop:** The OmniCondVAE was explicitly trained to output `[gain_db, compression_ratio, threshold_db]` that perfectly aligns the track. Adding a math-based RMS feedback loop overrides the intelligence. The brain "figures it out all together" — we must trust its weights.

## 2. Proposed Changes
### `c:\WEB CASE STUDY\sovereign_conductor.py` [MODIFY]
- **Stereo Ingestion:**
  ```python
  y_stereo, sr = librosa.load(path, mono=False)  # Shape: (2, N)
  y_mono = librosa.to_mono(y_stereo)             # Shape: (N,) for feature extraction ONLY
  ```
- **Trust the 109 Actors (The Brain):**
  - Feed the DSP extracted from `y_mono` into the ONNX Brain.
  - The Brain outputs `gain_db, ratio, threshold_db`.
  - Apply these EXACT parameters to `y_stereo`.
  - **No math loops.** No iterative RMS hunting. The Brain's prediction is the final command.
- **Stereo Export:**
  - Save `y_stereo.T` back to WAV using `soundfile.write`, preserving the original Left/Right panning and width.

## 3. Open Questions
- By "just run all my 109 actors", are you referring to the 105+ `TrainerActor` and `VAETrainer` instances currently sitting idle in your Ray cluster? If you want me to literally trigger a new training search (running them to find new weights) instead of just using the existing `.onnx` model, let me know. Otherwise, I will execute the plan above to fix the stereo audio routing through the existing ONNX Brain.
