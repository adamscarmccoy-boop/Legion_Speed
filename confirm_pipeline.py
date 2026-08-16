import os
import numpy as np
import torch
import librosa
import soundfile as sf

# =========================
# PATHS
# =========================
BASE = r"C:\WEB CASE STUDY\Snoop_Stylizer_App"

PROFILE_PATH = os.path.join(BASE, "Snoop_segment_profile.pt")
ROUTER_PATH  = os.path.join(BASE, "Snoop_segment_router.pt")
AUDIO_PATH   = os.path.join(BASE, "training_audio", "snoop_train_00010.wav")

OUT_DIR = os.path.join(BASE, "confirm_outputs")
os.makedirs(OUT_DIR, exist_ok=True)

# =========================
# LOAD MODELS
# =========================
profile = torch.load(PROFILE_PATH, map_location="cpu", weights_only=False)
router  = torch.load(ROUTER_PATH,  map_location="cpu", weights_only=False)

model = torch.nn.Sequential(
    torch.nn.Linear(57, 128),
    torch.nn.ReLU(),
    torch.nn.Linear(128, 64),
    torch.nn.ReLU(),
    torch.nn.Linear(64, 12),
)

model.load_state_dict(router["model_state_dict"])
model.eval()

print("✔ Models loaded")

# =========================
# FEATURE
# =========================
def extract_features(y, sr):
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    zcr = librosa.feature.zero_crossing_rate(y)

    vec = np.concatenate([
        np.mean(mfcc, axis=1),
        [np.mean(centroid)],
        [np.mean(zcr)]
    ])

    if len(vec) < 57:
        vec = np.pad(vec, (0, 57 - len(vec)))
    else:
        vec = vec[:57]

    return vec.astype(np.float32)

def normalize(x):
    mean = np.array(router["scaler_mean"])
    scale = np.array(router["scaler_scale"])
    return (x - mean) / (scale + 1e-8)

# =========================
# LOAD AUDIO
# =========================
y, sr = librosa.load(AUDIO_PATH, sr=22050)
print("✔ Audio loaded:", len(y))

step = int(sr * 0.75)

# =========================
# TEST 1: RAW ROUTER OUTPUT
# =========================
print("\n=== TEST 1: ROUTER CLUSTERS ===")

clusters = []

for i in range(0, len(y) - step, step):
    seg = y[i:i+step]

    seg = preprocess(seg, sr)
    feat = extract_features(seg, sr)
    feat = normalize(feat)

    x = torch.tensor(feat, dtype=torch.float32).unsqueeze(0)

    with torch.no_grad():
        logits = model(x)
        c = torch.argmax(logits).item()

    clusters.append(c)

print("Clusters sample:", clusters[:40])

# =========================
# TEST 2: NO SMOOTHING AUDIO
# =========================
print("\n=== TEST 2: RAW OUTPUT (NO SMOOTHING) ===")

out_raw = np.zeros_like(y)

for i in range(0, len(y) - step, step):
    seg = y[i:i+step]

    feat = extract_features(seg, sr)
    feat = normalize(feat)

    x = torch.tensor(feat, dtype=torch.float32).unsqueeze(0)

    with torch.no_grad():
        c = torch.argmax(model(x)).item()

    target = profile["cluster_centroids"][c]
    gain = 1.0 + (target[1] * 0.1)

    out_raw[i:i+step] = seg * gain

sf.write(os.path.join(OUT_DIR, "output_raw.wav"), out_raw, sr)
print("Saved: output_raw.wav")

# =========================
# TEST 3: SMOOTHED OUTPUT
# =========================
print("\n=== TEST 3: SMOOTHED OUTPUT ===")

out_smooth = np.zeros_like(y)
prev_gain = 1.0

for i in range(0, len(y) - step, step):
    seg = y[i:i+step]

    feat = extract_features(seg, sr)
    feat = normalize(feat)

    x = torch.tensor(feat, dtype=torch.float32).unsqueeze(0)

    with torch.no_grad():
        c = torch.argmax(model(x)).item()

    target = profile["cluster_centroids"][c]
    gain = 1.0 + (target[1] * 0.1)

    # smoothing
    gain = 0.9 * prev_gain + 0.1 * gain
    prev_gain = gain

    out_smooth[i:i+step] = seg * gain

sf.write(os.path.join(OUT_DIR, "output_smooth.wav"), out_smooth, sr)
print("Saved: output_smooth.wav")

# =========================
# TEST 4: SLOW INFERENCE (REALISTIC)
# =========================
print("\n=== TEST 4: SLOW INFERENCE ===")

out_slow = np.zeros_like(y)
prev_gain = 1.0
last_cluster = 0

for idx, i in enumerate(range(0, len(y) - step, step)):
    seg = y[i:i+step]

    # run model only every 4 segments
    if idx % 4 == 0:
        feat = extract_features(seg, sr)
        feat = normalize(feat)

        x = torch.tensor(feat, dtype=torch.float32).unsqueeze(0)

        with torch.no_grad():
            last_cluster = torch.argmax(model(x)).item()

    target = profile["cluster_centroids"][last_cluster]
    gain = 1.0 + (target[1] * 0.1)

    gain = 0.9 * prev_gain + 0.1 * gain
    prev_gain = gain

    out_slow[i:i+step] = seg * gain

sf.write(os.path.join(OUT_DIR, "output_slow.wav"), out_slow, sr)
print("Saved: output_slow.wav")

print("\n✔ ALL TESTS COMPLETE")