# smart_mastering_pipeline.py
import os
import sys
import time
import json
import numpy as np
import pandas as pd
import ray
import torch
import torch.nn as nn
import torch.optim as optim
import torchaudio
from pedalboard import Pedalboard, Compressor, HighpassFilter, Gain, Limiter, Clipping
from pedalboard.io import AudioFile
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from scipy.spatial.distance import cdist
from scipy import signal
from typing import Optional, Dict, Any, List

# Ensure Ray is initialized for actor creation
if not ray.is_initialized():
    # Connect to the existing Legion Ray cluster
    try:
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        print("Connected to existing Ray cluster.")
    except ConnectionError:
        print("No existing Ray cluster found. Spinning up a new local Ray cluster with strict memory limits...")
        ray.init(namespace="legion", object_store_memory=1500 * 1024 * 1024, _temp_dir=r"C:\tmp\ray", ignore_reinit_error=True, runtime_env={"env_vars": {"PYTHONPATH": r"c:\WEB CASE STUDY;c:\WEB CASE STUDY\sonic_dna_engine;c:\WEB CASE STUDY\antigravity_vscode_ext\backend"}})


# --- Mock PyTorch Synthesis Network ---
# This network takes a 'vibe vector' (e.g., desired RMS, Crest Factor, etc.)
# and outputs suggested Pedalboard parameters.
class MasteringParamSynthesizer(nn.Module):
    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, 64)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(64, output_dim)
        # Output_dim will be number of parameters:
        # [comp_thresh, comp_ratio, comp_attack, comp_release, gain_db, limiter_thresh, limiter_release]

    def forward(self, x):
        return self.fc2(self.relu(self.fc1(x)))

# --- Ray Actor for Style Classification (based on forest_engine_cell.py) ---
@ray.remote(num_cpus=1)
class StyleClassifierActor:
    def __init__(self):
        self.registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
        self.rf_classifier: Optional[RandomForestClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self.label_encoder: Optional[LabelEncoder] = None
        self.all_features: List[str] = ['tempo', 'rms_db', 'crest_factor', 'sub_bass_energy',
                                        'bass_energy', 'mid_energy', 'high_energy', 'spectral_centroid',
                                        'market_popularity', 'market_trending']
        print("StyleClassifierActor initialized.")
        self._load_model_data()

    def _load_model_data(self):
        """Loads training data from SwarmKnowledgeRegistry and trains the RF model."""
        print("StyleClassifierActor: Loading data for classification model...")
        try:
            # Get duckdb_audio_features and simulated market data (assuming merged)
            df_arrow = ray.get(self.registry.get_table.remote("duckdb_audio_features"))
            df_clean = df_arrow.to_pandas()

            # Mock artist labeling and market data merging (simplified for this example)
            ARTIST_MAP = {
                'chris lake': 'Chris Lake', 'fisher': 'Fisher', 'charlotte de witte': 'Charlotte de Witte',
                'sam shure': 'Sam Shure', 'eli brown': 'Eli Brown', 'djsusan': 'DJ Susan'
            }
            def label_artist(filename):
                p = str(filename).lower()
                for key, name in ARTIST_MAP.items():
                    if key in p: return name
                return 'Other'

            df_clean['artist'] = df_clean['filename'].apply(label_artist)
            
            # Use 'chris_lake_fused_raw' from registry for market data
            market_df_arrow = ray.get(self.registry.get_table.remote("chris_lake_fused_raw"))
            market_df_raw = market_df_arrow.to_pandas()
            artist_market = market_df_raw.groupby('apple_artist').agg(
                market_popularity=('apple_artist','size') # Simplified for demo
            ).reset_index().rename(columns={'apple_artist':'artist', 'market_popularity':'market_popularity'})
            artist_market['market_trending'] = artist_market['market_popularity'] * 0.1 # Mock trending

            df_clean = df_clean.merge(artist_market, on='artist', how='left')
            df_clean['market_popularity'] = df_clean['market_popularity'].fillna(df_clean['market_popularity'].median())
            df_clean['market_trending'] = df_clean['market_trending'].fillna(0)

            df_clean = df_clean.dropna(subset=self.all_features + ['artist'])
            
            # Filter classes with very few samples for stable training
            class_counts = df_clean['artist'].value_counts()
            valid_classes = class_counts[class_counts >= 3].index # Minimum 3 samples per class
            df_clean = df_clean[df_clean['artist'].isin(valid_classes)].copy()

            if df_clean.empty or len(df_clean['artist'].unique()) < 2:
                print("Classifier: Not enough data or classes for training.")
                return

            X = df_clean[self.all_features]
            y_labels = df_clean['artist']

            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            self.label_encoder = LabelEncoder()
            y = self.label_encoder.fit_transform(y_labels)

            self.rf_classifier = RandomForestClassifier(n_estimators=100, random_state=42,
                                                        class_weight='balanced', n_jobs=1) # n_jobs=1 for actor
            self.rf_classifier.fit(X_scaled, y)
            print(f"StyleClassifierActor: Model trained with {len(df_clean)} samples, {len(self.label_encoder.classes_)} classes.")
        except Exception as e:
            print(f"StyleClassifierActor: Failed to load or train model: {e}")
            self.rf_classifier = None # Ensure it's None if training fails

    def predict_style(self, audio_features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predicts the style of an audio track based on its features.
