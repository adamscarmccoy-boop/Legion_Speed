import os
import sys
import threading
import numpy as np
import sounddevice as sd
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from PyQt6 import QtWidgets, QtCore, QtGui

# ==============================================================================
# SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
# Prevents dangling stdout/stdio pipes and GCS registry locks on Windows exit
# ==============================================================================
import atexit
import signal

def clean_exit_handler(*args, **kwargs):
    import sys
    sys.stderr.write("\n[LMS LIFECYCLE] Exit triggered. Flushing system streams...\n")
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write("[LMS LIFECYCLE] Active Ray session detected. Disconnecting...\n")
            ray.shutdown()
    except Exception:
        pass
    sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================


try:
    from pedalboard import Pedalboard, Reverb, Chorus, Distortion, Compressor, LowShelfFilter, HighShelfFilter, Bitcrush, PitchShift
except ImportError:
    print("Error: 'pedalboard' library is required for this application.")
    sys.exit(1)

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QPushButton, QComboBox, QSlider, QLabel, QCheckBox
    )
except ImportError:
    print("Error: 'PyQt6' is required. Please install it via 'pip install PyQt6'.")
    sys.exit(1)

try:
    import ray
except ImportError:
    ray = None

class AppConfig(BaseModel):
    app_name: str = "Lindsay Audio Stylizer"
    ray_namespace: str = "legion"
    sample_rate: int = 48000
    block_size: int = 512
    default_preset: str = "Bypass"
    assets_path: str = os.getenv("AUDIO_ASSETS_PATH", "C:/WEB CASE STUDY/Acoustic-DNA-Audio-Engine/assets")

class StylizerState(BaseModel):
    preset: str = "Bypass"
    intensity: float = 0.5
    is_wild_mode: bool = False
    is_running: bool = False
    input_device_id: Optional[int] = None
    output_device_id: Optional[int] = None

class AudioEngine:
    def __init__(self, config: AppConfig):
        self.config = config
        self.state = StylizerState()
        self.lock = threading.Lock()
        self.board = Pedalboard()
        self.stream = None
        self.active_sample_rate = int(self.config.sample_rate)
        self._update_board()

    def _update_board(self):
        """Deterministic DSP chain construction based on preset and mode."""
        preset = self.state.preset
        intensity = float(self.state.intensity)
        wild = bool(self.state.is_wild_mode)

        plugins = []

        if preset == "Bypass":
            pass
        elif preset == "Warm Lecture":
            plugins.append(Compressor(threshold_db=-20, ratio=2.0))
            plugins.append(LowShelfFilter(cutoff_frequency_hz=300, gain_db=3.0 * intensity))
            plugins.append(HighShelfFilter(cutoff_frequency_hz=5000, gain_db=-6.0 * intensity))
        elif preset == "Rave Robot":
            crush_bits = 8 if not wild else 4
            plugins.append(Bitcrush(bit_depth=crush_bits))
            plugins.append(Chorus(rate_hz=1.5, depth=0.5 * intensity))
            plugins.append(HighShelfFilter(cutoff_frequency_hz=2000, gain_db=6.0 * intensity))
        elif preset == "Soft Focus":
            plugins.append(Reverb(room_size=min(1.0, 0.8 * intensity), wet_level=min(1.0, 0.4 * intensity)))
            plugins.append(HighShelfFilter(cutoff_frequency_hz=3000, gain_db=-12.0 * intensity))
        elif preset == "Pink Glitter":
            plugins.append(HighShelfFilter(cutoff_frequency_hz=1000, gain_db=6.0 * intensity))
            plugins.append(Chorus(rate_hz=2.0, depth=0.7 * intensity))
            plugins.append(Reverb(room_size=0.5, wet_level=min(1.0, 0.3 * intensity)))
        elif preset == "Demon Lite":
            shift_semitones = -5 if not wild else -12
            plugins.append(PitchShift(semitones=shift_semitones))
            plugins.append(Distortion(drive_db=10.0 * intensity))
            plugins.append(LowShelfFilter(cutoff_frequency_hz=200, gain_db=6.0))

        new_board = Pedalboard(plugins)
        with self.lock:
            self.board = new_board

    def audio_callback(self, indata: np.ndarray, outdata: np.ndarray, frames: int, time: Any, status: Any):
        """Real-time audio callback. Keep this fast and allocation-light."""
        if status:
            print(f"Audio Status Warning: {status}", file=sys.stderr)

        with self.lock:
            board = self.board
            sample_rate = int(self.active_sample_rate)

        try:
            # sounddevice gives (frames, channels). Pedalboard expects (channels, frames).
            audio_cf = np.ascontiguousarray(indata.T, dtype=np.float32)
            processed_cf = board(audio_cf, sample_rate)
            processed = np.asarray(processed_cf, dtype=np.float32).T

            if processed.shape == outdata.shape:
                outdata[:] = processed
            else:
                print(f"Audio shape mismatch: processed={processed.shape}, out={outdata.shape}", file=sys.stderr)
                outdata[:] = indata
        except Exception as exc:
            print(f"Audio callback error: {exc}", file=sys.stderr)
            outdata[:] = indata

    def _resolve_sample_rate(self, input_device: int, output_device: int) -> int:
        """Pick a sample rate both selected Windows devices accept."""
        candidates = []
        for dev in (input_device, output_device):
            try:
                candidates.append(int(sd.query_devices(dev)["default_samplerate"]))
            except Exception:
                pass

        candidates.extend([int(self.config.sample_rate), 48000, 44100])

        seen = set()
        for sr in candidates:
            if sr in seen:
                continue
            seen.add(sr)
            try:
                sd.check_input_settings(device=input_device, channels=2, dtype="float32", samplerate=sr)
                sd.check_output_settings(device=output_device, channels=2, dtype="float32", samplerate=sr)
                return sr
            except Exception:
                continue

        return int(self.config.sample_rate)

    def start(self):
        input_device = self.state.input_device_id
        output_device = self.state.output_device_id

        if input_device is None or output_device is None:
            print("Failed to start audio stream: input or output device is not selected", file=sys.stderr)
            self.state.is_running = False
            return

        input_device = int(input_device)
        output_device = int(output_device)
        block_size = int(self.config.block_size)
        sample_rate = self._resolve_sample_rate(input_device, output_device)

        self._update_board()

        try:
            self.stream = sd.Stream(
                device=(input_device, output_device),
                samplerate=sample_rate,
                blocksize=block_size,
                dtype="float32",
                channels=2,
                callback=self.audio_callback,
            )
            self.stream.start()
            with self.lock:
                self.active_sample_rate = sample_rate
            self.state.is_running = True
            print(
                f"Audio stream started: input={input_device}, output={output_device}, "
                f"sample_rate={sample_rate}, block_size={block_size}"
            )
        except Exception as e:
            print(f"Failed to start audio stream: {type(e).__name__}: {e}", file=sys.stderr)
            self.state.is_running = False

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.state.is_running = False

