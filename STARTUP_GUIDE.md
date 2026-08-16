# 🚀 Startup Guide: Modelship & vLLM Deployment

This guide outlines the exact steps required to restart the inference stack and the API gateway.

## 🛠️ System Configuration
- **Project Root:** `C:\WEB CASE STUDY`
- **Model:** `Qwen/Qwen2.5-Coder-1.5B-Instruct-AWQ`
- **Backend:** vLLM (via Modelship)
- **Environment:** `C:\WEB CASE STUDY\.venv` (Python 3.12.10)
- **Package Manager:** `uv`

---

## ⚠️ Critical Requirements (Read First)

### 1. Administrator Privileges
**You MUST run your terminal as Administrator.** 
Ray requires elevated privileges on Windows to start the head node and manage system resources. Running as a standard user will result in `WinError 740` (The requested operation requires elevation).

### 2. Environment Locks
Windows often locks the `.venv` folders if background Python or Ray processes are still running. To avoid "Access is denied" errors during startup, always use the `--no-sync` flag with `uv`.

### 3. The `special_hardware` Fix
The vLLM deployment for Qwen requests a custom resource: `special_hardware: 1.0`. 
This has been hardcoded into `modelship\deploy\serve_utils.py` in the `_own_cluster_init_kwargs` function. This allows the local Ray cluster to satisfy the resource request and move from `DEPLOYING` to `ACTIVE`.

---

## 🏁 Execution Steps

### Step 1: Clear Zombie Processes
Before starting, ensure no stale Ray or Python processes are locking the environment or ports.
```powershell
# Run this in Admin PowerShell
Get-Process python, ray* -ErrorAction SilentlyContinue | Stop-Process -Force
```

### Step 2: Launch the Stack
Run the deployment script using `uv`. This will start the Ray cluster, deploy the vLLM model, and launch the OpenAI-compatible API gateway.

```powershell
cd 'C:\WEB CASE STUDY\modelship\modelship-main'
uv run --no-sync python mship_deploy.py
```

### Step 3: Verify Connectivity
Once the terminal shows `Deployed app 'modelship api' successfully`:
- **API Gateway:** `http://localhost:8000`
- **Ray Dashboard:** `http://localhost:8265`

---

## 📂 Resource Map

| Asset | Path | Note |
| :--- | :--- | :--- |
| **Model Weights** | `C:\Users\adams\.cache\huggingface\hub` | Default HF cache; no redownload needed. |
| **DNA Memory** | `C:\WEB CASE STUDYay_categories.parquet` | Used by `mcp_legion-architect`. |
| **Sovereign Manifest** | `C:\.genkit\sovereign_manifest.json` | Defines the DNA Engine architecture. |
| **Bridge Logic** | `C:\.genkit\gemini_bridge.py` | Orchestrates MCP tool dispatching. |

---

## 🔍 Troubleshooting

| Error | Cause | Solution |
| :--- | :--- | :--- |
| `WinError 740` | Not running as Admin | Restart Terminal as Administrator. |
| `Access is denied (os error 5)` | File lock on `.venv` | Use `uv run --no-sync` or kill python processes. |
| `Stuck in DEPLOYING` | Missing `special_hardware` | Ensure `serve_utils.py` has the `resources` fix. |
| `Authentication failed` | HF Token missing | Set `$env:HF_TOKEN='your_token'`. |
