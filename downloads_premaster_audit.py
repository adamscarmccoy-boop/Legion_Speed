"""downloads_premaster_audit.py — download_pack(url, dest_dir) -> Path.

Placeholder downloader that fetches a real sample pack URL if it's an http(s)
endpoint, otherwise creates a synthetic WAV for testing. Real implementations
can swap this for Splice/Cymatics auth-aware downloaders later.
"""

import os
import struct
import math
from pathlib import Path
from urllib.parse import urlparse
import urllib.request


def _make_synthetic_wav(path: Path, vendor_tag: str, duration_sec: float = 8.0,
                         sample_rate: int = 44100) -> Path:
    """Write a tiny synthetic WAV so downstream DSP has something real to read."""
    import numpy as np
    n = int(duration_sec * sample_rate)
    # Simple per-vendor signature so DSP features vary between prospects
    tag_seed = sum(ord(c) for c in vendor_tag) % 7
    freqs = [110.0 * (1 + tag_seed * 0.13), 220.0 * (1 + tag_seed * 0.07), 440.0]
    t = np.arange(n) / sample_rate
    sig = np.zeros(n, dtype=np.float32)
    for f in freqs:
        sig += 0.3 * np.sin(2 * math.pi * f * t)
    # Tempo-pulse envelope
    bpm = 124 + tag_seed * 2
    pulse_period = 60.0 / bpm
    env = 0.5 + 0.5 * np.sign(np.sin(2 * math.pi * t / pulse_period))
    sig = (sig * env).astype(np.float32)
    # Write WAV
    import soundfile as sf
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), sig, sample_rate, subtype="PCM_16")
    return path


def download_pack(url: str, dest_dir) -> Path:
    """Download a sample pack (or synthesize a placeholder).

    Args:
        url: HTTP(S) URL or a vendor domain string.
        dest_dir: Directory to write the pack into.

    Returns:
        Path to the downloaded/synthesized file.
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    parsed = urlparse(url)
    slug = (parsed.netloc or parsed.path or "vendor").replace("www.", "").replace(".", "_")
    target = dest_dir / f"{slug}_sample.wav"

    # If it's a real http(s) URL, try a quick download
    if parsed.scheme in ("http", "https"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = r.read()
            if data and len(data) > 1024:
                target.write_bytes(data)
                return target
        except Exception:
            pass  # fall through to synthetic

    # Otherwise synthesize a representative sample
    return _make_synthetic_wav(target, vendor_tag=slug)