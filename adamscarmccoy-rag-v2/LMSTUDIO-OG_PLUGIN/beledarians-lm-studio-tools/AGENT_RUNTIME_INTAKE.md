# AGENT RUNTIME INTAKE

## Target Workflow
**One Sentence Goal:** Enable LM Studio to interact with local files, execute code, browse the web, and use secondary agents via a plugin-based tool system.

**Steps in Order:**
1. User prompt enters LM Studio
2. Prompt preprocessor injects tool documentation into context
3. LLM generates a response that may include tool invocations
4. Plugin executes tools (file ops, code execution, web search, secondary agent) and returns results
5. Tool results are fed back to LLM for further reasoning
6. Iterate until task complete

**Success Condition:** The LLM successfully completes the user's requested task using the available tools, with all file writes and command executions confined to the workspace.

**Workspace Path:** C:\WEB CASE STUDY\adamscarmccoy-rag-v2\LMSTUDIO-OG_PLUGIN\beledarians-lm-studio-tools

**Allowed Write Roots:**
- C:\WEB CASE STUDY\adamscarmccoy-rag-v2\LMSTUDIO-OG_PLUGIN\beledarians-lm-studio-tools

**Allowed Commands:**
- read_file
- save_file
- replace_text_in_file
- search_directory
- execute_command
- run_in_terminal
- web_search
- wikipedia_search
- rag_local_files
- run_background_command
- check_background_command
- cancel_background_command
- list_directory
- make_directory
- delete_path
- delete_files_by_pattern

## LM Studio JavaScript Boundary
**Integration Type:** plugin

**LM Studio Version:** unknown
**Model Identifier:** unknown
**Embedding Model Identifier:** nomic-ai/nomic-embed-text-v1.5-GGUF

**JavaScript Entry File:** src/index.ts

**Supported Hook Name:** promptPreprocessor

**Can Modify Prompt Before Generation:** yes
**Can Receive Streaming Events:** unknown
**Can Make Local HTTP Requests:** yes
**Can Open Unix Sockets:** unknown

**Current Request Code:**
```
// Plugin uses LM Studio SDK; message handling is internal to SDK. See index.ts for registration.
```

**Current Message Shape:**
```
{ role: 'user', content: 'user query string' }
```

## Existing Python ACP / Jinja Implementation
**Worked Before:** no
**Python Version:** N/A
**ACP Name/Protocol:** N/A
**Jinja Used:** no
**Python Entry File:** N/A

**Working Python Request Code:**
```
N/A
```

**Jinja Template:**
```
N/A
```

**Multi-Turn Trace:**
```
N/A
```

## Ray Boundary
**Status:** D_conceptual_only

**Ray Version:** N/A
**Ray Serve Used:** no
**Python Allowed for Ray Control Plane:** no
**Java Allowed for Ray Control Plane:** no

**Ray Head Address:** N/A
**Ray HTTP Address:** N/A
**Ray Worker Addresses:** [N/A]

**Ray Deployments/Actors:**
- Name: N/A, Language: N/A, Input Schema: N/A, Output Schema: N/A, Status: N/A

**Ray Request Code:**
```
NOT_IMPLEMENTED
```

**Ray Constraints:**
- N/A

## Forest / ONNX Native Inference Layer
**Forest Exists:** no
**Forest Language:** N/A
**Forest Interface:** N/A

**ONNX Runtime:** N/A
**Execution Providers:** []

**Models:**
- Name: N/A, Path/Identifier: N/A, Input Names: [N/A], Input Shapes: [N/A], Output Names: [N/A], Output Shapes: [N/A], Dtype: N/A, Status: N/A

**Native Input Example:**
```
N/A
```

**Native Output Example:**
```
N/A
```

**Forest API Code:**
```
N/A
```

## DuckDB and Lance Boundary
**DuckDB Version:** N/A
**DuckDB Language Binding:** N/A

**Lance Status:** N/A

**DuckDB and Lance Same Process:** N/A

**Extension Path:** N/A
**Database Path:** N/A
**Lance Table Path:** N/A

**Working SQL:**
```
N/A
```

