# Sovereign Vision Pipeline & Environment Guide

This document outlines the architecture, scripts, virtual environments, and path allocations for the local, offline audio-reactive vision pipeline.

---

## 1. Virtual Environments & GPU Allocation

To maximize efficiency and hardware utilization on the GTX 1650, the pipeline is split between two virtual environments depending on GPU (CUDA) compatibility:

| Virtual Environment Path | Hardware Target | Primary Purpose | Key Packages |
| :--- | :--- | :--- | :--- |
| `E:\WEB CASE STUDY\.venv` | **GPU (CUDA: True)** | Fast image generation & CLIP tensor math | `torch (2.12.1)`, `transformers`, `sentence-transformers` |
| `C:\WEB CASE STUDY\.venv` | **CPU (CUDA: False)** | Vision models & post-processing | `torch (2.12.1)`, `torchvision (0.27.1)`, `pandas`, `scikit-learn` |

---

## 2. Core Scripts & Workflow

The creative pipeline flows in three distinct stages:

```
[Text Prompt / Words]
        │
        ▼  (Runs on E:\ venv - GPU)
┌──────────────────────────────────────────┐
│ 1. clip_generative_art.py                │  <-- Morphs a seed image into a new style
└───────────────────┬──────────────────────┘
                    │  (Saves: mastered_output/generated_art_[slug]_[time].png)
                    ▼  (Runs on C:\ venv - CPU)
┌──────────────────────────────────────────┐
│ 2. ray_vision_pipeline.py                │  <-- Runs detection/pose & draws HUD overlays
└───────────────────┬──────────────────────┘
                    │  (Saves: mastered_output/artwork_creation/cyber_hud_art.png)
                    ▼  (Runs on C:\ venv - CPU)
┌──────────────────────────────────────────┐
│ 3. feedback_visualizer.py                │  <-- Warps, pulses, & muxes audio to video
└───────────────────┬──────────────────────┘
                    │
                    ▼
 [Final Social Reel: mastered_output/feedback_test/feedback_reel_final.mp4]
```

### Script Directory

### 🎨 1. Image Generator (`clip_generative_art.py`)
* **Purpose**: Performs Image-to-Image CLIP optimization. It takes a high-quality "seed" image from your Downloads folder (retaining physical borders, faces, and shapes) and morphs its textures to match your text prompt.
* **Run Command**:
  ```powershell
  & "E:\WEB CASE STUDY\.venv\Scripts\python.exe" clip_generative_art.py
  ```

### 🤖 2. Cyber HUD Scanner (`ray_vision_pipeline.py`)
* **Purpose**: Runs object detection (Faster R-CNN) and pose estimation (Keypoint R-CNN) sequentially in pure Python. Overlays sci-fi corner brackets, scrolling scanners, reticle crosshairs, and skeletal joint trackers onto the generated artwork. Bypasses Ray entirely to prevent system locks.
* **Run Command**:
  ```powershell
  & "C:\WEB CASE STUDY\.venv\Scripts\python.exe" ray_vision_pipeline.py
  ```

### 🔊 3. Video Compiler (`feedback_visualizer.py`)
* **Purpose**: Creates the final 30-second vertical video. Zoom-pulses the image to the audio RMS energy, warps it dynamically, overlays the reactive bottom waveform bars, and encodes/muxes the original audio track with frame-perfect synchronization.
* **Run Command**:
  ```powershell
  & "C:\WEB CASE STUDY\.venv\Scripts\python.exe" feedback_visualizer.py
  ```

---

## 3. Reference Path Index

### Workspace Paths
* **Workspace Directory**: `C:\WEB CASE STUDY`
* **Local Configuration File**: `C:\WEB CASE STUDY\.env`

### Input Asset Paths
* **Audio Track**: `E:\DJSUSAN\LEGION\what a waste-2 (Edit).wav` *(29.6 MB)*
* **Original Branding Image**: `E:\OTHER\SCAR BRANDING\IMG_1357-RSVP.jpeg`
* **Structured Character Seed**: `C:\Users\adams\Downloads\image-1783388762801.png`

### Output Directory Paths
* **Base Outputs**: `C:\WEB CASE STUDY\mastered_output`
* **Morphed Art File**: `C:\WEB CASE STUDY\mastered_output\generated_art_*.png`
* **Scanned HUD Art**: `C:\WEB CASE STUDY\mastered_output\artwork_creation\cyber_hud_art.png`
* **Final Rendered Video**: `C:\WEB CASE STUDY\mastered_output\feedback_test\feedback_reel_final.mp4`
