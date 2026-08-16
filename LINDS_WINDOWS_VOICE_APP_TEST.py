"""
LINDS_WINDOWS_VOICE_APP_TEST.py
================================
Windows realtime voice/audio stylizer test app.

Goal:
- Use the same practical tech shape as the Mac/Linds app:
  sounddevice realtime stream -> Pedalboard DSP -> UI controls -> audible output.
- Windows input capture uses WASAPI loopback when possible.
- Prevent fake-success by verifying input/output difference.
- Prevent popping with fade-in/fade-out and smoothed wet/intensity controls.

Install inside your project venv:
    pip install sounddevice numpy pedalboard pydantic PyQt6

Run:
    .venv\Scripts\python.exe LINDS_WINDOWS_VOICE_APP_TEST.py

If PyQt6 fails, install it:
    pip install PyQt6

Notes:
- Choose a WASAPI LOOPBACK input for system audio, or a microphone input for mic testing.
- Choose your speakers/headphones as output.
- Start with PROOF / OBVIOUS CHANGE. If that sounds the same, the route is wrong.
"""

from __future__ import annotations

import math
import sys
import time
import traceback
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple

import numpy as np
import sounddevice as sd
from pydantic import BaseModel, field_validator

from pedalboard import (
    Pedalboard,
    Compressor,
    HighpassFilter,
    LowpassFilter,
    Limiter,
    Gain,
    PitchShift,
    Distortion,
    Bitcrush,
    Chorus,
    Phaser,
    GSMFullRateCompressor,
)

try:
    from PyQt6 import QtCore, QtWidgets
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "PyQt6 is required for this test UI. Install with: pip install PyQt6"
    ) from exc


# =============================================================================
# Pydantic DSP schemas, adapted from your existing Sovereign/Chris Lake style
# =============================================================================

class SegmentPhysics(BaseModel):
    """DSP features for one short realtime buffer/window."""
    segment_name: str
    track_name: str = "live_input"
    rms_db: float = -100.0
    crest_factor: float = 0.0
    sub_bass_energy: float = 0.0
    bass_energy: float = 0.0
    mid_energy: float = 0.0
    high_energy: float = 0.0
    spectral_centroid: float = 0.0
    spectral_bandwidth: float = 0.0
    spectral_rolloff: float = 0.0
    spectral_flatness: float = 0.0
    zero_crossing_rate: float = 0.0

    @field_validator("rms_db", "crest_factor", mode="before")
    @classmethod
    def coerce_float(cls, v):
        return float(v) if v is not None else 0.0


class VoiceRenderVerification(BaseModel):
    input_rms_db: float
    output_rms_db: float
    mean_abs_diff: float
    peak_in: float
    peak_out: float
    clipping_detected: bool
    changed_enough: bool
    pop_risk_detected: bool
    status: str


# =============================================================================
# Small realtime feature extractor. No librosa dependency so the test stays light.
# =============================================================================

