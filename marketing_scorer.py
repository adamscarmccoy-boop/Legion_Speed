import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, IsolationForest

class MarketingScorer:
    def __init__(self):
        print("🌲 INITIALIZING MARKETING SCORER / FOREST ENGINE...")
        FEATURES_PATH = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/exported_json/duckdb_audio_features.json"
        MARKET_PATH   = r"c:/STUDIES_BACKUP/Legion-Jacked-Pipeline/ableton-session-intelligence/fused_web_data.json"
        
        with open(FEATURES_PATH, 'r', encoding='utf-8') as f:
            df = pd.DataFrame(json.load(f))
            
        with open(MARKET_PATH, 'r', encoding='utf-8') as f:
            market_raw = json.load(f)
        market_df = pd.DataFrame(market_raw if isinstance(market_raw, list) else list(market_raw.values()))
        market_df = market_df[['artist_name','popularity','trending_score','dsp_rms','dsp_crest',
                               'dsp_sub','dsp_bass','dsp_mid','dsp_high']].dropna(subset=['dsp_rms'])
                               
        ARTIST_MAP = {
            'chris lake':         'Chris Lake',
            'fisher':             'Fisher',
            'charlotte de witte': 'Charlotte de Witte',
            'sam shure':          'Sam Shure',
            'eli brown':          'Eli Brown',
        }

        def label_artist(path):
            p = str(path).lower()
            for key, name in ARTIST_MAP.items():
                if key in p: return name
            return 'Other'

        df['artist'] = df['filepath'].apply(label_artist)
        
        self.DSP_FEATURES = ['tempo','rms_db','crest_factor','sub_bass_energy',
                             'bass_energy','mid_energy','high_energy','spectral_centroid']

        artist_market = market_df.groupby('artist_name').agg(
            market_popularity=('popularity','mean'),
            market_trending=('trending_score','mean')
        ).reset_index().rename(columns={'artist_name':'artist'})

        df = df.merge(artist_market, on='artist', how='left')
        df['market_popularity'] = df['market_popularity'].fillna(df['market_popularity'].median())
        df['market_trending']   = df['market_trending'].fillna(0)

        self.ALL_FEATURES = self.DSP_FEATURES + ['market_popularity', 'market_trending']
        df_clean = df.dropna(subset=self.ALL_FEATURES + ['artist'])
        
        class_counts = df_clean['artist'].value_counts()
        valid_classes = class_counts[class_counts >= 5].index
        df_clean = df_clean[df_clean['artist'].isin(valid_classes)].copy()
        
        X = df_clean[self.ALL_FEATURES]
        y_labels = df_clean['artist']
        
        self.le = LabelEncoder()
        y = self.le.fit_transform(y_labels)
        
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        self.rf = RandomForestClassifier(n_estimators=500, random_state=42, class_weight='balanced', n_jobs=-1)
        self.rf.fit(X_scaled, y)
        
        self.iso = IsolationForest(n_estimators=200, contamination=0.08, random_state=42)
        self.iso.fit(X_scaled)
        
        self.mean_popularity = df_clean['market_popularity'].mean()
        self.mean_trending = df_clean['market_trending'].mean()
        print("✅ Forest Engine Ready.")

    def score_track(self, track_features_dict: dict):
        """
        Takes raw DSP features, fills in market stats, and predicts Marketing Score / Style.
        """
        # Ensure we have defaults for missing DSP
        for f in self.DSP_FEATURES:
            if f not in track_features_dict:
                track_features_dict[f] = 0.0
                
        # Fill in average market stats for prediction
        track_features_dict['market_popularity'] = self.mean_popularity
        track_features_dict['market_trending'] = self.mean_trending
        
        # Order features correctly
        ordered_features = [track_features_dict[f] for f in self.ALL_FEATURES]
        
        # Scale
        X_test = self.scaler.transform([ordered_features])
        
        # Predict
        proba = self.rf.predict_proba(X_test)[0]
        sorted_idx = np.argsort(proba)[::-1]
        
        predictions = []
        for i in sorted_idx:
            predictions.append({
                "style": self.le.classes_[i],
                "probability": float(proba[i])
            })
            
        anomaly_score = int(self.iso.predict(X_test)[0]) # -1 for anomaly, 1 for normal
        
        return {
            "top_match": predictions[0]["style"],
            "marketing_score_confidence": predictions[0]["probability"],
            "is_anomaly": anomaly_score == -1,
            "full_style_breakdown": predictions
        }
