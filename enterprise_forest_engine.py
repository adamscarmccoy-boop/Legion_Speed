import os
import json
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyArrowPatch
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import cross_val_score
from math import pi
import sys

# Force output to UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# ── CONFIGURATION ────────────────────────────────────────────────────────────
DATA_PATH = r"C:\WEB CASE STUDY\als_master_data.parquet"
MARKET_PATH = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\fused_web_data.json"
OUTPUT_IMAGE = "forest_engine_enterprise_dashboard.png"

print("=== Starting Enterprise Forest Engine ===")

# ── 1. LOAD DATA ─────────────────────────────────────────────────────────────
try:
    print("Fetching audio features from Onyx API...")
    res = requests.post('http://localhost:8002/query/duckdb', 
                        json={'sql_query': 'SELECT * FROM audio_features;'})
    data = res.json()
    if data['status'] == 'success':
        df = pd.DataFrame(data['results'])
    else:
        print(f"API Error: {data}")
        sys.exit(1)
except Exception as e:
    print(f"Error fetching from API: {e}")
    sys.exit(1)

try:
    print(f"Loading market intel from {MARKET_PATH}...")
    with open(MARKET_PATH, 'r', encoding='utf-8') as f:
        market_raw = json.load(f)
    market_df = pd.DataFrame(market_raw if isinstance(market_raw, list) else list(market_raw.values()))
except Exception as e:
    print(f"Warning: Could not load market data: {e}. Proceeding with DSP only.")
    market_df = pd.DataFrame()

print(f"DSP Catalog:  {len(df)} tracks")
if not market_df.empty:
    print(f"Market Intel: {len(market_df)} records")

# ── 2. LABELING ───────────────────────────────────────────────────────────────
ARTIST_MAP = {
    'chris lake':         'Chris Lake',
    'fisher':             'Fisher',
    'charlotte de witte': 'Charlotte de Witte',
    'sam shure':          'Sam Shure',
    'eli brown':          'Eli Brown',
}

def label_artist(path):
    if not isinstance(path, str): return 'Other'
    p = path.lower()
    for key, name in ARTIST_MAP.items():
        if key in p:
            return name
    return 'Other'

if 'filepath' in df.columns:
    df['artist'] = df['filepath'].apply(label_artist)
elif 'filename' in df.columns:
    df['artist'] = df['filename'].apply(label_artist)
else:
    print("Error: No filepath or filename column found for labeling.")
    sys.exit(1)

# ── 3. FEATURE FUSION ─────────────────────────────────────────────────────────
POTENTIAL_FEATURES = ['tempo', 'rms_db', 'crest_factor', 'sub_bass_energy', 
                      'bass_energy', 'mid_energy', 'high_energy', 'spectral_centroid']
DSP_FEATURES = [f for f in POTENTIAL_FEATURES if f in df.columns]

if not market_df.empty and 'artist_name' in market_df.columns:
    artist_market = market_df.groupby('artist_name').agg(
        market_popularity=('popularity','mean') if 'popularity' in market_df.columns else ('popularity', lambda x: 0),
        market_trending=('trending_score','mean') if 'trending_score' in market_df.columns else ('trending_score', lambda x: 0)
    ).reset_index().rename(columns={'artist_name':'artist'})

    df = df.merge(artist_market, on='artist', how='left')
    df['market_popularity'] = df['market_popularity'].fillna(df['market_popularity'].median() if not df['market_popularity'].isna().all() else 0)
    df['market_trending'] = df['market_trending'].fillna(0)
    
    ALL_FEATURES = DSP_FEATURES + ['market_popularity', 'market_trending']
else:
    print("Using DSP features only.")
    ALL_FEATURES = DSP_FEATURES

df_clean = df.dropna(subset=ALL_FEATURES + ['artist']).copy()
X = df_clean[ALL_FEATURES]
y_labels = df_clean['artist']

# ── 4. SCALE + ENCODE ─────────────────────────────────────────────────────────
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
le = LabelEncoder()
y = le.fit_transform(y_labels)