class RealtimeFeatureExtractor:
    def __init__(self, sample_rate: int):
        self.sample_rate = int(sample_rate)

    @staticmethod
    def _to_mono(audio: np.ndarray) -> np.ndarray:
        if audio.ndim == 2:
            return audio.mean(axis=1).astype(np.float32)
        return audio.astype(np.float32)

    def extract(self, audio: np.ndarray, segment_name: str = "live") -> SegmentPhysics:
        y = self._to_mono(audio)
        y = np.nan_to_num(y).astype(np.float32)
        if y.size < 16:
            return SegmentPhysics(segment_name=segment_name)

        eps = 1e-9
        rms = float(np.sqrt(np.mean(y * y) + eps))
        rms_db = float(20.0 * np.log10(max(rms, eps)))
        peak = float(np.max(np.abs(y)) + eps)
        crest = float(peak / max(rms, eps))

        # Windowed FFT features.
        win = np.hanning(y.size).astype(np.float32)
        yw = y * win
        mag = np.abs(np.fft.rfft(yw)).astype(np.float64)
        freqs = np.fft.rfftfreq(yw.size, d=1.0 / self.sample_rate).astype(np.float64)
        mag_sum = float(np.sum(mag) + eps)

        centroid = float(np.sum(freqs * mag) / mag_sum)
        bandwidth = float(np.sqrt(np.sum(((freqs - centroid) ** 2) * mag) / mag_sum))

        cumulative = np.cumsum(mag)
        rolloff_idx = int(np.searchsorted(cumulative, 0.85 * cumulative[-1])) if cumulative[-1] > 0 else 0
        rolloff = float(freqs[min(rolloff_idx, len(freqs) - 1)])

        # Spectral flatness: geometric mean / arithmetic mean.
        flatness = float(np.exp(np.mean(np.log(mag + eps))) / (np.mean(mag + eps)))

        zcr = float(np.mean(np.abs(np.diff(np.signbit(y))).astype(np.float32)))

        def band_energy(lo: float, hi: float) -> float:
            mask = (freqs >= lo) & (freqs < hi)
            if not np.any(mask):
                return 0.0
            return float(np.sum(mag[mask] ** 2))

        return SegmentPhysics(
            segment_name=segment_name,
            rms_db=rms_db,
            crest_factor=crest,
            sub_bass_energy=band_energy(20, 80),
            bass_energy=band_energy(80, 250),
            mid_energy=band_energy(250, 3000),
            high_energy=band_energy(3000, 10000),
            spectral_centroid=centroid,
            spectral_bandwidth=bandwidth,
            spectral_rolloff=rolloff,
            spectral_flatness=flatness,
            zero_crossing_rate=zcr,
        )


# =============================================================================
# Effect-chain factory: actual voice-changing chains, no Pedalboard([]) betrayal.
# =============================================================================

class EffectFactory:
    """Builds Pedalboard chains. These are deliberately audible for debugging."""

    @staticmethod
    def build(effect_name: str, intensity: float) -> Pedalboard:
        intensity = float(np.clip(intensity, 0.0, 1.0))

        # Important: every chain ends with Limiter. Digital shrapnel is not a vibe.
        if effect_name == "PROOF / obvious change":
            return Pedalboard([
                HighpassFilter(cutoff_frequency_hz=120),
                PitchShift(semitones=-2.0 - 5.0 * intensity),
                Distortion(drive_db=6.0 + 18.0 * intensity),
                Compressor(threshold_db=-24, ratio=2.5 + 2.0 * intensity),
                Gain(gain_db=-5.0),
                Limiter(threshold_db=-1.0),
            ])

        if effect_name == "deep pitch body":
            return Pedalboard([
                HighpassFilter(cutoff_frequency_hz=80),
                PitchShift(semitones=-1.0 - 6.0 * intensity),
                LowpassFilter(cutoff_frequency_hz=8500 - 3500 * intensity),
                Compressor(threshold_db=-22, ratio=2.5 + intensity),
                Gain(gain_db=-2.0),
                Limiter(threshold_db=-1.0),
            ])

        if effect_name == "phone/radio mask":
            return Pedalboard([
                HighpassFilter(cutoff_frequency_hz=250 + 150 * intensity),
                LowpassFilter(cutoff_frequency_hz=4300 - 1200 * intensity),
                GSMFullRateCompressor(),
                Compressor(threshold_db=-18, ratio=3.0),
                Distortion(drive_db=2.0 + 6.0 * intensity),
                Gain(gain_db=-1.5),
                Limiter(threshold_db=-1.0),
            ])

        if effect_name == "robot/digital":
            bit_depth = int(round(12 - 6 * intensity))
            bit_depth = max(5, min(12, bit_depth))
            return Pedalboard([
                HighpassFilter(cutoff_frequency_hz=120),
                PitchShift(semitones=1.0 + 4.0 * intensity),
                Bitcrush(bit_depth=bit_depth),
                Phaser(rate_hz=0.4 + 1.2 * intensity, depth=0.4 + 0.4 * intensity, mix=0.25 + 0.25 * intensity),
                Compressor(threshold_db=-22, ratio=3.0),
                Limiter(threshold_db=-1.0),
            ])

        if effect_name == "alien doubled":
            return Pedalboard([
                HighpassFilter(cutoff_frequency_hz=100),
                PitchShift(semitones=2.0 + 3.0 * intensity),
                Chorus(rate_hz=0.8 + 1.5 * intensity, depth=0.25 + 0.35 * intensity, mix=0.25 + 0.35 * intensity),
                Phaser(rate_hz=0.3 + 0.8 * intensity, depth=0.35 + 0.4 * intensity, mix=0.2 + 0.3 * intensity),
                Gain(gain_db=-2.0),
                Limiter(threshold_db=-1.0),
            ])

        if effect_name == "clean safety only":
            return Pedalboard([
                HighpassFilter(cutoff_frequency_hz=90),
                Compressor(threshold_db=-22, ratio=2.2),
                Gain(gain_db=1.0),
                Limiter(threshold_db=-1.0),
            ])

        # Explicit fallback should still not be empty.
        return Pedalboard([
            HighpassFilter(cutoff_frequency_hz=120),
            Compressor(threshold_db=-22, ratio=2.5),
            Limiter(threshold_db=-1.0),
        ])


