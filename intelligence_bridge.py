  """
LEGION SONIC ENGINE — Intelligence Bridge
=========================================
This module provides the data ingestion and analysis layer that connects
raw market and audio data to the Ray-distributed Warden.
"""

import os
import json
import pandas as pd
import numpy as np
import ray
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

# --- 1. SCHEMAS ---

class MarketTrend(BaseModel):
    metric: str
    value: float
    direction: str  # "up", "down", "stable"
    description: str

class IntelligenceReport(BaseModel):
    trends: List[MarketTrend]
    audio_baseline: Dict[str, float]
    intelligence_gap: Optional[str] = None

# --- 2. THE BRIDGE ACTOR ---

@ray.remote
class IntelligenceBridge:
    """
    The IntelligenceBridge is a Ray Actor that manages the 'Ground Truth'.
    It ingests market and audio data and provides processed trends and 
    baselines to the Warden.
    """
    def __init__(self, market_data_path: str):
        self.market_data_path = market_data_path
        self.market_df: Optional[pd.DataFrame] = None
        self.baseline_metrics: Dict[str, float] = {}
        self._load_data()

    def _load_data(self):
        """Loads and processes the market data."""
        if os.path.exists(self.market_data_path):
            try:
                # In a production setup, this would also ingest DuckDB/LanceDB
                self.market_df = pd.read_json(self.market_data_path)
                print(f"[IntelligenceBridge] Successfully loaded market data: {self.market_df.shape[0]} records.")
                self._calculate_baselines()
            except Exception as e:
                print(f"[IntelligenceBridge] Error loading data: {e}")
        else:
            print(f"[IntelligenceBridge] Warning: Data path {self.market_data_path} not found.")

    def _calculate_baselines(self):
        """Calculates the 'Industry Standard' metrics from the loaded data."""
        if self.market_df is not None:
            # We look for typical DSP metrics in the market data
            metrics = ['dsp_rms', 'dsp_crest', 'dsp_sub', 'dsp_bass', 'dsp_mid', 'dsp_high']
            for m in metrics:
                if m in self.market_df.columns:
                    self.baseline_metrics[m] = float(self.market_df[m].mean())
            print(f"[IntelligenceBridge] Baselines calculated: {self.baseline_metrics}")

    def get_market_trends(self) -> List[MarketTrend]:
        """Returns a list of current market trends."""
        if self.market_df is None:
            return []
        
        # Mocking trend detection logic for simulation
        # In production, this compares current trends vs historical baselines
        trends = [
            MarketTrend(metric="sub_bass_energy", value=0.45, direction="up", description="Deep sub-bass is trending in tech-house."),
            MarketTrend(metric="rms_loudness", value=-8.5, direction="down", description="Dynamic range is becoming more valued.")
        ]
        return trends

    def get_audio_baseline(self) -> Dict[str, float]:
        return self.baseline_metrics

    def get_intelligence_gap(self, current_audio_metrics: Dict[str, float]) -> Optional[str]:
        """
        The core logic: Compares current audio metrics against the market baseline
        to identify an 'Intelligence Gap'.
        """
        if not self.baseline_metrics:
            return None
        
        # Example: Detect if current sub-bass is significantly lower than market average
        if "dsp_sub" in current_audio_metrics:
            target = self.baseline_metrics.get("dsp_sub", 0.0)
            actual = current_audio_metrics["dsp_sub"]
            
            if actual < (target * 0.7):
                return f"Sub-bass energy is significantly below market baseline ({actual:.2f} vs {target:.2f})."
            
            if actual > (target * 1.3):
                return f"Sub-bass energy is excessively high ({actual:.2f} vs {target:.2f})."

        return None

# --- 3. TEST RUNNER ---

if __name__ == "__main__":
    if not ray.is_initialized():
        ray.init(namespace="legion", ignore_reinit_error=True)

    print("[LAUNCH] Testing Intelligence Bridge Actor...")
    
    # Using the dummy file we found earlier
    test_path = r"C:\WEB CASE STUDY\data\chris_lake_fused_raw.json"
    
    bridge = IntelligenceBridge.remote(test_path)
    
    # Test baseline retrieval
    baselines = ray.get(bridge.get_audio_baseline.remote())
    print(f"Baselines: {baselines}")
    
    # Test gap detection
    gap = ray.get(bridge.get_intelligence_gap.remote({"dsp_sub": 5.0})) # Very low
    print(f"Detected Gap: {gap}")
    
    ray.shutdown()
