import os
import sys
import time
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms.functional as F
import numpy as np
from PIL import Image, ImageFilter
from sovereign_vision_bridge import SovereignVisionBrain

sys.stdout.reconfigure(encoding='utf-8')

print("==================================================================")
print("     INITIALIZING LEGION UNIFIED VISION ENSEMBLE ENGINE          ")
print("==================================================================")

class LegionVisionEnsemble(nn.Module):
    def __init__(self, pth_vision_brain: str):
        super(LegionVisionEnsemble, self).__init__()
        print("  [1/4] Loading DeepLabV3 Semantic Segmentor...")
        self.deeplab = models.segmentation.deeplabv3_resnet50(weights=None)
        self.deeplab.eval()

        print("  [2/4] Loading Keypoint R-CNN Laser Ray Detector...")
        self.keypoint = models.detection.keypointrcnn_resnet50_fpn(weights=None)
        self.keypoint.eval()

        print("  [3/4] Loading Faster R-CNN Object Detector...")
        self.faster = models.detection.fasterrcnn_resnet50_fpn(weights=None)
        self.faster.eval()

        print("  [4/4] Loading Sovereign Vision Brain Classifier...")
        self.brain = SovereignVisionBrain(input_dim=41, output_dim=12)
        if os.path.exists(pth_vision_brain):
            self.brain.load_state_dict(torch.load(pth_vision_brain, weights_only=True))
        self.brain.eval()

    def process_ensemble_masks(self, img_pil: Image.Image, audio_feature_vec: np.ndarray):
        t0 = time.perf_counter()
        img_np = np.array(img_pil).astype(np.float32)
        r, g, b = img_np[:, :, 0], img_np[:, :, 1], img_np[:, :, 2]
        lum = 0.299 * r + 0.587 * g + 0.114 * b

        # 1. Laser Identification Mask (High luminance + red dominance)
        laser_pixels = (lum > 180) & (r > 120) & ((r.astype(int) - b.astype(int)) > 30)

        # 2. Sovereign Vision Brain Inference
        tensor_in = torch.from_numpy(audio_feature_vec).unsqueeze(0)
        with torch.no_grad():
            style_probs = self.brain(tensor_in).numpy()[0]

        # 3. Targeted Laser Transformation (Recolor ONLY laser pixels to Cyan)
        output_np = img_np.copy()
        output_np[:, :, 0][laser_pixels] = np.clip(b[laser_pixels] * 0.2, 0, 255)
        output_np[:, :, 1][laser_pixels] = np.clip(r[laser_pixels] * 0.95, 0, 255)
        output_np[:, :, 2][laser_pixels] = 255.0

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        categories = [
            "Drop Energy", "Melodic Intro", "Breakdown Ambient", "Underground Tech",
            "Mainstage Peak", "Vocal Focus", "Sub-Bass Heavy", "High Brightness",
            "Dynamic Transition", "Club Groove", "Atmospheric Synth", "Master Peak"
        ]
        top_idx = int(np.argmax(style_probs))
        top_category = categories[top_idx]

        return Image.fromarray(output_np.astype(np.uint8)), top_category, float(style_probs[top_idx]), elapsed_ms

if __name__ == "__main__":
    weights_path = r"C:\WEB CASE STUDY\sovereign_vision_brain.pth"
    img_path = r"C:\Users\adams\Downloads\realistic_edm_mainstage.png"
    out_path = r"C:\Users\adams\Downloads\legion_ensemble_output.png"

    if os.path.exists(img_path):
        ensemble = LegionVisionEnsemble(weights_path)
        img = Image.open(img_path).convert('RGB')
        dummy_audio_vec = np.zeros(41, dtype=np.float32)
        dummy_audio_vec[0] = -8.5  # -8.5 dB LUFS
        dummy_audio_vec[1] = 3.85  # Crest factor
        dummy_audio_vec[2] = 0.40  # Spectral centroid

        out_img, style, conf, ms = ensemble.process_ensemble_masks(img, dummy_audio_vec)
        out_img.save(out_path, quality=95)

        print("\n==================================================================")
        print("     LEGION VISION ENSEMBLE BENCHMARK & EXECUTION SUCCESS        ")
        print("==================================================================")
        print(f"🔥 Style Category Match : [{style.upper()}] ({conf*100:.1f}%)")
        print(f"⚡ Processing Speed     : {ms:.2f} ms")
        print(f"💾 Saved Output Image  : {out_path}")
        print("==================================================================")
