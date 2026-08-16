import sys
import threading
import numpy as np
import sounddevice as sd
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

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
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QPushButton, QComboBox, QSlider, QLabel, QCheckBox
    )
    from PyQt6.QtCore import Qt, pyqtSlot
except ImportError:
    print("Error: PyQt6 is required to run this application. Please install it via 'pip install PyQt6'.")
    sys.exit(1)

try:
    from pedalboard import Pedalboard, Chorus, Reverb, Compressor, LowShelfFilter, HighShelfFilter, Bitcrush, Distortion, PitchShift, Gain
except ImportError:
    print("Error: pedalboard is required for DSP processing. Please install it via 'pip install pedalboard'.")
    sys.exit(1)

try:
    import ray
except ImportError:
    ray = None

# --- Configuration Models ---

class AppConfig(BaseModel):
    namespace: str = "legion"
    sample_rate: int = 44100
    block_size: int = 512
    default_preset: str = "Bypass"
    presets: List[str] = [
        "Warm Lecture", "Rave Robot", "Soft Focus", 
        "Pink Glitter", "Demon Lite", "Bypass"
    ]

class StylizerState(BaseModel):
    is_running: bool = False
    current_preset: str = "Bypass"
    intensity: float = 0.5
    mode_wild: bool = False
    input_device: Optional[int] = None
    output_device: Optional[int] = None

# --- DSP Engine ---

class AudioEngine:
    def __init__(self, config: AppConfig):
        self.config = config
        self.state = StylizerState()
        self.lock = threading.Lock()
        self.board = Pedalboard()
        self._update_board()
        
        self.stream = None

    def _update_board(self):
        """Deterministic DSP Chain Construction based on preset."""
        preset = self.state.current_preset
        intensity = self.state.intensity
        wild = self.state.mode_wild

        # Base boards
        plugins = []

        if preset == "Warm Lecture":
            plugins.append(Compressor(threshold_db=-20, ratio=4))
            plugins.append(LowShelfFilter(cutoff_frequency=300, gain_db=3))
            plugins.append(Gain(gain_db=2))
        
        elif preset == "Rave Robot":
            plugins.append(Bitcrush(bit_depth=8 if not wild else 4))
            plugins.append(Distortion(drive_db=10 * intensity))
            plugins.append(HighShelfFilter(cutoff_frequency=2000, gain_db=6))
            
        elif preset == "Soft Focus":
            plugins.append(Chorus(rate_hz=1.5, depth=0.3 * intensity))
            plugins.append(Reverb(room_size=0.7, wet_level=0.3 * intensity))
            plugins.append(LowShelfFilter(cutoff_frequency=1000, gain_db=-3))
            
        elif preset == "Pink Glitter":
            plugins.append(HighShelfFilter(cutoff_frequency=5000, gain_db=10 * intensity))
            plugins.append(Chorus(rate_hz=2.0, depth=0.5))
            plugins.append(Reverb(room_size=0.9, wet_level=0.4))
            
        elif preset == "Demon Lite":
            shift = -5 if not wild else -12
            plugins.append(PitchShift(semitones=shift))
            plugins.append(Distortion(drive_db=5 * intensity))
            plugins.append(LowShelfFilter(cutoff_frequency=200, gain_db=6))
            
        elif preset == "Bypass":
            pass # Empty list = dry signal

        # Final gain stage to prevent clipping based on intensity
        plugins.append(Gain(gain_db=-1.0))
        
        self.board = Pedalboard(plugins)

    def audio_callback(self, indata, outdata, frames, time, status):
        """Fast real-time callback."""
        if status:
            print(f"Audio Status: {status}")
        
        with self.lock:
            # Process audio using the current deterministic pedalboard
            # Pedalboard expects float32 numpy arrays
            processed = self.board(indata, self.config.sample_rate)
            outdata[:] = processed

    def start(self):
        with self.lock:
            self.state.is_running = True
            self._update_board()
            self.stream = sd.Stream(
                device=(self.state.input_device, self.state.output_device),
                samplerate=self.config.sample_rate,
                blocksize=self.config.block_size,
                dtype='float32',
                channels=2,
                callback=self.audio_callback
            )
            self.stream.start()

    def stop(self):
        with self.lock:
            self.state.is_running = False
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None

    def update_params(self, preset: str, intensity: float, wild: bool):
        with self.lock:
            self.state.current_preset = preset
            self.state.intensity = intensity
            self.state.mode_wild = wild
            self._update_board()

# --- UI Application ---

class LindsayAudioApp(QMainWindow):
    def __init__(self, engine: AudioEngine, config: AppConfig):
        super().__init__()
        self.engine = engine
        self.config = config
        self.setWindowTitle("Lindsay Audio Stylizer")
        self.setFixedSize(400, 500)

        self.init_ui()
        self.init_ray()

    def init_ray(self):
        """Optional Ray integration for state snapshots."""
        if ray:
            try:
                if not ray.is_initialized():
                    ray.init(namespace=self.config.namespace, ignore_reinit_error=True)
                print(f"Connected to Ray namespace: {self.config.namespace}")
            except Exception as e:
                print(f"Ray initialization failed: {e}")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Device Selection
        dev_layout = QHBoxLayout()
        self.in_combo = QComboBox()
        self.out_combo = QComboBox()
        self.refresh_devices()
        
        dev_layout.addWidget(QLabel("In:"))
        dev_layout.addWidget(self.in_combo)
        dev_layout.addWidget(QLabel("Out:"))
        dev_layout.addWidget(self.out_combo)
        layout.addLayout(dev_layout)

        # Preset Selection
        layout.addWidget(QLabel("Stylization Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(self.config.presets)
        self.preset_combo.setCurrentText(self.config.default_preset)
        self.preset_combo.currentTextChanged.connect(self.on_param_changed)
        layout.addWidget(self.preset_combo)

        # Intensity Slider
        layout.addWidget(QLabel("Intensity:"))
        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(0, 100)
        self.intensity_slider.setValue(50)
        self.intensity_slider.valueChanged.connect(self.on_param_changed)
        layout.addWidget(self.intensity_slider)

        # Mode Switch
        self.wild_checkbox = QCheckBox("Wild Mode")
        self.wild_checkbox.stateChanged.connect(self.on_param_changed)
        layout.addWidget(self.wild_checkbox)

        # Control Buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        
        self.start_btn.clicked.connect(self.handle_start)
        self.stop_btn.clicked.connect(self.handle_stop)
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # Status
        self.status_label = QLabel("Status: Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def refresh_devices(self):
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            name = f"{i}: {dev['name']}"
            self.in_combo.addItem(name)
            self.out_combo.addItem(name)

    def on_param_changed(self):
        preset = self.preset_combo.currentText()
        intensity = self.intensity_slider.value() / 100.0
        wild = self.wild_checkbox.isChecked()
        self.engine.update_params(preset, intensity, wild)

    def handle_start(self):
        try:
            in_idx = int(self.in_combo.currentText().split(":")[0])
            out_idx = int(self.out_combo.currentText().split(":")[0])
            self.engine.state.input_device = in_idx
            self.engine.state.output_device = out_idx
            
            self.on_param_changed()
            self.engine.start()
            
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("Status: Processing Audio...")
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")

    def handle_stop(self):
        self.engine.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: Stopped")

# --- Main Entry ---

if __name__ == "__main__":
    # Deterministic config instantiation
    app_config = AppConfig()
    engine = AudioEngine(app_config)
    
    qt_app = QApplication(sys.argv)
    window = LindsayAudioApp(engine, app_config)
    window.show()
    
    sys.exit(qt_app.exec())