# =============================================================================
# Realtime audio engine
# =============================================================================

@dataclass
class DeviceChoice:
    label: str
    index: Optional[int]
    samplerate: int
    channels: int
    hostapi: str
    is_loopback: bool = False


class LindsRealtimeEngine(QtCore.QObject):
    status_signal = QtCore.pyqtSignal(str)
    verify_signal = QtCore.pyqtSignal(str)
    level_signal = QtCore.pyqtSignal(float, float)
    feature_signal = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.stream: Optional[sd.Stream] = None
        self.running = False

        self.input_choice: Optional[DeviceChoice] = None
        self.output_choice: Optional[DeviceChoice] = None
        self.sample_rate: int = 48000
        self.channels: int = 2
        self.blocksize: int = 1024

        self.effect_name = "PROOF / obvious change"
        self.intensity_target = 0.75
        self.intensity_current = 0.75
        self.wet_target = 1.0
        self.wet_current = 1.0
        self.output_gain_db = -3.0

        self.board = EffectFactory.build(self.effect_name, self.intensity_current)
        self.extractor = RealtimeFeatureExtractor(self.sample_rate)

        self._fade_samples_total = int(0.04 * self.sample_rate)  # 40ms fade
        self._fade_pos = 0
        self._stopping = False
        self._callback_count = 0
        self._last_verify_time = 0.0
        self._last_processed_tail: Optional[np.ndarray] = None
        self._lock = QtCore.QMutex()

    # ---------------------------------------------------------------------
    # Device discovery
    # ---------------------------------------------------------------------
    @staticmethod
    def list_hostapis() -> List[dict]:
        return list(sd.query_hostapis())

    @staticmethod
    def list_input_choices() -> List[DeviceChoice]:
        devices = sd.query_devices()
        hostapis = sd.query_hostapis()
        choices: List[DeviceChoice] = []
        wasapi_indices = {i for i, api in enumerate(hostapis) if "WASAPI" in api["name"].upper()}

        # Normal physical inputs.
        for idx, d in enumerate(devices):
            hostapi_name = hostapis[d["hostapi"]]["name"]
            if int(d.get("max_input_channels", 0)) > 0:
                sr = int(d.get("default_samplerate") or 48000)
                ch = min(2, int(d.get("max_input_channels", 1)))
                choices.append(DeviceChoice(
                    label=f"INPUT [{idx}] {d['name']} ({hostapi_name})",
                    index=idx,
                    samplerate=sr,
                    channels=max(1, ch),
                    hostapi=hostapi_name,
                    is_loopback=False,
                ))

        # Windows WASAPI loopback from output devices.
        for idx, d in enumerate(devices):
            hostapi_name = hostapis[d["hostapi"]]["name"]
            if d["hostapi"] in wasapi_indices and int(d.get("max_output_channels", 0)) > 0:
                sr = int(d.get("default_samplerate") or 48000)
                ch = min(2, int(d.get("max_output_channels", 2)))
                choices.append(DeviceChoice(
                    label=f"LOOPBACK [{idx}] {d['name']} ({hostapi_name})",
                    index=idx,
                    samplerate=sr,
                    channels=max(1, ch),
                    hostapi=hostapi_name,
                    is_loopback=True,
                ))

        return choices

    @staticmethod
    def list_output_choices() -> List[DeviceChoice]:
        devices = sd.query_devices()
        hostapis = sd.query_hostapis()
        choices: List[DeviceChoice] = []
        for idx, d in enumerate(devices):
            hostapi_name = hostapis[d["hostapi"]]["name"]
            if int(d.get("max_output_channels", 0)) > 0:
                sr = int(d.get("default_samplerate") or 48000)
                ch = min(2, int(d.get("max_output_channels", 2)))
                choices.append(DeviceChoice(
                    label=f"OUTPUT [{idx}] {d['name']} ({hostapi_name})",
                    index=idx,
                    samplerate=sr,
                    channels=max(1, ch),
                    hostapi=hostapi_name,
                    is_loopback=False,
                ))
        return choices

    # ---------------------------------------------------------------------
    # Parameter updates
    # ---------------------------------------------------------------------
    def set_effect(self, effect_name: str):
        self.effect_name = effect_name
        # Rebuild at current target intensity. Wet smoothing handles the audible transition.
        self.board = EffectFactory.build(self.effect_name, self.intensity_target)
        self.status_signal.emit(f"Effect board loaded: {effect_name} | effects={self.describe_board()}")

    def set_intensity(self, value_0_to_100: int):
        self.intensity_target = float(np.clip(value_0_to_100 / 100.0, 0.0, 1.0))
        # Rebuild board at target intensity. For heavy parameter changes this may click less because wet is smoothed.
        self.board = EffectFactory.build(self.effect_name, self.intensity_target)

    def set_wet(self, value_0_to_100: int):
        self.wet_target = float(np.clip(value_0_to_100 / 100.0, 0.0, 1.0))

    def set_gain(self, value_db: float):
        self.output_gain_db = float(np.clip(value_db, -24.0, 12.0))

    def describe_board(self) -> str:
        try:
            names = [type(effect).__name__ for effect in self.board]
            return ", ".join(names) if names else "EMPTY_BOARD"
        except Exception:
            return "UNKNOWN_BOARD"

    # ---------------------------------------------------------------------
    # Stream control
    # ---------------------------------------------------------------------
    def start(self, input_choice: DeviceChoice, output_choice: DeviceChoice, blocksize: int = 1024):
        if self.running:
            self.status_signal.emit("Already running.")
            return

        self.input_choice = input_choice
        self.output_choice = output_choice
        self.sample_rate = int(input_choice.samplerate or output_choice.samplerate or 48000)
        self.channels = int(min(input_choice.channels, output_choice.channels, 2)) or 1
        self.blocksize = int(blocksize)
        self.extractor = RealtimeFeatureExtractor(self.sample_rate)
        self._fade_samples_total = max(1, int(0.04 * self.sample_rate))
        self._fade_pos = 0
        self._stopping = False
        self._callback_count = 0
        self._last_processed_tail = None

        if self.describe_board() == "EMPTY_BOARD":
            raise RuntimeError("Refusing to start with empty Pedalboard([]). Nice try, codegen goblin.")

        extra_settings = None
        if input_choice.is_loopback:
            try:
                extra_settings = sd.WasapiSettings(loopback=True)
            except Exception as exc:
                self.status_signal.emit(f"WARNING: Could not create WASAPI loopback settings: {exc}")
                extra_settings = None

        device_arg: Tuple[Optional[int], Optional[int]] = (input_choice.index, output_choice.index)

        self.status_signal.emit(
            f"Starting stream | in={input_choice.label} | out={output_choice.label} | "
            f"sr={self.sample_rate} ch={self.channels} block={self.blocksize} loopback={input_choice.is_loopback}"
        )
        self.status_signal.emit(f"Board: {self.describe_board()}")

        try:
            self.stream = sd.Stream(
                samplerate=self.sample_rate,
                blocksize=self.blocksize,
                device=device_arg,
                channels=self.channels,
                dtype="float32",
                callback=self._audio_callback,
                extra_settings=extra_settings,
                latency="low",
            )
            self.stream.start()
            self.running = True
            self.status_signal.emit("RUNNING. If PROOF mode sounds dry, your route is wrong.")
        except Exception as exc:
            self.running = False
            self.stream = None
            self.status_signal.emit("FAILED TO START STREAM:\n" + "".join(traceback.format_exception(exc)))

    def stop(self):
        if not self.running:
            self.status_signal.emit("Not running.")
            return
        self._stopping = True
        self.status_signal.emit("Stopping with fade-out...")
        # Give callback a moment to fade. Then hard stop.
        QtCore.QTimer.singleShot(120, self._finish_stop)

    def _finish_stop(self):
        try:
            if self.stream is not None:
                self.stream.stop()
                self.stream.close()
        except Exception as exc:
            self.status_signal.emit(f"Stop error: {exc}")
        finally:
            self.stream = None
            self.running = False
            self._stopping = False
            self.status_signal.emit("STOPPED.")

    # ---------------------------------------------------------------------
    # Audio callback
    # ---------------------------------------------------------------------
    def _smooth_value(self, current: float, target: float, smoothing: float = 0.015) -> float:
        return current + (target - current) * smoothing

    def _fade_envelope(self, frames: int) -> np.ndarray:
        # Fade in at start, fade out when stopping.
        env = np.ones(frames, dtype=np.float32)
        if self._fade_pos < self._fade_samples_total and not self._stopping:
            start = self._fade_pos
            stop = min(self._fade_pos + frames, self._fade_samples_total)
            ramp_len = stop - start
            if ramp_len > 0:
                env[:ramp_len] = np.linspace(start / self._fade_samples_total, stop / self._fade_samples_total, ramp_len, dtype=np.float32)
            self._fade_pos += frames
        elif self._stopping:
            # Simple per-buffer fade-out.
            env *= np.linspace(1.0, 0.0, frames, dtype=np.float32)
        return env

    def _audio_callback(self, indata, outdata, frames, callback_time, status):
        if status:
            # Do not print every callback forever, but emit occasionally.
            if self._callback_count % 50 == 0:
                self.status_signal.emit(f"Stream status: {status}")

        self._callback_count += 1

        try:
            x = np.nan_to_num(indata).astype(np.float32, copy=False)

            # Smooth live controls.
            self.wet_current = self._smooth_value(self.wet_current, self.wet_target, smoothing=0.025)
            self.intensity_current = self._smooth_value(self.intensity_current, self.intensity_target, smoothing=0.02)

            # Pedalboard expects shape (samples, channels) fine in modern versions.
            y = self.board(x, self.sample_rate).astype(np.float32, copy=False)
            y = np.nan_to_num(y)

            # Ensure output shape matches exactly.
            if y.shape != x.shape:
                y = np.reshape(y, x.shape).astype(np.float32)

            # Wet/dry mix with smoothing.
            wet = float(np.clip(self.wet_current, 0.0, 1.0))
            mixed = (1.0 - wet) * x + wet * y

            # Output gain.
            gain = float(10.0 ** (self.output_gain_db / 20.0))
            mixed = mixed * gain

            # Anti-pop / start-stop envelope.
            env = self._fade_envelope(frames)
            if mixed.ndim == 2:
                mixed = mixed * env[:, None]
            else:
                mixed = mixed * env

            # Final safety soft clip. Limiter already helps, this catches nonsense.
            mixed = np.tanh(mixed * 1.05).astype(np.float32)

            outdata[:] = mixed

            # UI meters.
            if self._callback_count % 8 == 0:
                rms_in = float(np.sqrt(np.mean(x * x) + 1e-9))
                rms_out = float(np.sqrt(np.mean(mixed * mixed) + 1e-9))
                self.level_signal.emit(rms_in, rms_out)

            # Verification every ~1 sec, not a terminal confetti cannon.
            now = time.time()
            if now - self._last_verify_time > 1.0:
                self._last_verify_time = now
                verification = self._verify_block(x, mixed)
                self.verify_signal.emit(
                    f"{verification.status} | diff={verification.mean_abs_diff:.6f} | "
                    f"in={verification.input_rms_db:.1f}dB out={verification.output_rms_db:.1f}dB | "
                    f"clip={verification.clipping_detected} popRisk={verification.pop_risk_detected}"
                )

                inp = self.extractor.extract(x, "input")
                out = self.extractor.extract(mixed, "output")
                self.feature_signal.emit(
                    f"Input centroid={inp.spectral_centroid:.0f}Hz crest={inp.crest_factor:.2f} flat={inp.spectral_flatness:.4f}\n"
                    f"Output centroid={out.spectral_centroid:.0f}Hz crest={out.crest_factor:.2f} flat={out.spectral_flatness:.4f}"
                )

        except Exception as exc:
            # Fail safe to silence instead of speaker murder.
            outdata[:] = np.zeros_like(outdata)
            if self._callback_count % 20 == 0:
                self.status_signal.emit("CALLBACK ERROR:\n" + "".join(traceback.format_exception(exc)))

    def _verify_block(self, x: np.ndarray, y: np.ndarray) -> VoiceRenderVerification:
        eps = 1e-9
        x = np.nan_to_num(x).astype(np.float32)
        y = np.nan_to_num(y).astype(np.float32)
        rms_in = float(np.sqrt(np.mean(x * x) + eps))
        rms_out = float(np.sqrt(np.mean(y * y) + eps))
        rms_in_db = float(20 * np.log10(max(rms_in, eps)))
        rms_out_db = float(20 * np.log10(max(rms_out, eps)))
        diff = float(np.mean(np.abs(y - x)))
        peak_in = float(np.max(np.abs(x))) if x.size else 0.0
        peak_out = float(np.max(np.abs(y))) if y.size else 0.0
        clipping = bool(peak_out >= 0.985)

        # Pop risk: huge discontinuity compared with normal frame-to-frame changes.
        pop_risk = False
        if self._last_processed_tail is not None and y.size:
            first = y[0] if y.ndim == 1 else y[0, :]
            jump = float(np.max(np.abs(first - self._last_processed_tail)))
            pop_risk = bool(jump > 0.35)
        if y.size:
            self._last_processed_tail = y[-1].copy() if y.ndim == 2 else np.array(y[-1], dtype=np.float32)

        changed = bool(diff > 0.002 or abs(rms_out_db - rms_in_db) > 1.0)
        if not changed:
            status = "WARNING: near-identical output; bypass/wrong route possible"
        elif clipping:
            status = "WARNING: changed but clipping risk"
        else:
            status = "OK: processed output changed"

        return VoiceRenderVerification(
            input_rms_db=rms_in_db,
            output_rms_db=rms_out_db,
            mean_abs_diff=diff,
            peak_in=peak_in,
            peak_out=peak_out,
            clipping_detected=clipping,
            changed_enough=changed,
            pop_risk_detected=pop_risk,
            status=status,
        )


