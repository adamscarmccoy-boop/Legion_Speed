PROJECT = {
    # ------------------------------------------------------------------
    # A. Target workflow
    # ------------------------------------------------------------------
    "target_workflow": {
        "one_sentence_goal": (
            "Enable LM Studio to interact with local files, execute code, browse the web, and use secondary agents via a plugin-based tool system."
        ),

        "steps_in_order": [
            "User prompt enters LM Studio",
            "Prompt preprocessor injects tool documentation into context",
            "LLM generates a response that may include tool invocations",
            "Plugin executes tools (file ops, code execution, web search, secondary agent) and returns results",
            "Tool results are fed back to LLM for further reasoning",
            "Iterate until task complete"
        ],

        "success_condition": (
            "The LLM successfully completes the user's requested task using the available tools, with all file writes and command executions confined to the workspace."
        ),

        "workspace_path": "C:\\\\WEB CASE STUDY\\\\adamscarmccoy-rag-v2\\\\LMSTUDIO-OG_PLUGIN\\\\beledarians-lm-studio-tools",
        "allowed_write_roots": [
            "C:\\\\WEB CASE STUDY\\\\adamscarmccoy-rag-v2\\\\LMSTUDIO-OG_PLUGIN\\\\beledarians-lm-studio-tools"
        ],
        "allowed_commands": [
            "read_file", "save_file", "replace_text_in_file", "search_directory", "execute_command", "run_in_terminal", "web_search", "wikipedia_search", "rag_local_files", "run_background_command", "check_background_command", "cancel_background_command", "list_directory", "make_directory", "delete_path", "delete_files_by_pattern"
        ],
    },

    # ------------------------------------------------------------------
    # B. LM Studio JavaScript boundary
    # ------------------------------------------------------------------
    "lm_studio": {
        "integration_type": (
            "plugin"
        ),

        "lm_studio_version": "unknown",
        "model_identifier": "unknown",
        "embedding_model_identifier": (
            "nomic-ai/nomic-embed-text-v1.5-GGUF"
        ),

        "javascript_entry_file": "src/index.ts",

        "supported_hook_name": (
            "promptPreprocessor"
        ),

        "can_modify_prompt_before_generation": "yes",
        "can_receive_streaming_events": "unknown",
        "can_make_local_http_requests": "yes",
        "can_open_unix_sockets": "unknown",

        "current_request_code": r"""
// Plugin uses LM Studio SDK; message handling is internal to SDK. See index.ts for registration.
""",

        "current_message_shape": r"""
{ role: 'user', content: 'user query string' }
""",
    },

    # ------------------------------------------------------------------
    # C. Existing Python ACP / Jinja implementation
    # ------------------------------------------------------------------
    "old_python_acp": {
        "worked_before": "no",
        "python_version": "N/A",
        "acp_name_or_protocol": "N/A",
        "jinja_used": "no",
        "python_entry_file": "N/A",

        "working_python_request_code": r"""
N/A
""",

        "jinja_template": r"""
N/A
""",

        "multi_turn_trace": r"""
N/A
""",
    },

    # ------------------------------------------------------------------
    # D. Ray boundary
    # ------------------------------------------------------------------
    "ray": {
        "status": (
            "D_conceptual_only"
        ),

        "ray_version": "N/A",
        "ray_serve_used": "no",
        "python_allowed_for_ray_control_plane": (
            "no"
        ),
        "java_allowed_for_ray_control_plane": (
            "no"
        ),

        "ray_head_address": "N/A",
        "ray_http_address": "N/A",
        "ray_worker_addresses": [
            "N/A"
        ],

        "ray_deployments_or_actors": [
            {
                "name": "N/A",
                "language": "N/A",
                "input_schema": "N/A",
                "output_schema": "N/A",
                "status": "N/A",
            }
        ],

        "ray_request_code": r"""
NOT_IMPLEMENTED
""",

        "ray_constraints": [
            "N/A",
        ],
    },

    # ------------------------------------------------------------------
    # E. Forest / ONNX native inference layer
    # ------------------------------------------------------------------
    "forest_onnx": {
        "forest_exists": "no",
        "forest_language": "N/A",
        "forest_interface": (
            "N/A"
        ),

        "onnx_runtime": "N/A",
        "execution_providers": [],

        "models": [
            {
                "name": "N/A",
                "path_or_identifier": "N/A",
                "input_names": ["N/A"],
                "input_shapes": ["N/A"],
                "output_names": ["N/A"],
                "output_shapes": ["N/A"],
                "dtype": "N/A",
                "status": "N/A",
            }
        ],

        "native_input_example": r"""
N/A
""",

        "native_output_example": r"""
N/A
""",

        "forest_api_code": r"""
N/A
""",
    },

    # ------------------------------------------------------------------
    # F. DuckDB and Lance boundary
    # ------------------------------------------------------------------
    "duckdb_lance": {
        "duckdb_version": "N/A",
        "duckdb_language_binding": (
            "N/A"
        ),

        "lance_status": (
            "N/A"
        ),

        "duckdb_and_lance_same_process": (
            "N/A"
        ),

        "extension_path": "N/A",
        "database_path": "N/A",
        "lance_table_path": "N/A",

        "working_sql": r"""
N/A
""",

        "working_cpp_database_code": r"""
N/A
""",

        "current_schema": r"""
N/A
""",

        "desired_native_operators": [
            "N/A",
        ],

        "large_data_must_stay_native": (
            "N/A"
        ),
    },

    # ------------------------------------------------------------------
    # G. AST and code-context system
    # ------------------------------------------------------------------
    "ast_context": {
        "parser": (
            "unknown"
        ),
        "supported_languages": [],

        "ast_index_exists": "no",
        "dependency_graph_exists": "no",
        "code_quality_filter_exists": "no",

        "retrieval_sequence": [],

        "ast_output_example": r"""
N/A
""",

        "context_output_example": r"""
N/A
""",

        "context_budget_tokens": "N/A",
        "minimum_code_quality_score": "N/A",
        "maximum_ast_expansion_depth": "N/A",
    },

    # ------------------------------------------------------------------
    # H. Monty / file and command execution
    # ------------------------------------------------------------------
    "monty": {
        "monty_exists": "yes",
        "monty_interface": (
            "HTTP"
        ),
        "monty_process_address": "http://localhost:1234/v1 (from secondaryAgentEndpoint setting)",

        "write_file_supported": "yes",
        "run_command_supported": "yes",
        "read_file_supported": "yes",

        "write_file_request": r"""
Save content to a specified file in the current working directory. Returns full path.
""",

        "write_file_response": r"""
{ success: true, paths: ['/full/path/to/file.txt'], errors: undefined }
""",

        "run_command_request": r"""
Execute a shell command in the current working directory. Returns stdout and stderr.
""",

        "run_command_response": r"""
{ stdout: 'command output', stderr: '' }
""",

        "required_safety_rules": [
            "workspace_only",
            "no_network_by_default",
            "allowlisted_commands_only",
            "timeout_commands",
            "return_file_hashes",
            "return_structured_diagnostics",
        ],
    },

    # ------------------------------------------------------------------
    # I. Desired communication protocol
    # ------------------------------------------------------------------
    "communication": {
        "preferred_transport": (
            "HTTP"
        ),

        "streaming_required": "unknown",
        "preferred_stream": "unknown",

        "single_gateway_process": "yes",
        "native_gateway_language": "TypeScript",
        "ray_handles_only_control_messages": (
            "N/A"
        ),

        "large_tensors_cross_process": (
            "N/A"
        ),

        "shared_memory_allowed": "no",
        "maximum_request_latency_ms": "N/A",
        "maximum_retrieval_latency_ms": "N/A",
        "maximum_generation_context_tokens": "N/A",

        "required_event_types": [
            "retrieval.started",
            "retrieval.finished",
            "context.compiled",
            "draft.generated",
            "tool.requested",
            "tool.result",
            "build.finished",
            "test.finished",
            "agent.completed",
            "agent.failed",
        ],
    },

    # ------------------------------------------------------------------
    # J. Assumptions: confirm or correct these
    # ------------------------------------------------------------------
    "assumptions": {
        "A01": {
            "assumption": (
                "LM Studio JavaScript can call a local HTTP or Unix-socket gateway."
            ),
            "correct": "yes",
            "correction": "Plugin can make HTTP requests via web_search tool and secondary agent HTTP endpoint."
        },
        "A02": {
            "assumption": (
                "The LM Studio integration can inject or replace prompt context "
                "before generation."
            ),
            "correct": "yes",
            "correction": "Prompt preprocessor injects tool documentation and system prompts."
        },
        "A03": {
            "assumption": (
                "Ray should carry request/session/control state, not large tensors."
            ),
            "correct": "unknown",
            "correction": "Ray not used in this plugin."
        },
        "A04": {
            "assumption": (
                "Forest/ONNX sessions should remain warm inside a native worker."
            ),
            "correct": "unknown",
            "correction": "Forest/ONNX not used."
        },
        "A05": {
            "assumption": (
                "DuckDB should compose model outputs as typed columns or relations."
            ),
            "correct": "unknown",
            "correction": "DuckDB not used."
        },
        "A06": {
            "assumption": (
                "Lance is used for vector retrieval while DuckDB performs relational "
                "composition, filtering, ranking, and projection."
            ),
            "correct": "unknown",
            "correction": "Lance/DuckDB not used."
        },
        "A07": {
            "assumption": (
                "AST expansion should preserve symbol and dependency coherence rather "
                "than simply returning top-k text chunks."
            ),
            "correct": "unknown",
            "correction": "AST not used."
        },
        "A08": {
            "assumption": (
                "Monty should receive typed file/build actions and return structured "
                "tool results."
            ),
            "correct": "yes",
            "correction": "Secondary agent and file tools return structured JSON results."
        },
        "A09": {
            "assumption": (
                "Compiler and test diagnostics should re-enter the same retrieval/"
                "AST/context loop."
            ),
            "correct": "unknown",
            "correction": "Not applicable."
        },
        "A10": {
            "assumption": (
                "The first implementation should target one complete code-agent "
                "workflow before generalizing the protocol."
            ),
            "correct": "yes",
            "correction": "Plugin provides a full toolset for file, code, web, and agent interactions."
        },
    },
}


