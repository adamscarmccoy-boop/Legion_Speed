import os
import glob
import numpy as np
import librosa
import torch
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# =========================
# CONFIG
# =========================
AUDIO_DIR = r"C:\WEB CASE STUDY\Snoop_Stylizer_App\training_audio"
OUT_DIR   = r"C:\WEB CASE STUDY\Snoop_Stylizer_App"

N_CLUSTERS = 12
SR = 22050
SEGMENT_SEC = 0.75

# =========================
# AUDIO VALIDATION
# =========================
def valid_audio(y):
    if len(y) < 1000:
        return False
    if np.isnan(y).any():
        return False

    rms = np.sqrt(np.mean(y**2))
    if rms < 1e-4:
        return False

    if np.max(np.abs(y)) > 1.5:
        return False

    return True

# =========================
# FAST FEATURES (57 dim)
# =========================
def extract_features(y):
    mfcc = librosa.feature.mfcc(y=y, sr=SR, n_mfcc=13)
    centroid = librosa.feature.spectral_centroid(y=y, sr=SR)
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

# =========================
# TEMPORAL SMOOTHING
# =========================
def smooth_sequence(X, alpha=0.85):
    out = []
    prev = X[0]

    for x in X:
        x = alpha * prev + (1 - alpha) * x
        out.append(x)
        prev = x

    return np.array(out)

# =========================
# LOAD AUDIO + BUILD DATASET
# =========================
print("\nLoading audio...\n")

files = glob.glob(os.path.join(AUDIO_DIR, "*.wav"))

X = []

for f in files:
    print("Processing:", os.path.basename(f))

    y, _ = librosa.load(f, sr=SR)

    step = int(SR * SEGMENT_SEC)

    feats = []

    for i in range(0, len(y) - step, step):
        seg = y[i:i+step]

        if not valid_audio(seg):
            continue

        feat = extract_features(seg)
        feats.append(feat)

    if len(feats) == 0:
        continue

    feats = smooth_sequence(feats)

    X.extend(feats)

X = np.array(X)

print("\nTotal segments:", len(X))

# =========================
# NORMALIZE
# =========================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# =========================
# CLUSTER
# =========================
print("\nClustering...")

kmeans = KMeans(
    n_clusters=N_CLUSTERS,
    n_init=20,
    max_iter=500,
    random_state=42
)

cluster_ids = kmeans.fit_predict(X_scaled)

# =========================
# CLUSTER STABILITY FIX
# =========================
print("Stabilizing clusters...")

stable = []
last = cluster_ids[0]

for c in cluster_ids:
    if c != last:
        if np.random.rand() < 0.6:
            c = last
    stable.append(c)
    last = c

cluster_ids = np.array(stable)

# =========================
# TRAIN ROUTER
# =========================
print("\nTraining router...")

model = torch.nn.Sequential(
    torch.nn.Linear(57, 128),
    torch.nn.ReLU(),
    torch.nn.Linear(128, 64),
    torch.nn.ReLU(),
    torch.nn.Linear(64, N_CLUSTERS),
)

optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = torch.nn.CrossEntropyLoss()

X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
y_tensor = torch.tensor(cluster_ids, dtype=torch.long)

for epoch in range(60):
    optimizer.zero_grad()
    logits = model(X_tensor)
    loss = loss_fn(logits, y_tensor)
    loss.backward()
    optimizer.step()

    if epoch % 10 == 0:
        pred = torch.argmax(logits, dim=1)
        acc = (pred == y_tensor).float().mean().item()
        print(f"epoch {epoch} | loss={loss.item():.4f} | acc={acc:.3f}")

# =========================
# SAVE OUTPUTS
# =========================
profile = {
    "cluster_centroids": kmeans.cluster_centers_,
    "scaler_mean": scaler.mean_,
    "scaler_scale": scaler.scale_,
}

router = {
    "model_state_dict": model.state_dict(),
    "input_dim": 57,
    "n_clusters": N_CLUSTERS,
    "scaler_mean": scaler.mean_,
    "scaler_scale": scaler.scale_,
}

torch.save(profile, os.path.join(OUT_DIR, "Snoop_segment_profile.pt"))
torch.save(router, os.path.join(OUT_DIR, "Snoop_segment_router.pt"))

print("\nDONE.")
print("Saved weights.")