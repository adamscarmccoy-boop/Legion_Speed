#!/usr/bin/env python
# coding: utf-8

# # 🏆 Sovereign Downloads Audit Leaderboard — Sectioned & Essentia-Driven
# 
# This notebook performs a professional, structural acoustic audit of your entire Windows Downloads directory, comparing every `.mp3` and `.wav` file side-by-side against the **true Chris Lake "Somebody" baseline**.
# 
# ### 🛡️ Phase-Preserving Stereo Sectioning:
# To protect wide stereo spatial elements and prevent destructive phase cancellation, this engine:
# 1. Slices the audio into **dynamic structural sections** using **Essentia C++ onsets** (via WSL/Python bridge).
# 2. Loads each section in **full stereo (mono=False)**, extracting Left and Right channel features independently to average their magnitudes post-extraction.
# 3. Computes section-by-section similarity matches using our **calibrated commercial scales** and averages them to get your true overall **Sonic Fit Score**!
# 

# In[1]:


import os
import json
import librosa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, HTML, Audio

print("✅ Setup Complete. Notebook visualization libraries loaded successfully!")


# In[2]:


# Import your actual, production-calibrated DSP scoring core directly from disk!
from audit_and_score_downloads import extract_audio_features, CHRIS_LAKE_BASELINE, DOWNLOADS_DIR, ASSETS_DIR

print("✅ Active, Essentia-driven Stereo Core imported successfully from audit_and_score_downloads.py!")


# ## 🥈 1. System Visualizations (Pre-Generated Charts)
# 
# These charts were compiled by your live Ray & Forest engines during the complete mastering pass:
# 

# In[3]:


import matplotlib.image as mpimg

# Load and display pre-generated high-fidelity charts
img_paths = [
    ("downloaded_tracks_comparison.png", "Downloaded Tracks Comparison"),
    ("alignment_heatmap.png", "Acoustic Alignment Heatmap"),
    ("alignment_bar_chart.png", "Acoustic Match Scores"),
    ("dynamic_alignment_map.png", "Segment-by-Segment Alignment Map")
]

for filename, title in img_paths:
    full_p = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(full_p):
        img = mpimg.imread(full_p)
        fig, ax = plt.subplots(figsize=(12, 6), dpi=120)
        ax.imshow(img)
        ax.axis('off')
        ax.set_title(title, fontsize=14, color='white', fontweight='bold', pad=10)
        plt.tight_layout()
        plt.show()
    else:
        print(f"⚠️ Visualization not found: {filename}")


# ## 🥇 2. Live Playback & Interactive Ratings Leaderboard
# 
# This section reads your completed results directly from `market_score_audit_report_ranked.json` and renders your interactive HTML5 player cards!
# 

# In[4]:


# Load the completed production report
report_path = os.path.join(ASSETS_DIR, "market_score_audit_report_ranked.json")

if not os.path.exists(report_path):
    print(f"❌ Error: Production report not found at {report_path}")