class_counts = y_labels.value_counts()
valid_classes = class_counts[class_counts >= 5].index
df_clean = df_clean[df_clean['artist'].isin(valid_classes)].copy()

if len(df_clean) == 0:
    print("Error: No classes with enough samples (>=5) found for training.")
    sys.exit(1)

X = df_clean[ALL_FEATURES]
y_labels = df_clean['artist']
le = LabelEncoder()
y = le.fit_transform(y_labels)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print(f"Training on {len(df_clean)} tracks across {len(le.classes_)} classes: {list(le.classes_)}")

# ── 5. RANDOM FOREST ──────────────────────────────────────────────────────────
rf = RandomForestClassifier(n_estimators=500, random_state=42,
                             class_weight='balanced', n_jobs=-1)
rf.fit(X_scaled, y)
y_pred = rf.predict(X_scaled)

n_min_class = pd.Series(y).value_counts().min()
n_splits = min(5, n_min_class) if n_min_class > 1 else 2
try:
    cv_scores = cross_val_score(rf, X_scaled, y, cv=n_splits, scoring='f1_weighted')
    cv_mean = cv_scores.mean()
    cv_std = cv_scores.std()
except:
    cv_mean, cv_std = 0, 0

print(f"\n{'='*60}")
print("FOREST ENGINE -- CLASSIFICATION REPORT")
print(f"{'='*60}")
print(classification_report(y, y_pred, target_names=le.classes_))
print(f"Cross-Val F1 ({n_splits}-fold): {cv_mean:.3f} +/- {cv_std:.3f}")

# ── 6. ISOLATION FOREST ───────────────────────────────────────────────────────
iso = IsolationForest(n_estimators=200, contamination=0.08, random_state=42)
df_clean['anomaly_score'] = iso.fit_predict(X_scaled)
df_clean['outlier'] = df_clean['anomaly_score'] == -1

print(f"Isolation Forest: {df_clean['outlier'].sum()} anomalous tracks flagged")

# ── 7. VISUAL DASHBOARD ───────────────────────────────────────────────────────
plt.style.use('dark_background')
fig = plt.figure(figsize=(22, 20), facecolor='#0d0d14')
gs  = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)
PALETTE = ['#00f0ff','#ff3cac','#ffe600','#7dff8a','#ff6b35','#c77dff']

ax_imp = fig.add_subplot(gs[0, :2])
importances = rf.feature_importances_
feat_order = np.argsort(importances)[::-1]
feat_names = ALL_FEATURES
colors_imp = [PALETTE[i % len(PALETTE)] for i in range(len(feat_names))]
bars = ax_imp.barh([feat_names[i] for i in feat_order],
                   [importances[i] for i in feat_order],
                   color=[colors_imp[i] for i in feat_order])
ax_imp.set_facecolor('#13131f')
ax_imp.set_title('🔑 FEATURE IMPORTANCES', color='white', fontsize=13, fontweight='bold')
ax_imp.tick_params(colors='white')
for bar, val in zip(bars, [importances[i] for i in feat_order]):
    ax_imp.text(val + 0.002, bar.get_y() + bar.get_height()/2, f'{val*100:.1f}%', va='center', color='white', fontsize=9)

ax_mkt = fig.add_subplot(gs[0, 2])
if not market_df.empty:
    mkt_summary = df_clean.groupby('artist')['market_popularity'].mean().sort_values(ascending=False)
    ax_mkt.barh(mkt_summary.index, mkt_summary.values, color='#00f0ff')
ax_mkt.set_facecolor('#13131f')
ax_mkt.set_title('📈 MARKET POPULARITY', color='white', fontsize=12, fontweight='bold')
ax_mkt.tick_params(colors='white')

