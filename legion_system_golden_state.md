# LEGION MATRIX SYSTEM COGNITIVE MANIFEST (GOLDEN STATE)

This document maps out every single physical configuration, software boundary, and distributed routing path that has been **empirically proven and verified functional** on your local machine.

---

## 1. HOST HARDWARE & OPERATING SYSTEM
*   **Operating System**: Windows 11 [115]
*   **Default Shell**: `C:\Windows\system32\cmd.exe` [115]
*   **Active Workspace Root**: `C:\STUDIES` [115]
*   **Active Project Root**: `C:\WEB CASE STUDY` [425]
*   **Physical GPU**: NVIDIA GeForce GTX 1650 SUPER [161]
    *   **VRAM Allocation**: 4095 MiB total [172]
    *   **Thermal Envelope**: Stable operational temperature range of 50°C to 62°C [1, 116]

---

## 2. LOCAL INFERENCE ENGINE (LM STUDIO CORE)
The raw C++ `llama.cpp` inference backend is highly optimized and running with the following verified metrics:

### Hardware-Level Layer Splitting
*   **CUDA Hybrid Offloading**: The allocator successfully splits GGUF layers between GPU and CPU [400]. 
    *   *Example*: Out of 42 model layers, **23 layers offload to CUDA GPU VRAM (~1,457 MiB)**, while the remaining **19 layers map to System RAM via `mmap` (~1,240 MiB)**, leaving sufficient headroom on a 4GB card [400].
*   **SSM State Buffering**: Allocates **324 MiB** for `llama_memory_recurrent` state arrays, enabling native, fused-kernel SSM (Mamba-2) token evaluation [400].

### Dynamic JIT Cache Performance
*   **VRAM Prompt Cache**: Successfully stores context checkpoints directly in GPU memory [402].
*   **Warm Restores**: Restores **81.088 MiB context checkpoints** (representing 894 tokens of historical context) directly from VRAM in exactly **720.57 ms** (processing at **123.51 tokens per second**) [5].

---

## 3. VERIFIED LOCAL MODELS & CONFIGURATIONS

### A. The Reasoner: `nvidia/nemotron-3-nano-4b`
*   **Architecture**: Hybrid Mamba-2 / State-Space Model (SSM) [372].
*   **Operational Sizing (The Runway)**:
    *   *Single-Agent Focus (`n_parallel=1`)*: Supports a context runway of up to **28,160 tokens** [53].
    *   *Swarm Mode (`n_parallel=4`)*: Restricts individual context slots to **16,128 tokens** [1, 2].
*   **Zero-Entropy Sampler Parameters**:
    *   `temperature = 0.000` (Forces mathematical precision for port and structural audits) [1, 5]
    *   `repeat_penalty = 1.100` [5]
    *   `top_k = 40` [5]
    *   `min_p = 0.05` [5]
*   **Prefill Throughput**: Reaches **148.33 tokens per second** [370] on local GPU loopback due to $O(N)$ linear complexity [372].

### B. The Embedder: `text-embedding-snowflake-arctic-embed-l-v2.0`
*   **Output Vector Space**: Dense **1024-dimension float vectors** [339, 341].
*   **Proven LM Studio Sizing Flags**:
    *   To prevent 7.6GB activation buffer allocation crashes (`failed to decode, ret = -2`) on your 4GB card [8], manually restrict the downstream limits to:
        *   `n_batch = 512` [10, 15]
        *   `n_ubatch = 256` [15]
    *   This forces the backend to segment massive document inputs into micro-batches, dropping peak VRAM requirements to **under 500MB** [262].

---

## 4. PROVEN RAY CLUSTER TOPOLOGY
Your machine is verified running a local, production-grade distributed actor mesh [336].

*   **Ray Head Node Address**: `127.0.0.1:6379` [14]
*   **Ray Dashboard Port**: `8265` [14]
*   **Central State GCS**: Port `6379` [257]
*   **Unified Namespace**: `"legion"` [1]

### Verified Ray Serve Deployments (Port 8000)
Requests routed via the local HTTP Proxy Actor map cleanly to the following live deployment routes:

| Route Signature | Target Deployment Class | Loaded Weights / Models |
| :--- | :--- | :--- |
| **`/`** | `SovereignSieve` [424] | In-memory binary matrices (`bridge.bin`, `brain.bin`) [424, 425] |
| **`/dna`** | `DNADeployment` [424] | ONNX Graph `C:\WEB CASE STUDY\dna_brain.onnx` [393] |
| **`/latent`** | `LatentDeployment` [424] | ONNX Model `C:\WEB CASE STUDY\fretflow_omni_v4.onnx` [393, 441] |
| **`/param`** | `ParamDeployment` [424] | — |
| **`/render`** | `SovereignRenderDeployment` [424] | — |

---

## 5. RE-INITIALIZED DATABASE SHELLS

### A. LanceDB (The Vector Store)
*   **Hard Connection Path**: `C:\STUDIES_BACKUP\vectors\lancedb_store` [471]
*   **Active Table: `audio_vibe_gpu`**
    *   *Schema*: `['filename', 'filepath', 'vector']` [471]
    *   *Confirmed Status*: Connected cleanly, currently sitting on **0 rows** (ready for ingestion) [471].
*   **Active Table: `legion_memory`**
    *   *Schema*: `['id', 'role', 'text', 'vector', 'timestamp']` [471]
    *   *Confirmed Status*: Connected cleanly, currently sitting on **0 rows** [471].

### B. DuckDB (The Analytical Store)
*   **Hard Connection Path**: `C:\STUDIES\data\metadata\sonic_core.duckdb` [77]
*   **Verified Extension**: Exposes native `lance` extension integration for unified SQL queries across vector slices [447].

---

## 6. ACTIVE DAEMON PORT REGISTRY
The following background servers successfully bind to local loopback concurrent ports without socket collisions:

*   **Port `1234` / `1010`**: LM Studio local GGUF server [163, 425]
*   **Port `8001`**: MCP API Gateway Server (`mcp_api_server.py`) [425]
*   **Port `8005`**: MCP RAG Server (`mcp_rag_server.py --sse`) [425]
*   **Port `8787`**: Cloudflare Local Worker [425]
*   **Port `6379`**: Ray GCS [425]
*   **Port `8265`**: Ray Dashboard [14]

---

## 7. PHYSICAL PATH DIRECTORY
Use these hard paths when feeding data or mapping volumes inside your new chat:

*   **Workspace Folder**: `C:\STUDIES` [37]
*   **Case Study Folder**: `C:\WEB CASE STUDY` [318, 425]
*   **Active SQLite Catalog**: `C:\STUDIES\chroma_db\chroma.sqlite3` [77]
*   **DuckDB Database**: `C:\STUDIES\data\metadata\sonic_core.duckdb` [77]
*   **LM Studio Logger Output**: `C:\Users\adams\.lmstudio\logs\main.log` [116]
*   **ONNX Diffusion Transformer**: `C:\WEB CASE STUDY\fretflow_omni_v4.onnx` [393, 441]
*   **ONNX DNA Handler**: `C:\WEB CASE STUDY\dna_brain.onnx` [393]
