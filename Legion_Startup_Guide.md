# Legion Sonic Engine & OpenClaw Swarm Startup Guide

This guide covers the exact steps and correct environments required to launch the complete Autonomous Audio Mastering architecture, ensuring API blockers and token safeguards are strictly enforced.

---

## 1. Launching the OpenClaw Swarm Control Center
We have consolidated the entire OpenClaw infrastructure into a single executable batch script on your Desktop.

**Action**: Double-click `Start_OpenClaw.bat` on your Desktop.

This script sequentially executes:
1. **Ollama**: Boots the local inferencing server in the background.
2. **OpenClaw Gateway**: Starts the secure gateway node silently.
3. **Web Dashboard**: Automatically pops open the OpenClaw UI in your default browser.
4. **Terminal Interface**: Drops you into the active OpenClaw terminal session.

*Note: Your `openclaw.json` has been hardcoded to map the NVIDIA NIM API (`nvidia/nemotron-3-ultra-550b-a55b`) as the primary inference provider.*

---

## 2. Launching the Legion Swarm Backend (API Bridge)
The `api_bridge.py` is the orchestrator that sits between your UI and the backend C++/DSP PyTorch pipelines (`torchaudio`, `librosa`). 

**CRITICAL RULE**: The primary `C:\WEB CASE STUDY\.venv` is corrupted and missing key PyTorch binaries. You **must** always use your backup `E:` drive virtual environment, which has all dependencies pre-compiled and intact.

**Action**: Run the following command from any terminal to launch the API bridge:

```powershell
& "E:\WEB CASE STUDY\.venv\Scripts\python.exe" "C:\WEB CASE STUDY\antigravity_vscode_ext\backend\api_bridge.py"
```

When this boots:
1. It starts a FastAPI server on **Port 8000**.
2. It initializes the `LegionLangGraphAgent` (powered by Google GenAI).
3. It binds your custom C++ DSP Python tools (`analyze_audio_structure` & `apply_dynamic_mastering`) directly to the LLM's brain.

---

## 3. Built-In Token Safeguards
To prevent runaway loops, infinite recursion, and massive token bills during experimental agentic orchestration, we have hardcoded strict physical limits into the pipeline:

- **LangGraph Brain (`legion_langgraph_brain.py`)**: `max_recursion_limit = 1`
- **GenAI Fallback (`api_bridge.py`)**: `max_tool_iterations = 1`

**What this means:** The Swarm backend is mathematically restricted to executing exactly **one** DSP tool or operation per prompt. If it hallucinates or gets confused, it will immediately stop execution and hand control back to you. It is 100% safe to operate.