ax_cm = fig.add_subplot(gs[1, 0])
cm = confusion_matrix(y, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=le.classes_)
disp.plot(ax=ax_cm, colorbar=False, cmap='plasma')
ax_cm.set_facecolor('#13131f')
ax_cm.set_title('🎯 CONFUSION MATRIX', color='white', fontsize=12, fontweight='bold')
ax_cm.tick_params(colors='white', labelsize=7)

ax_radar = fig.add_subplot(gs[1, 1:], polar=True)
radar_feats = [f for f in POTENTIAL_FEATURES if f in df_clean.columns]
N = len(radar_feats)
angles = [n / float(N) * 2 * pi for n in range(N)] + [0]
ax_radar.set_facecolor('#13131f')
ax_radar.set_title('🕸️ DSP FINGERPRINT RADAR', color='white', fontsize=12, fontweight='bold', pad=20)
ax_radar.set_xticks(angles[:-1])
ax_radar.set_xticklabels(radar_feats, size=8, color='#ccc')
ax_radar.set_yticklabels([])

scaler_radar = StandardScaler()
radar_scaled = pd.DataFrame(scaler_radar.fit_transform(df_clean[radar_feats]), columns=radar_feats)
df_radar = pd.concat([df_clean[['artist']].reset_index(drop=True), radar_scaled], axis=1)

for i, artist in enumerate(sorted(df_clean['artist'].unique())):
    group = df_radar[df_radar['artist'] == artist][radar_feats].mean()
    vals = group.tolist() + [group.tolist()[0]]
    ax_radar.plot(angles, vals, color=PALETTE[i % len(PALETTE)], linewidth=2, label=artist)
    ax_radar.fill(angles, vals, color=PALETTE[i % len(PALETTE)], alpha=0.08)
ax_radar.legend(loc='upper right', bbox_to_anchor=(1.35, 1.1), fontsize=8, labelcolor='white')

ax_anom = fig.add_subplot(gs[2, :2])
ax_anom.set_facecolor('#13131f')
if 'rms_db' in df_clean.columns and 'sub_bass_energy' in df_clean.columns:
    normal = df_clean[~df_clean['outlier']]
    outlier = df_clean[df_clean['outlier']]
    for i, artist in enumerate(sorted(normal['artist'].unique())):
        grp = normal[normal['artist'] == artist]
        ax_anom.scatter(grp['rms_db'], grp['sub_bass_energy'], color=PALETTE[i % len(PALETTE)], alpha=0.6, s=20, label=artist)
    ax_anom.scatter(outlier['rms_db'], outlier['sub_bass_energy'], color='red', alpha=0.9, s=60, marker='X', label='Anomaly')
ax_anom.set_title('🚨 ANOMALY DETECTION', color='white', fontsize=12, fontweight='bold')
ax_anom.set_xlabel('RMS dB', color='#aaa')
ax_anom.set_ylabel('Sub Bass Energy', color='#aaa')
ax_anom.tick_params(colors='white')
ax_anom.legend(fontsize=8, labelcolor='white')

ax_prob = fig.add_subplot(gs[2, 2])
ax_prob.set_facecolor('#13131f')
your_track = pd.DataFrame([dict(zip(ALL_FEATURES, X_scaled.mean(axis=0)))])
proba = rf.predict_proba(your_track)[0]
sorted_idx = np.argsort(proba)[::-1]
ax_prob.barh([le.classes_[i] for i in sorted_idx], [proba[i] for i in sorted_idx], color='#00f0ff')
ax_prob.set_title('🎲 STYLE PROBABILITY', color='white', fontsize=12, fontweight='bold')
ax_prob.set_xlim(0, 1)
ax_prob.tick_params(colors='white')

fig.suptitle('🌲 FOREST ENGINE ENTERPRISE — DSP Intelligence + Market Fusion', color='white', fontsize=16, fontweight='bold', y=0.98)
plt.savefig(OUTPUT_IMAGE, dpi=150, bbox_inches='tight', facecolor='#0d0d14')
print(f"\nDashboard saved -> {OUTPUT_IMAGE}")
print(f"Processed {len(df_clean)} tracks across {len(le.classes_)} classes.")
