import sounddevice as sd
import numpy as np
import ipywidgets as widgets
from pedalboard import Pedalboard, Compressor, Reverb, HighpassFilter
from IPython.display import display
import threading

class SovereignWASAPIWidget:
    def __init__(self):
        # 1. Setup Pedalboard Effects (Bypass - No effects)
        self.board = Pedalboard([])
        
        self.running = False
        self.stream = None
        
        # 2. Find WASAPI Loopback Devices
        devices = sd.query_devices()
        wasapi_api_index = next((i for i, api in enumerate(sd.query_hostapis()) if "WASAPI" in api['name']), None)
        
        self.loopback_options = {}
        if wasapi_api_index is not None:
            for i, d in enumerate(devices):
                # On Windows WASAPI, output devices can be used as loopback inputs
                if d['hostapi'] == wasapi_api_index and d['max_output_channels'] > 0:
                    name = f"LOOPBACK: {d['name']}"
                    self.loopback_options[name] = i

        # 3. UI Elements
        self.device_dropdown = widgets.Dropdown(
            options=self.loopback_options.keys(),
            description='Source:',
            style={'description_width': 'initial'},
            layout={'width': 'max-content'}
        )
        
        self.toggle_btn = widgets.ToggleButton(
            value=False,
            description='START WEB/DESKTOP LISTEN',
            button_style='danger',
            icon='headphones',
            layout={'height': '40px'}
        )
        
        self.status = widgets.Label(value="Status: Ready to capture desktop audio.")
        
        self.toggle_btn.observe(self.on_toggle, names='value')
        
        display(widgets.VBox([
            widgets.HTML("<h3>Sovereign Web-Audio Link</h3>"),
            widgets.HTML("<p>Capturing desktop audio via WASAPI Loopback (No cables needed)</p>"),
            self.device_dropdown,
            self.toggle_btn,
            self.status
        ]))

    def audio_callback(self, indata, outdata, frames, time, status):
        if status:
            print(status)
        # Process the captured loopback audio through Pedalboard
        # outdata is what we hear (processed)
        processed = self.board(indata, sd.query_devices(self.device_dropdown.value)['default_samplerate'])
        outdata[:] = processed

    def on_toggle(self, change):
        if change['new']:
            self.start_stream()
        else:
            self.stop_stream()

    def start_stream(self):
        try:
            device_idx = self.loopback_options[self.device_dropdown.value]
            device_info = sd.query_devices(device_idx)
            samplerate = int(device_info['default_samplerate'])
            
            # WASAPI Loopback requires specific settings
            wasapi_settings = sd.WasapiSettings(loopback=True)
            self.stream = sd.Stream(
                device=(device_idx, device_idx), # Use same device for loopback input and output
                samplerate=samplerate,
                channels=2,
                callback=self.audio_callback,
                extra_settings=wasapi_settings
            )
            self.stream.start()
            self.running = True
            self.toggle_btn.description = 'STOP LISTENING'
            self.toggle_btn.button_style = 'success'
            self.status.value = f"Status: Capturing from {self.device_dropdown.value}..."
        except Exception as e:
            self.status.value = f"Error: {str(e)}"
            self.toggle_btn.value = False

    def stop_stream(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.running = False
        self.toggle_btn.description = 'START WEB/DESKTOP LISTEN'
        self.toggle_btn.button_style = 'danger'
        self.status.value = "Status: Capture Stopped."

# Usage: 
# ui = SovereignWASAPIWidget()
