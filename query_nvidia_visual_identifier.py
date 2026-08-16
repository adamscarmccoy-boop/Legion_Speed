import os
import sys
import json
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv(r"C:\WEB CASE STUDY\.env")
api_key = os.getenv("NVIDIA_API_KEY")

print("==================================================================")
print("     QUERYING NVIDIA NIM FOR VISUAL IDENTIFIER & TARGETED INPAINT  ")
print("==================================================================")

if not api_key:
    print("❌ Error: NVIDIA_API_KEY missing.")
    sys.exit(1)

prompt = """
You are the Lead Computer Vision & AI Systems Architect for the Sovereign Audio-Visual Swarm.

CONTEXT & USER GOAL:
We have local visual identification and segmentation models (DeepLabV3, PyTorch torchvision segmentors, ONNX feature extractors, object identifier models) designed to isolate specific scene elements:
- Lasers / Light Beams
- DJ Booth / Mainstage Structure
- Crowd / Audience
- Background / Horizon
- HUD Overlays / Reticles

USER REQUEST:
Design a precise 4-step technical pipeline using our Visual Identifier models to perform TARGETED ELEMENT REPLACEMENT (e.g., detecting and changing ONLY the lasers—color, beam angle, pulse rate—while keeping the DJ, crowd, and stage 100% untouched and synchronized with audio beats).

Provide:
1. Identification & Mask Extraction (using local segmentors to isolate laser mask tensor)
2. Targeted Element Manipulation (PyTorch GPU tensor hue/color shift & glow injection on laser mask ONLY)
3. Audio-Reactive Beat Synchronization (modulating laser intensity/color with sound transient density & sub-bass drops)
4. Integration with Ray Arrow Swarm for <5ms frame rendering.

Output clear GitHub-flavored markdown with complete Python code examples.
"""

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "meta/llama-3.1-8b-instruct",
    "messages": [
        {"role": "system", "content": "You are a world-class computer vision and PyTorch GPU architecture expert. Output clear markdown with runnable code."},
        {"role": "user", "content": prompt}
    ],
    "max_tokens": 1024,
    "temperature": 0.2
}

try:
    res = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
    res.raise_for_status()
    answer = res.json()["choices"][0]["message"]["content"]
    print("\n==================================================================")
    print("     NVIDIA NIM VISUAL IDENTIFIER & LASER MANIPULATION ROADMAP    ")
    print("==================================================================")
    print(answer)
    print("==================================================================")
except Exception as e:
    print(f"❌ NVIDIA API Error: {e}")