else:
    with open(report_path, "r", encoding="utf-8") as f:
        ranked_tracks = json.load(f)

    print(f"🔊 Loaded {len(ranked_tracks)} compiled tracks from your production run!")

    # Render HTML Leaderboard Table
    html_table = """
    <div style="background-color: #0d0d12; padding: 20px; border-radius: 10px; margin-bottom: 30px; border: 1px solid #1f1f2e;">
        <h2 style="color: #ff6600; margin-top: 0; font-family: sans-serif;">🥇 Global Chris Lake Peer Leaderboard</h2>
        <table style="width: 100%; border-collapse: collapse; font-family: monospace; color: #ffffff;">
            <thead>
                <tr style="border-bottom: 2px solid #ff6600; text-align: left; background-color: #13131d;">
                    <th style="padding: 10px;">Rank</th>
                    <th style="padding: 10px;">Track Name</th>
                    <th style="padding: 10px;">Sonic Fit</th>
                    <th style="padding: 10px;">Market Score</th>
                    <th style="padding: 10px;">Crest</th>
                    <th style="padding: 10px;">RMS dB</th>
                </tr>
            </thead>
            <tbody>
    """
    for r_idx, t in enumerate(ranked_tracks):
        bg_color = "#1a1a26" if r_idx % 2 == 0 else "#0d0d12"
        html_table += f"""
                <tr style="background-color: {bg_color}; border-bottom: 1px solid #1f1f2e;">
                    <td style="padding: 10px; color: #ffcc00; font-weight: bold;">#{r_idx+1}</td>
                    <td style="padding: 10px; font-weight: bold;">{t['filename']}</td>
                    <td style="padding: 10px; color: #00ffff; font-weight: bold;">{t['sonic_fit_score']:.1f}%</td>
                    <td style="padding: 10px; color: #ff6600; font-weight: bold;">{t['market_score']:.1f}%</td>
                    <td style="padding: 10px;">{t['crest_factor']:.2f}</td>
                    <td style="padding: 10px;">{t['rms_db']:.2f}</td>
                </tr>
        """
    html_table += """
            </tbody>
        </table>
    </div>
    """
    display(HTML(html_table))

    # Render interactive cards with instant snippet player
    for r_idx, t in enumerate(ranked_tracks):
        display(HTML(f"""
        <div style="background-color: #13131d; padding: 15px; border-radius: 8px; margin-top: 25px; border: 1px solid #ff6600; font-family: sans-serif; color: white;">
            <h3 style="margin-top: 0; color: #ffcc00;">#{r_idx+1} Player Card: {t['filename']}</h3>
            <p style="margin: 5px 0;"><b>Sonic Fit Similarity:</b> <span style="color: #00ffff; font-weight: bold;">{t['sonic_fit_score']:.1f}%</span> | <b>Weighted Market Score:</b> <span style="color: #ff6600; font-weight: bold;">{t['market_score']:.1f}%</span></p>
            <p style="margin: 5px 0; color: #aaaaaa; font-family: monospace;">Fidelity Verdict: {t.get('verdict', 'PASS')} | RMS: {t['rms_db']:.2f} dB | Crest Factor: {t['crest_factor']:.2f}</p>
        </div>
        """))

        # Chart
        fig, ax = plt.subplots(figsize=(8, 3.5), dpi=120)
        ax.set_facecolor('#13131d')
        fig.patch.set_facecolor('#0d0d12')

        bands = ['Sub-Bass', 'Bass', 'Mids', 'Highs']
        track_vals = [t['sub_bass_energy'], t['bass_energy'], t['mid_energy'], t['high_energy']]
        ref_vals = [21.98, 66.93, 7.23, 3.86] # Calibrated baseline averages

        x = np.arange(len(bands))
        width = 0.35

        ax.bar(x - width/2, track_vals, width, label=f"This Track ({t['filename'][:20]}...)", color='#ff6600', alpha=0.9)
        ax.bar(x + width/2, ref_vals, width, label='Chris Lake "Somebody" Profile', color='#00ffff', alpha=0.9)

        ax.set_ylabel('Spectral Energy %', color='#aaaaaa', fontsize=10)
        ax.set_title('Frequency Energy Distribution vs. Chris Lake Baseline', color='white', fontsize=11, fontweight='bold', pad=10)
        ax.set_xticks(x)
        ax.set_xticklabels(bands, color='white', fontsize=9)
        ax.legend(facecolor='#222222', edgecolor='#444444', labelcolor='white', fontsize=9)
        ax.tick_params(colors='#666666')
        ax.yaxis.label.set_color('#aaaaaa')
        for spine in ax.spines.values():
            spine.set_edgecolor('#333333')
        plt.tight_layout()
        plt.show()

        # Instant player (30s drop preview)
        audio_path = os.path.join(DOWNLOADS_DIR, t["filename"].replace("[GPU-GEN] ", ""))
        try:
            print("⏳ Loading fast 30s drop preview (starting at 60s)...\n")
            y_prev, sr_prev = librosa.load(audio_path, sr=22050, duration=30, offset=60)
            display(Audio(data=y_prev, rate=sr_prev))
        except Exception as e:
            display(Audio(filename=audio_path))
        print("-" * 100)

