# Gemini Spark Workstation Orchestration Playbook
## 24/7 Agentic Control of the Code Forest Ingestion Pipeline

This orchestration playbook defines the tasks, skills, and schedules required for **Gemini Spark** to manage, audit, and coordinate your local physical workstation data ingestion engine. 

By leveraging **Gemini Spark's persistent cloud runtime** alongside your **local execution agent running on Port 8099**, you establish a continuous, closed-loop developer environment.

---

## 🗺️ System Architecture

```
   ┌────────────────────────────────────────────────────────┐
   │            Google Cloud: Gemini Spark (24/7)           │
   │  Manages schedules, tracks background tasks, plans      │
   └───────────────────────────┬────────────────────────────┘
                               │
                Secure Web Tunnel / Loopback
                               │
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │         Local Workstation Agent (Port 8099)            │
   │  - Orchestrates OS commands & compilations             │
   │  - Spawns DuckDB / LanceDB database pipelines          │
   │  - Runs ONNX metrics classification models             │
   └───────────────────────────┬────────────────────────────┘
                               │
             Coordinates Databases & Inference Loops
                               │
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │        Local Services, DBs, and LLM Engines            │
   │  - DuckDB/LanceDB (Port 8001 RAG Services)             │
   │  - LM Studio C++ Inference Kernel (Port 1234/1010)     │
   └────────────────────────────────────────────────────────┘
```

---

## 🎯 1. Spark Task Blueprint (The Goal)
*Copy and paste this exact prompt into the **Tasks** panel of your Gemini Spark application to establish the main objective.*

```text
Objective: Audit, ingest, and synchronize workspace code metrics from the local file system into DuckDB and LanceDB, leveraging the local automation engine.

Execution Steps:
1. Establish contact with the local helper agent running on loopback address: http://127.0.0.1:8099.
2. Direct the 8099 agent to run the Code Forest Engine recursive folder crawler to gather size, extensions, and row counts of active directories.
3. Validate that the DuckDB relational schema (workspace_metrics) and LanceDB vector store are initialized correctly.
4. Instruct the local compiler (using modern C++17 and the active headers) to compile any pending database bindings into the .dll or .so output.
5. Retrieve the current processing logs from the C++ inference engine (main.log) via the local agent to verify no context overflows or hardware constraint boundaries are being hit.
6. Package a consolidated Daily Diagnostic Summary and push any anomalies to the local WebUI workspace directory.
```

---

## 🛠️ 2. Spark Skill Templates (The How)
*Save these individual configurations in the **Skills** panel of your Spark agent so they can be reused across multiple background execution runs.*

### Skill A: `@QueryLocalAgent8099`
* **Purpose**: Dispatches structured execution requests to your local helper agent.
* **Instruction Payload**:
  ```text
  When executing a workstation task, construct a secure POST request to http://127.0.0.1:8099/execute with a JSON payload specifying the action ("run_crawler", "compile_cpp", "get_system_logs"). Always parse the returned stdout and exit code. If the port is unresponsive, attempt fallback scanning on adjacent loopback ports (8001, 1234) and flag any offline services to the user.
  ```

### Skill B: `@ValidateDatabaseState`
* **Purpose**: Inspects and queries active database states through the Port 8001 REST API.
* **Instruction Payload**:
  ```text
  Send a GET request to http://127.0.0.1:8001/status to check the connection status of DuckDB and LanceDB. Parse the JSON return structure to verify:
  1. The "workspace_metrics" table contains columns: file_path, file_extension, file_size, line_count, anomaly_score, and classification.
  2. The total row count in the database is greater than 0.
  If the tables are empty or uninitialized, run the schema setup script.
  ```

### Skill C: `@DiagnoseInferenceHealth`
* **Purpose**: Monitors GGUF and LM Studio memory limits.
* **Instruction Payload**:
  ```text
  Request the last 100 lines of "main.log" from the local agent. Parse the logs for the following keywords: "CUDA error", "Out of Memory", "OOM", "context limit exceeded", or "slot full". If found, cross-reference with "hardware-config.json" and recommend reducing active GPU offload layers or shrinking the context window parameter.
  ```

---

## 📅 3. Spark Schedule Configuration (The When)
To transform your workstation pipeline from a manual system into a proactive helper, set up the following automated schedule within Gemini Spark:

*   **Trigger**: Daily at **2:00 AM** (Local Workstation Time)
*   **Active Job Budget**: Consumes **1** background task slot (leaving 14 available for concurrent tasks).
*   **Schedule Flow**:
    1.  Wake up and ping the Port **8099** agent.
    2.  Execute the physical folder crawl while development activity is zero.
    3.  Generate the Scikit-Learn predictions and update the DuckDB rows.
    4.  Deliver a **"Codebase Ingestion & Anomaly Report"** directly to your mobile Gemini app when you wake up.

---

## 🛡️ Human-in-the-Loop Safeguards
Because Gemini Spark works directly with your physical operating system and database layers, the following security guardrails are active:
*   **Write Operations**: Spark is restricted from executing direct file overwrites or directory deletions without prompting for an explicit **"Click to Approve"** push notification on your device.
*   **Safe-Exclude Paths**: The folder crawler is hardcoded to completely ignore and skip system directories, virtual environments (`.venv_314`), node modules (`node_modules`), and version control metadata (`.git`) to keep system memory consumption low.
