import numpy as np
import librosa
import logging
import os
from datetime import datetime
from pedalboard import Pedalboard, Gain

# --- H.O.R.N. Log Configuration ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"engine_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AcousticDNAEngine")

class AcousticDNAEngine:
    """
    Production-ready feature extraction core.
    Designed for zero-copy buffer handoffs with integrated H.O.R.N. logging.
    """
    def __init__(self, sample_rate=44100, buffer_size=1024):
        self.sr = sample_rate
        self.buffer_size = buffer_size
        self.board = Pedalboard([Gain(gain_db=6.0)])
        logger.info(f"Acoustic DNA Engine Initialized: SR={self.sr}, Buffer={self.buffer_size}")

    def process_buffer(self, raw_buffer):
        """
        Applies DSP conditioning and extracts Chroma DNA.
        """
        if len(raw_buffer) != self.buffer_size:
            logger.warning(f"Buffer size mismatch! Expected {self.buffer_size}, got {len(raw_buffer)}")
        
        # 1. Condition
        conditioned = self.board(raw_buffer, sample_rate=self.sr)
        
        # 2. Extract Chroma (12-note energy vector)
        # Optimized hop_length for single-frame inference
        chroma = librosa.feature.chroma_stft(
            y=conditioned, 
            sr=self.sr, 
            n_fft=self.buffer_size, 
            hop_length=self.buffer_size + 1
        )
        
        dna_vector = np.mean(chroma, axis=1)
        
        # Log high-energy detections (simplified confidence)
        if np.max(dna_vector) > 0.8:
            logger.info(f"High-confidence note detected: NoteIndex={np.argmax(dna_vector)}")
            
        return dna_vector

    def get_latency_optimized_window(self):
        """Returns the recommended buffer size for mobile real-time."""
        return self.buffer_size
