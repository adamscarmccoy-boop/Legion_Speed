import json
import os

path = r"C:\WEB CASE STUDY\Sovereign_Mastering_Audit_Notebook.ipynb"
if not os.path.exists(path):
    print("Notebook not found!")
    exit(1)

with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

new_cell = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 📊 Sovereign V2 DSP Engine Architecture & Telemetry Specs\n",
        "\n",
        "### 1. Stateful Block-by-Block Processing (Click-Free)\n",
        "To apply the time-varying parameter curves predicted by the ONNX model, the engine processes the audio in contiguous 100ms blocks. However, to prevent boundary popping, the engine:\n",
        "* Reuses a single `Pedalboard` instance.\n",
        "* Updates parameters in-place on the existing filter and compressor nodes.\n",
        "* Processes each block with `reset=False` to preserve internal memory/state lines of the DSP nodes.\n",
        "\n",
        "### 2. Physical Phase & Peak Alignment\n",
        "* **Sub-Bass Summing:** The stereo track below 150 Hz is summed to mono to guarantee a tight, punchy low-end and prevent stereo phase cancellation on club sound systems.\n",
        "* **Master Limiter Catch:** Because summing/filtering shifts phases and changes peak heights, a final brickwall `Limiter` is run at the very end of the signal path. This prevents the peak overshoots from clipping or getting hard-clamped at `[-1.0, 1.0]`.\n",
        "* **Phase Correlation Check:** The phase correlation coefficient ($R$) between Left and Right channels is calculated above 150 Hz. A value $> 0.0$ indicates a healthy stereo image (no anti-phase cancellations).\n",
        "\n",
        "### 3. Prometheus Telemetry (`metrics.prom`)\n",
        "On every run, the engine writes physical metrics to the Prometheus scrape target files at:\n",
        "* `C:\\WEB CASE STUDY\\sovereign_production\\08_logs\\metrics.prom`\n",
        "* `C:\\WEB CASE STUDY\\logs\\metrics.prom`\n",
        "\n",
        "Metrics exported:\n",
        "* `sovereign_mastering_duration_seconds` (latency)\n",
        "* `sovereign_final_rms_db` (loudness)\n",
        "* `sovereign_phase_correlation` (phase correlation)\n",
        "* `sovereign_stereo_width` (stereo width)\n",
        "* `sovereign_peak_L_db` & `sovereign_peak_R_db` (channel peak dBFS)\n",
        "\n",
        "### 4. Gemma Audit Package\n",
        "The metadata is packed into a sidecar `.dna.json` file next to the mastered WAV, which contains the complete telemetry required by the Gemma reasoning council."
    ]
}

# Append the new cell to the notebook cells list
nb["cells"].append(new_cell)

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2)

print("Notebook updated with telemetry documentation cell!")