class StylizerApp(QMainWindow):
    def __init__(self, config: AppConfig, engine: AudioEngine):
        super().__init__()
        self.config = config
        self.engine = engine
        self.setWindowTitle(self.config.app_name)
        self.setMinimumSize(400, 500)

        self.init_ui()
        self.setup_ray()

    def setup_ray(self):
        """Optional Ray connection for state snapshots."""
        if ray:
            try:
                if not ray.is_initialized():
                    ray.init(namespace=self.config.ray_namespace, ignore_reinit_error=True)
                print(f"Connected to Ray namespace: {self.config.ray_namespace}")
            except Exception as e:
                print(f"Ray initialization failed: {e}")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Device Selection
        dev_layout = QHBoxLayout()
        self.input_combo = QComboBox()
        self.output_combo = QComboBox()
        self.populate_devices()
        
        dev_layout.addWidget(QLabel("Input:"))
        dev_layout.addWidget(self.input_combo)
        dev_layout.addWidget(QLabel("Output:"))
        dev_layout.addWidget(self.output_combo)
        layout.addLayout(dev_layout)

        # Preset Selection
        self.preset_combo = QComboBox()
        presets = ["Warm Lecture", "Rave Robot", "Soft Focus", "Pink Glitter", "Demon Lite", "Bypass"]
        self.preset_combo.addItems(presets)
        self.preset_combo.setCurrentText(self.config.default_preset)
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        layout.addWidget(QLabel("Stylizer Preset:"))
        layout.addWidget(self.preset_combo)

        # Intensity Slider
        layout.addWidget(QLabel("Intensity:"))
        self.intensity_slider = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(0, 100)
        self.intensity_slider.setValue(50)
        self.intensity_slider.valueChanged.connect(self.on_intensity_changed)
        layout.addWidget(self.intensity_slider)

        # Mode Selector
        self.wild_checkbox = QCheckBox("Wild Mode")
        self.wild_checkbox.stateChanged.connect(self.on_mode_changed)
        layout.addWidget(self.wild_checkbox)

        # Status Label
        self.status_label = QLabel("Status: Idle")
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Control Buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        
        self.start_btn.clicked.connect(self.start_audio)
        self.stop_btn.clicked.connect(self.stop_audio)
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

    def populate_devices(self):
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            name = f"{i}: {dev['name']}"
            if dev['max_input_channels'] > 0:
                self.input_combo.addItem(name, i)
            if dev['max_output_channels'] > 0:
                self.output_combo.addItem(name, i)

    def on_preset_changed(self, preset: str):
        self.engine.state.preset = preset
        self.engine._update_board()

    def on_intensity_changed(self, value: int):
        self.engine.state.intensity = value / 100.0
        self.engine._update_board()

    def on_mode_changed(self, state: int):
        self.engine.state.is_wild_mode = (state == 2)
        self.engine._update_board()

    def start_audio(self):
        self.engine.state.input_device_id = self.input_combo.currentData()
        self.engine.state.output_device_id = self.output_combo.currentData()
        self.engine.start()
        if self.engine.state.is_running:
            self.status_label.setText("Status: Processing...")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)

    def stop_audio(self):
        self.engine.stop()
        self.status_label.setText("Status: Idle")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

if __name__ == "__main__":
    app_config = AppConfig()
    audio_engine = AudioEngine(app_config)
    
    qt_app = QApplication(sys.argv)
    window = StylizerApp(app_config, audio_engine)
    window.show()
    
    try:
        sys.exit(qt_app.exec())
    finally:
        audio_engine.stop()
        if ray and ray.is_initialized():
            ray.shutdown()