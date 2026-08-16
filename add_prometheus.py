import nbformat

path = r'C:\.genkit\Sovereign_Audio_Intelligence_Generative_WhitePaper.ipynb'

with open(path, 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

md_prom = nbformat.v4.new_markdown_cell(
    "## 📉 Live Prometheus Telemetry\n"
    "The system is monitored via a dedicated **Prometheus** loop. Below we scrape the current pipeline performance directly from the `metrics.prom` telemetry file."
)

code_prom = nbformat.v4.new_code_cell(
    "import os\n"
    "import time\n"
    "\n"
    "def get_latest_metric(metric_name, log_path=r\"C:\\WEB CASE STUDY\\sovereign_production\\08_logs\\metrics.prom\"):\n"
    "    try:\n"
    "        if not os.path.exists(log_path):\n"
    "            return \"Log file not found.\"\n"
    "        with open(log_path, \"r\", encoding=\"utf-8\") as f:\n"
    "            lines = f.readlines()\n"
    "            for line in reversed(lines):\n"
    "                if metric_name in line:\n"
    "                    return line.split(\" \")[1].strip()\n"
    "    except Exception as e:\n"
    "        return f\"Error: {e}\"\n"
    "    return \"N/A\"\n"
    "\n"
    "latency = get_latest_metric(\"sovereign_total_pipeline_latency_seconds\")\n"
    "print(f\"⏱️ Current Pipeline Latency: {latency} seconds\")\n"
)

# Insert the Prometheus cells after the executive summary (index 0)
nb.cells.insert(1, md_prom)
nb.cells.insert(2, code_prom)

with open(path, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print("✅ Inserted Prometheus Telemetry Cells!")
