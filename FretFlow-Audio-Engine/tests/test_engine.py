import pytest
import numpy as np
import os
from engine.analysis import AcousticDNAEngine

@pytest.fixture
def engine():
    return AcousticDNAEngine(sample_rate=44100, buffer_size=1024)

def test_engine_initialization(engine):
    """Verify engine parameters are set correctly."""
    assert engine.sr == 44100
    assert engine.buffer_size == 1024

def test_feature_extraction_shape(engine):
    """Ensure the Acoustic DNA vector is exactly 12 dimensions (C through B)."""
    dummy_buffer = np.random.uniform(-0.1, 0.1, 1024).astype(np.float32)
    dna = engine.process_buffer(dummy_buffer)
    assert dna.shape == (12,)
    assert np.all(dna >= 0)  # Energy must be non-negative

def test_buffer_mismatch_warning(engine, caplog):
    """Test that the engine logs a warning if the buffer size is incorrect."""
    wrong_buffer = np.random.uniform(-0.1, 0.1, 512).astype(np.float32)
    _ = engine.process_buffer(wrong_buffer)
    assert "Buffer size mismatch" in caplog.text

def test_log_creation():
    """Verify that the logs directory and engine log file are created."""
    assert os.path.exists("logs")
    log_files = [f for f in os.listdir("logs") if f.startswith("engine_")]
    assert len(log_files) > 0

def test_deterministic_output(engine):
    """Verify that the same buffer produces the same DNA vector."""
    buffer = np.random.uniform(-0.1, 0.1, 1024).astype(np.float32)
    dna1 = engine.process_buffer(buffer)
    dna2 = engine.process_buffer(buffer)
    np.testing.assert_array_almost_equal(dna1, dna2)