# ----------------------------------------------------------------------
# Validation and export
# ----------------------------------------------------------------------
import json

def find_fill_me(value, path="PROJECT"):
    missing = []

    if isinstance(value, dict):
        for key, item in value.items():
            missing.extend(find_fill_me(item, f"{path}.{key}"))

    elif isinstance(value, list):
        for index, item in enumerate(value):
            missing.extend(find_fill_me(item, f"{path}[{index}]"))

    elif isinstance(value, str) and "FILL_ME" in value:
        missing.append(path)

    return missing


def redact_for_export(value):
    """
    Removes obvious secret-like fields while preserving protocol information.
    """
    secret_terms = (
        "api_key",
        "apikey",
        "token",
        "password",
        "secret",
        "authorization",
        "private_key",
    )

    if isinstance(value, dict):
        output = {}
        for key, item in value.items():
            key_lower = key.lower()
            if any(term in key_lower for term in secret_terms):
                output[key] = "<REDACTED>"
            else:
                output[key] = redact_for_export(item)
        return output

    if isinstance(value, list):
        return [redact_for_export(item) for item in value]

    return value


missing_fields = find_fill_me(PROJECT)

print("=" * 80)
print("AGENT RUNTIME INTAKE")
print("=" * 80)

if missing_fields:
    print(f"\nFields still containing FILL_ME: {len(missing_fields)}\n")
    for field in missing_fields:
        print(f"- {field}")
else:
    print("\nNo FILL_ME fields remain.")

print("\nAssumptions:")
for key, item in PROJECT["assumptions"].items():
    print(f"{key}: {item['correct']} — {item['assumption']}")

print("\nWorking components:")
for section_name in [
    "old_python_acp",
    "ray",
    "forest_onnx",
    "duckdb_lance",
    "ast_context",
    "monty",
]:
    section = PROJECT[section_name]
    print(f"- {section_name}: {json.dumps(section, default=str)[:300]}...")

print("\nExportable intake JSON:")
print(json.dumps(redact_for_export(PROJECT), indent=2, default=str))