# =============================================================================
# PyQt UI
# =============================================================================

class MainWindow(QtWidgets.QWidget):
    EFFECTS = [
        "PROOF / obvious change",
        "deep pitch body",
        "phone/radio mask",
        "robot/digital",
        "alien doubled",
        "clean safety only",
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Linds Windows Voice App Test - Realtime Pedalboard")
        self.resize(980, 720)
        self.engine = LindsRealtimeEngine()
        self.input_choices: List[DeviceChoice] = []
        self.output_choices: List[DeviceChoice] = []

        self._build_ui()
        self._connect_signals()
        self.refresh_devices()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        header = QtWidgets.QLabel("Linds Voice App Test - Windows WASAPI / Pedalboard / Anti-Pop / Verification")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)

        warning = QtWidgets.QLabel(
            "Start with PROOF / obvious change. If it sounds dry, the route is wrong, not the effect. "
            "No empty Pedalboard allowed, because we have suffered enough."
        )
        warning.setWordWrap(True)
        layout.addWidget(warning)

        grid = QtWidgets.QGridLayout()
        layout.addLayout(grid)

        self.input_combo = QtWidgets.QComboBox()
        self.output_combo = QtWidgets.QComboBox()
        self.refresh_btn = QtWidgets.QPushButton("Refresh Devices")

        grid.addWidget(QtWidgets.QLabel("Input / Loopback:"), 0, 0)
        grid.addWidget(self.input_combo, 0, 1)
        grid.addWidget(self.refresh_btn, 0, 2)

        grid.addWidget(QtWidgets.QLabel("Output:"), 1, 0)
        grid.addWidget(self.output_combo, 1, 1, 1, 2)

        self.effect_combo = QtWidgets.QComboBox()
        self.effect_combo.addItems(self.EFFECTS)
        grid.addWidget(QtWidgets.QLabel("Voice-changing effect:"), 2, 0)
        grid.addWidget(self.effect_combo, 2, 1, 1, 2)

        self.intensity = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.intensity.setMinimum(0)
        self.intensity.setMaximum(100)
        self.intensity.setValue(75)
        self.intensity_label = QtWidgets.QLabel("75%")
        grid.addWidget(QtWidgets.QLabel("Intensity:"), 3, 0)
        grid.addWidget(self.intensity, 3, 1)
        grid.addWidget(self.intensity_label, 3, 2)

        self.wet = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.wet.setMinimum(0)
        self.wet.setMaximum(100)
        self.wet.setValue(100)
        self.wet_label = QtWidgets.QLabel("100%")
        grid.addWidget(QtWidgets.QLabel("Wet mix:"), 4, 0)
        grid.addWidget(self.wet, 4, 1)
        grid.addWidget(self.wet_label, 4, 2)

        self.gain = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.gain.setMinimum(-24)
        self.gain.setMaximum(12)
        self.gain.setValue(-3)
        self.gain_label = QtWidgets.QLabel("-3 dB")
        grid.addWidget(QtWidgets.QLabel("Output gain:"), 5, 0)
        grid.addWidget(self.gain, 5, 1)
        grid.addWidget(self.gain_label, 5, 2)

        self.block_combo = QtWidgets.QComboBox()
        self.block_combo.addItems(["512", "1024", "2048"])
        self.block_combo.setCurrentText("1024")
        grid.addWidget(QtWidgets.QLabel("Blocksize:"), 6, 0)
        grid.addWidget(self.block_combo, 6, 1)

        btn_row = QtWidgets.QHBoxLayout()
        layout.addLayout(btn_row)
        self.start_btn = QtWidgets.QPushButton("START")
        self.stop_btn = QtWidgets.QPushButton("STOP")
        self.stop_btn.setEnabled(False)
        self.start_btn.setMinimumHeight(44)
        self.stop_btn.setMinimumHeight(44)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)

        meters = QtWidgets.QHBoxLayout()
        layout.addLayout(meters)
        self.in_meter = QtWidgets.QProgressBar()
        self.out_meter = QtWidgets.QProgressBar()
        self.in_meter.setRange(0, 100)
        self.out_meter.setRange(0, 100)
        meters.addWidget(QtWidgets.QLabel("Input"))
        meters.addWidget(self.in_meter)
        meters.addWidget(QtWidgets.QLabel("Output"))
        meters.addWidget(self.out_meter)

        self.verify_label = QtWidgets.QLabel("Verification: not running")
        self.verify_label.setWordWrap(True)
        self.verify_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.verify_label)

        self.features = QtWidgets.QPlainTextEdit()
        self.features.setReadOnly(True)
        self.features.setMaximumHeight(90)
        layout.addWidget(self.features)

        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

    def _connect_signals(self):
        self.refresh_btn.clicked.connect(self.refresh_devices)
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.effect_combo.currentTextChanged.connect(self.engine.set_effect)
        self.intensity.valueChanged.connect(self._intensity_changed)
        self.wet.valueChanged.connect(self._wet_changed)
        self.gain.valueChanged.connect(self._gain_changed)

        self.engine.status_signal.connect(self.append_log)
        self.engine.verify_signal.connect(self.verify_label.setText)
        self.engine.level_signal.connect(self.update_meters)
        self.engine.feature_signal.connect(self.features.setPlainText)

    def refresh_devices(self):
        self.input_combo.clear()
        self.output_combo.clear()
        self.input_choices = self.engine.list_input_choices()
        self.output_choices = self.engine.list_output_choices()

        for choice in self.input_choices:
            self.input_combo.addItem(choice.label)
        for choice in self.output_choices:
            self.output_combo.addItem(choice.label)

        # Prefer loopback for input if present.
        for i, c in enumerate(self.input_choices):
            if c.is_loopback:
                self.input_combo.setCurrentIndex(i)
                break

        self.append_log(f"Loaded {len(self.input_choices)} input/loopback choices and {len(self.output_choices)} outputs.")
        self.append_log("Pick LOOPBACK for system audio, or INPUT microphone for mic testing.")

    def _intensity_changed(self, value: int):
        self.intensity_label.setText(f"{value}%")
        self.engine.set_intensity(value)

    def _wet_changed(self, value: int):
        self.wet_label.setText(f"{value}%")
        self.engine.set_wet(value)

    def _gain_changed(self, value: int):
        self.gain_label.setText(f"{value} dB")
        self.engine.set_gain(float(value))

    def start(self):
        if not self.input_choices or not self.output_choices:
            self.append_log("No devices available. Refresh devices first.")
            return
        input_choice = self.input_choices[self.input_combo.currentIndex()]
        output_choice = self.output_choices[self.output_combo.currentIndex()]
        blocksize = int(self.block_combo.currentText())
        self.engine.set_effect(self.effect_combo.currentText())
        self.engine.set_intensity(self.intensity.value())
        self.engine.set_wet(self.wet.value())
        self.engine.set_gain(float(self.gain.value()))
        self.engine.start(input_choice, output_choice, blocksize=blocksize)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop(self):
        self.engine.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def update_meters(self, rms_in: float, rms_out: float):
        def to_meter(rms: float) -> int:
            db = 20 * math.log10(max(rms, 1e-9))
            return int(np.clip((db + 60) / 60 * 100, 0, 100))
        self.in_meter.setValue(to_meter(rms_in))
        self.out_meter.setValue(to_meter(rms_out))

    def append_log(self, text: str):
        ts = time.strftime("%H:%M:%S")
        self.log.appendPlainText(f"[{ts}] {text}")
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def closeEvent(self, event):
        try:
            self.engine.stop()
        except Exception:
            pass
        event.accept()


# =============================================================================
# Entrypoint
# =============================================================================

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