**Working C++ Database Code:**
```
N/A
```

**Current Schema:**
```
N/A
```

**Desired Native Operators:**
- N/A

**Large Data Must Stay Native:** N/A

## AST and Code-Context System
**Parser:** unknown
**Supported Languages:** []

**AST Index Exists:** no
**Dependency Graph Exists:** no
**Code Quality Filter Exists:** no

**Retrieval Sequence:** []

**AST Output Example:**
```
N/A
```

**Context Output Example:**
```
N/A
```

**Context Budget Tokens:** N/A
**Minimum Code Quality Score:** N/A
**Maximum AST Expansion Depth:** N/A

## Monty / File and Command Execution
**Monty Exists:** yes
**Monty Interface:** HTTP
**Monty Process Address:** http://localhost:1234/v1 (from secondaryAgentEndpoint setting)

**Write File Supported:** yes
**Run Command Supported:** yes
**Read File Supported:** yes

**Write File Request:**
Save content to a specified file in the current working directory. Returns full path.

**Write File Response:**
{ success: true, paths: ['/full/path/to/file.txt'], errors: undefined }

**Run Command Request:**
Execute a shell command in the current working directory. Returns stdout and stderr.

**Run Command Response:**
{ stdout: 'command output', stderr: '' }

**Required Safety Rules:**
- workspace_only
- no_network_by_default
- allowlisted_commands_only
- timeout_commands
- return_file_hashes
- return_structured_diagnostics

## Desired Communication Protocol
**Preferred Transport:** HTTP

**Streaming Required:** unknown
**Preferred Stream:** unknown

**Single Gateway Process:** yes
**Native Gateway Language:** TypeScript
**Ray Handles Only Control Messages:** N/A

**Large Tensors Cross Process:** N/A

**Shared Memory Allowed:** no
**Maximum Request Latency Ms:** N/A
**Maximum Retrieval Latency Ms:** N/A
**Maximum Generation Context Tokens:** N/A

**Required Event Types:**
- retrieval.started
- retrieval.finished
- context.compiled
- draft.generated
- tool.requested
- tool.result
- build.finished
- test.finished
- agent.completed
- agent.failed

## Assumptions: Confirm or Correct These
**A01:**
- **Assumption:** LM Studio JavaScript can call a local HTTP or Unix-socket gateway.
- **Correct:** yes
- **Correction:** Plugin can make HTTP requests via web_search tool and secondary agent HTTP endpoint.

**A02:**
- **Assumption:** The LM Studio integration can inject or replace prompt context before generation.
- **Correct:** yes
- **Correction:** Prompt preprocessor injects tool documentation and system prompts.

**A03:**
- **Assumption:** Ray should carry request/session/control state, not large tensors.
- **Correct:** unknown
- **Correction:** Ray not used in this plugin.

**A04:**
- **Assumption:** Forest/ONNX sessions should remain warm inside a native worker.
- **Correct:** unknown
- **Correction:** Forest/ONNX not used.

**A05:**
- **Assumption:** DuckDB should compose model outputs as typed columns or relations.
- **Correct:** unknown
- **Correction:** DuckDB not used.

**A06:**
- **Assumption:** Lance is used for vector retrieval while DuckDB performs relational composition, filtering, ranking, and projection.
- **Correct:** unknown
- **Correction:** Lance/DuckDB not used.

**A07:**
- **Assumption:** AST expansion should preserve symbol and dependency coherence rather than simply returning top-k text chunks.
- **Correct:** unknown
- **Correction:** AST not used.

**A08:**
- **Assumption:** Monty should receive typed file/build actions and return structured tool results.
- **Correct:** yes
- **Correction:** Secondary agent and file tools return structured JSON results.

**A09:**
- **Assumption:** Compiler and test diagnostics should re-enter the same retrieval/AST/context loop.
- **Correct:** unknown
- **Correction:** Not applicable.

**A10:**
- **Assumption:** The first implementation should target one complete code-agent workflow before generalizing the protocol.
- **Correct:** yes
- **Correction:** Plugin provides a full toolset for file, code, web, and agent interactions.