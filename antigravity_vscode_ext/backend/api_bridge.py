import os
import sys
import uvicorn
import logging
import json # Explicitly import json
import ray
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Tuple
from starlette.middleware.cors import CORSMiddleware # For VS Code extension development

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


# Backend files are now consolidated in the same directory!

try:
    # Import the modified dynamic_segment_master that returns output path
    from dynamic_segment_master import dynamic_segment_master 
    # Import LangGraph agent and Pydantic models from its definition
    from legion_langgraph_brain import LegionLangGraphAgent, AgentState, MasterTrackStructuralProfile, MasteringToolOutput
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage # Import specific message types for AgentState handling
except ImportError as e:
    logging.error(f"Failed to import core modules: {e}")
    logging.error("Please ensure dynamic_segment_master.py and legion_langgraph_brain.py are in the same directory.")
    sys.exit(1) # Critical startup error

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("api_bridge")

app = FastAPI(
    title="Legion Sonic Engine API Bridge",
    description="API for the Antigravity Swarm Legion Sonic Engine, bridging VS Code UI to LangGraph AI and DSP.",
    version="0.1.0",
)

# --- CORS Middleware for VS Code Extension ---
# Allows the VS Code extension (running in a different origin/port) to communicate with this API
origins = [
    "vscode-webview://*", # Allow VS Code webview
    "http://localhost", # For local dev if needed
    "http://localhost:3000", # Example for web client
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For broad compatibility during development, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models for API Requests/Responses (mirroring common_types.ts) ---
class AnalyzeAudioRequest(BaseModel):
    file_path: str = Field(..., description="Absolute path to the audio file to analyze.")

class MasterAudioRequest(BaseModel):
    input_file_path: str = Field(..., description="Absolute path to the input audio file for mastering.")
    output_file_path: Optional[str] = Field(None, description="Optional: Absolute path for the mastered output file. If not provided, a default will be used.")
    # Future: detailed mastering parameters could go here.
    # mastering_config: Optional[Dict[str, Any]] = Field(None, description="Optional mastering configuration parameters.")

class ChatRequest(BaseModel):
    message: str = Field(..., description="The conversational message to send to the agent.")

class AgentStatus(BaseModel):
    status: str = Field(..., description="Current status of the Legion backend (e.g., 'initializing', 'ready', 'processing', 'error').")
    message: Optional[str] = Field(None, description="Detailed status message.")
    detail: Optional[Any] = Field(None, description="Optional: More verbose details or current operation data.")

class ProcessResult(BaseModel):
    success: bool = Field(..., description="True if the operation was successful, False otherwise.")
    message: str = Field(..., description="A human-readable message about the operation's outcome.")
    data: Optional[Any] = Field(None, description="Optional: The data returned by the operation (e.g., analysis report, output file path).")

# --- Global State for the LangGraph Agent and API Status ---
agent_instance: Optional[LegionLangGraphAgent] = None
current_status: AgentStatus = AgentStatus(status="initializing", message="Legion backend is starting up...")

@app.on_event("startup")
async def startup_event():
    """Initializes the LangGraph agent when the FastAPI app starts."""
    global agent_instance, current_status
    logger.info("Attempting to initialize Legion LangGraph Agent...")
    current_status = AgentStatus(status="initializing", message="Legion backend is starting up and initializing agent.")
    try:
        llm_provider = os.getenv("LLM_PROVIDER", "nvidia")
        agent_instance = LegionLangGraphAgent(provider=llm_provider)
        
        # Initialize Ray in the legion namespace and start the Serve deployment
        import ray
        if not ray.is_initialized():
            try:
                ray.init(address="auto", namespace="legion", object_store_memory=1500 * 1024 * 1024)
            except Exception as e:
                logger.error(f"Failed to connect to Ray cluster: {e}. Running without Ray backend.")
            
        try:
            if ray.is_initialized():
                from legion_status_service import start_legion_status_service
                logger.info("Starting Legion Status Ray Serve deployment...")
                start_legion_status_service()
            else:
                logger.warning("Skipping Ray Serve deployment because Ray is not initialized.")
        except Exception as serve_err:
            logger.error(f"Failed to start Ray Serve deployment: {serve_err}")
            
        current_status = AgentStatus(status="ready", message="Legion backend is ready and Ray Serve is running.")
        logger.info("Legion LangGraph Agent initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Legion LangGraph Agent: {e}", exc_info=True)
        current_status = AgentStatus(status="error", message=f"Failed to initialize LangGraph agent: {str(e)}", detail=str(e))
        # sys.exit(1) # Do not exit if FastAPI should still run for /ping, etc. but with error status

@app.get("/ping", response_model=Dict[str, str])
async def ping():
    """Checks if the API is running and returns 'pong'."""
    logger.debug("Ping received.")
    return {"status": "pong"}

@app.get("/status", response_model=AgentStatus)
async def get_status():
    """Returns the current operational status of the Legion backend."""
    return current_status

@app.get("/ray_status")
async def ray_status():
    """Returns real Ray cluster status instead of faking it."""
    try:
        import ray
        if ray.is_initialized():
            ctx = ray.get_runtime_context()
            nodes = ray.nodes()
            return {
                "connected": True,
                "namespace": ctx.namespace,
                "node_count": len([n for n in nodes if n.get("Alive")]),
                "total_nodes": len(nodes),
            }
        else:
            return {"connected": False, "message": "Ray is not initialized."}
    except Exception as e:
        return {"connected": False, "message": str(e)}

@app.post("/analyze_audio", response_model=ProcessResult)
async def analyze_audio_endpoint(request: AnalyzeAudioRequest):
    """
    Triggers the LangGraph agent to analyze an audio file's structure.
    """
    global current_status
    if current_status.status == "processing":
        raise HTTPException(status_code=429, detail="Legion is currently busy. Please wait for the current operation to complete.")
    
    logger.info(f"Received analysis request for: {request.file_path}")
    current_status = AgentStatus(status="processing", message=f"Analyzing audio file: {request.file_path}")

    if not agent_instance or current_status.status == "error":
        detail_msg = current_status.message if current_status.status == "error" else "Legion agent not initialized."
        current_status = AgentStatus(status="error", message=detail_msg)
        raise HTTPException(status_code=500, detail=detail_msg)

    if not os.path.exists(request.file_path):
        current_status = AgentStatus(status="ready", message="Analysis failed: File not found.")
        raise HTTPException(status_code=404, detail=f"Audio file not found at: {request.file_path}")

    try:
        # LangGraph agent is designed to handle the conversation and tool calls.
        initial_message_content = f"Please analyze the structural sections and key characteristics of the audio file located at '{request.file_path}'. Provide the full analysis report."
        initial_messages = [HumanMessage(content=initial_message_content)] # Start with a HumanMessage

        # Invoke the LangGraph agent
        final_state: AgentState = await agent_instance.ainvoke({"messages": initial_messages})

        analysis_output = None
        # Attempt to extract structured analysis from the final state's messages
        for message in reversed(final_state["messages"]):
            if isinstance(message, ToolMessage) and message.content:
                try:
                    content_dict = json.loads(message.content)
                    # Check if the content matches our MasterTrackStructuralProfile schema
                    if "total_sections_found" in content_dict and "segment_data" in content_dict:
                        # Validate against the Pydantic model
                        MasterTrackStructuralProfile.model_validate(content_dict)
                        analysis_output = content_dict
                        break
                except (json.JSONDecodeError, ValueError) as e:
                    logger.debug(f"Could not parse or validate tool message content as analysis profile: {e}")
            elif isinstance(message, AIMessage) and message.content:
                # Agent might summarize the tool output directly in its AIMessage
                try:
                    parsed_content = json.loads(message.content)
                    if "total_sections_found" in parsed_content: # Heuristic check
                        MasterTrackStructuralProfile.model_validate(parsed_content) # Validate
                        analysis_output = parsed_content
                        break
                except (json.JSONDecodeError, ValueError):
                    pass


        if analysis_output:
            current_status = AgentStatus(status="ready", message="Audio analysis completed successfully.")
            return ProcessResult(success=True, message="Audio analysis completed.", data=analysis_output)
        else:
            final_agent_response = final_state["messages"][-1].content if final_state["messages"] and isinstance(final_state["messages"][-1], BaseMessage) else "No specific output from agent."
            logger.warning(f"LangGraph analysis did not produce structured output. Final agent response: {final_agent_response}")
            current_status = AgentStatus(status="error", message="Audio analysis failed or produced unstructured output.")
            return ProcessResult(
                success=False,
                message=f"Legion agent could not produce a structured analysis report. Agent's final response: '{final_agent_response}'",
                data={"agent_response": final_agent_response}
            )

    except Exception as e:
        logger.error(f"Error during audio analysis: {e}", exc_info=True)
        current_status = AgentStatus(status="error", message=f"Error during audio analysis: {str(e)}", detail=str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error during analysis: {str(e)}")
    finally:
        if current_status.status == "processing": # Ensure status is reset if not explicitly set
            current_status = AgentStatus(status="ready", message="Operation finished.")


@app.post("/master_audio", response_model=ProcessResult)
async def master_audio_endpoint(request: MasterAudioRequest):
    """
    Triggers the dynamic segment mastering process for an audio file.
    """
    global current_status
    if current_status.status == "processing":
        raise HTTPException(status_code=429, detail="Legion is currently busy. Please wait for the current operation to complete.")

    logger.info(f"Received mastering request for: {request.input_file_path}")
    current_status = AgentStatus(status="processing", message=f"Mastering audio file: {request.input_file_path}")

    if not agent_instance or current_status.status == "error":
        detail_msg = current_status.message if current_status.status == "error" else "Legion agent not initialized."
        current_status = AgentStatus(status="error", message=detail_msg)
        raise HTTPException(status_code=500, detail=detail_msg)
    
    if not os.path.exists(request.input_file_path):
        current_status = AgentStatus(status="ready", message="Mastering failed: Input file not found.")
        raise HTTPException(status_code=404, detail=f"Input audio file not found at: {request.input_file_path}")

    try:
        # Determine output path, if not provided by user
        output_file_path = request.output_file_path
        if not output_file_path:
            base_name = os.path.splitext(os.path.basename(request.input_file_path))[0]
            output_dir = os.path.dirname(request.input_file_path)
            output_file_path = os.path.join(output_dir, f"{base_name}_MASTERED.wav")
            
        initial_message_content = f"Master the audio file at '{request.input_file_path}' and save the output to '{output_file_path}'. Use the dynamic segment mastering pipeline."
        initial_messages = [HumanMessage(content=initial_message_content)]
        
        final_state: AgentState = await agent_instance.ainvoke({"messages": initial_messages})

        mastering_output_data = {"input_file": request.input_file_path, "output_file": output_file_path}
        
        # Check agent's final message or tool outputs for confirmation of mastering success
        success_message_found = False
        for message in reversed(final_state["messages"]):
            if isinstance(message, ToolMessage) and message.content:
                try:
                    content_dict = json.loads(message.content)
                    if "success" in content_dict and content_dict["success"] is True:
                        MasteringToolOutput.model_validate(content_dict) # Validate against schema
                        mastering_output_data.update(content_dict)
                        success_message_found = True
                        break
                except (json.JSONDecodeError, ValueError) as e:
                    logger.debug(f"Could not parse or validate tool message content as mastering output: {e}")
            elif isinstance(message, AIMessage) and message.content:
                if "Mastered file successfully saved" in message.content or "Master Completed" in message.content: # Heuristic check
                    success_message_found = True
                    break
        
        if success_message_found:
            current_status = AgentStatus(status="ready", message="Audio mastering completed successfully.")
            return ProcessResult(
                success=True, 
                message=f"Audio mastering completed. Output saved to: {output_file_path}", 
                data=mastering_output_data
            )
        else:
            final_agent_response = final_state["messages"][-1].content if final_state["messages"] and isinstance(final_state["messages"][-1], BaseMessage) else "No specific output from agent."
            logger.warning(f"LangGraph mastering did not produce clear success. Final agent response: {final_agent_response}")
            current_status = AgentStatus(status="error", message="Audio mastering failed or agent could not confirm success.")
            return ProcessResult(
                success=False,
                message=f"Legion agent could not confirm successful mastering. Agent's final response: '{final_agent_response}'",
                data={"agent_response": final_agent_response}
            )

    except Exception as e:
        logger.error(f"Error during audio mastering: {e}", exc_info=True)
        current_status = AgentStatus(status="error", message=f"Error during audio mastering: {str(e)}", detail=str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error during mastering: {str(e)}")
    finally:
        if current_status.status == "processing": # Ensure status is reset if not explicitly set
            current_status = AgentStatus(status="ready", message="Operation finished.")

@app.post("/chat", response_model=ProcessResult)
async def chat_endpoint(request: ChatRequest):
    """
    Passes a conversational message through the LLM Router.
    Default: NVIDIA API (meta/llama-3.1-70b-instruct via OpenClaw-compatible endpoint).
    Optional: Add ?provider=gemini or ?provider=lmstudio to use alternative backends.
    
    DSP tools are available for the LLM to call (analyze_audio, apply_mastering).
    """
    from llm_router import create_router, LLMRouter

    global current_status
    if current_status.status == "processing":
        raise HTTPException(status_code=429, detail="Legion is currently busy. Please wait for the current operation to complete.")
    
    logger.info(f"Received chat message: {request.message}")
    current_status = AgentStatus(status="processing", message="Processing chat via LLM Router...")

    try:
        # Get provider from request or default to nvidia
        provider = getattr(request, 'provider', None) or os.getenv("LLM_PROVIDER", "nvidia")
        router = create_router(provider)

        # Build system prompt with loaded context (NOT re-uploaded every call)
        system_prompt = _build_system_prompt()

        # Define DSP tools in OpenAI-compatible format (works with NVIDIA and converts for Gemini)
        tools = [
            LLMRouter.build_tool_schema(
                name="analyze_audio_structure",
                description="Dynamically computes authentic transient/beat section boundaries and profiles them for an audio file. Returns structured JSON with sections, RMS, crest factor, spectral data.",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Absolute path to the audio file to analyze."}
                    },
                    "required": ["file_path"],
                },
            ),
            LLMRouter.build_tool_schema(
                name="apply_dynamic_mastering",
                description="Applies the dynamic segment mastering pipeline to an audio file using LanceDB baselines and Pedalboard for professional-grade processing.",
                parameters={
                    "type": "object",
                    "properties": {
                        "input_file_path": {"type": "string", "description": "Absolute path to the input audio file for mastering."},
                        "output_file_path": {"type": "string", "description": "Optional output path. Defaults to input_MASTERED.wav."},
                    },
                    "required": ["input_file_path"],
                },
            ),
        ]

        # Send chat request through the router
        messages = [{"role": "user", "content": request.message}]
        response = await router.chat(messages=messages, tools=tools, system_prompt=system_prompt)

        # Handle tool calls if the LLM decided to use one
        if response.get("tool_calls"):
            tool_results = []
            for tc in response["tool_calls"]:
                func_name = tc["name"]
                args = tc["arguments"]
                logger.info(f"LLM requested tool call: {func_name}({args})")

                try:
                    if func_name == "analyze_audio_structure":
                        result = await analyze_audio_structure_tool.ainvoke({"file_path": args["file_path"]})
                        tool_result = result.model_dump() if hasattr(result, 'model_dump') else result
                    elif func_name == "apply_dynamic_mastering":
                        invoke_args = {"input_file_path": args["input_file_path"]}
                        if "output_file_path" in args:
                            invoke_args["output_file_path"] = args["output_file_path"]
                        result = await apply_dynamic_mastering_tool.ainvoke(invoke_args)
                        tool_result = result.model_dump() if hasattr(result, 'model_dump') else result
                    else:
                        tool_result = {"error": f"Unknown tool: {func_name}"}
                    
                    tool_results.append({"tool": func_name, "result": tool_result})
                except Exception as tool_err:
                    tool_results.append({"tool": func_name, "error": str(tool_err)})

            # Send tool results back for a final response
            followup_messages = messages + [
                {"role": "assistant", "content": json.dumps(response.get("tool_calls", []))},
                {"role": "user", "content": f"Tool results: {json.dumps(tool_results)}. Please summarize the results."},
            ]
            final_response = await router.chat(messages=followup_messages, system_prompt=system_prompt)
            final_text = final_response.get("content", "Tool executed but no summary generated.")
        else:
            final_text = response.get("content", "No response generated.")

        # Save output (same pattern as ask_antigravity_codegen.py)
        base_out_file = r"C:\WEB CASE STUDY\antigravity_codegen_output.md"
        out_file = base_out_file
        if os.path.exists(out_file):
            base, ext = os.path.splitext(base_out_file)
            i = 1
            while os.path.exists(f"{base}_{i}{ext}"):
                i += 1
            out_file = f"{base}_{i}{ext}"
            
        with open(out_file, "w", encoding="utf-8") as out:
            out.write(final_text)
        
        logger.info(f"Saved output to {out_file} via {response.get('provider', 'unknown')} / {response.get('model', 'unknown')}")
        
        current_status = AgentStatus(status="ready", message=f"Chat response generated via {response.get('provider', 'unknown')}.")
        return ProcessResult(success=True, message=final_text)

    except Exception as e:
        logger.error(f"Error during chat: {e}", exc_info=True)
        current_status = AgentStatus(status="error", message=f"Error during chat: {str(e)}", detail=str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error during chat: {str(e)}")
    finally:
        if current_status.status == "processing":
            current_status = AgentStatus(status="ready", message="Operation finished.")


# ---------------------------------------------------------------------------
# System prompt builder — loads context files ONCE, not per-call uploads
# ---------------------------------------------------------------------------
_cached_system_prompt: Optional[str] = None

def _build_system_prompt() -> str:
    """
    Builds a system prompt from local context files.
    Cached after first call so we don't re-read every message.
    """
    global _cached_system_prompt
    if _cached_system_prompt is not None:
        return _cached_system_prompt

    parts = [
        "You are the Legion Sonic Engine, an AI assistant specialized in audio analysis, "
        "mastering, and music production. You have access to DSP tools for analyzing and "
        "mastering audio files. You are part of the Antigravity Swarm — a distributed AI "
        "system running on Ray with Pydantic-validated data flowing between actors.",
        "",
        "Key capabilities:",
        "- analyze_audio_structure: Compute section boundaries, RMS, crest factor, spectral data",
        "- apply_dynamic_mastering: Master audio with LanceDB baselines + Pedalboard DSP",
        "",
    ]

    # Load context files if they exist (lightweight — just the key ones)
    context_files = [
        (r"C:\WEB CASE STUDY\LEGION_MANIFEST.md", "LEGION MANIFEST"),
        (r"C:\WEB CASE STUDY\current_session_chat.md", "CURRENT SESSION"),
    ]

    for fpath, label in context_files:
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                # Truncate to avoid blowing up context windows
                if len(content) > 8000:
                    content = content[:8000] + "\n... [truncated]"
                parts.append(f"\n--- {label} ---\n{content}")
            except Exception as e:
                logger.warning(f"Could not load context file {fpath}: {e}")

    _cached_system_prompt = "\n".join(parts)
    return _cached_system_prompt

if __name__ == "__main__":
    # For local development: run with `python api_bridge.py`
    # Ensure you have `uvicorn` installed: `pip install uvicorn`
    # Default port is 8000
    logger.info("Starting Legion Sonic Engine API Bridge...")
    # To run with auto-reload for development: uvicorn api_bridge:app --reload --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)


@app.post("/analyze_audio", response_model=ProcessResult)
async def analyze_audio_endpoint(request: AnalyzeAudioRequest):
    """
    Triggers the LangGraph agent to analyze an audio file's structure.
    """
    global current_status
    if current_status.status == "processing":
        raise HTTPException(status_code=429, detail="Legion is currently busy. Please wait for the current operation to complete.")
    
    logger.info(f"Received analysis request for: {request.file_path}")
    current_status = AgentStatus(status="processing", message=f"Analyzing audio file: {request.file_path}")

    if not agent_instance or current_status.status == "error":
        detail_msg = current_status.message if current_status.status == "error" else "Legion agent not initialized."
        current_status = AgentStatus(status="error", message=detail_msg)
        raise HTTPException(status_code=500, detail=detail_msg)

    if not os.path.exists(request.file_path):
        current_status = AgentStatus(status="ready", message="Analysis failed: File not found.")
        raise HTTPException(status_code=404, detail=f"Audio file not found at: {request.file_path}")

    try:
        # LangGraph agent is designed to handle the conversation and tool calls.
        initial_message_content = f"Please analyze the structural sections and key characteristics of the audio file located at '{request.file_path}'. Provide the full analysis report."
        initial_messages = [HumanMessage(content=initial_message_content)] # Start with a HumanMessage

        # Invoke the LangGraph agent
        final_state: AgentState = await agent_instance.ainvoke({"messages": initial_messages})

        analysis_output = None
        # Attempt to extract structured analysis from the final state's messages
        for message in reversed(final_state["messages"]):
            if isinstance(message, ToolMessage) and message.content:
                try:
                    content_dict = json.loads(message.content)
                    # Check if the content matches our MasterTrackStructuralProfile schema
                    if "total_sections_found" in content_dict and "segment_data" in content_dict:
                        # Validate against the Pydantic model
                        MasterTrackStructuralProfile.model_validate(content_dict)
                        analysis_output = content_dict
                        break
                except (json.JSONDecodeError, ValueError) as e:
                    logger.debug(f"Could not parse or validate tool message content as analysis profile: {e}")
            elif isinstance(message, AIMessage) and message.content:
                # Agent might summarize the tool output directly in its AIMessage
                try:
                    parsed_content = json.loads(message.content)
                    if "total_sections_found" in parsed_content: # Heuristic check
                        MasterTrackStructuralProfile.model_validate(parsed_content) # Validate
                        analysis_output = parsed_content
                        break
                except (json.JSONDecodeError, ValueError):
                    pass


        if analysis_output:
            current_status = AgentStatus(status="ready", message="Audio analysis completed successfully.")
            return ProcessResult(success=True, message="Audio analysis completed.", data=analysis_output)
        else:
            final_agent_response = final_state["messages"][-1].content if final_state["messages"] and isinstance(final_state["messages"][-1], BaseMessage) else "No specific output from agent."
            logger.warning(f"LangGraph analysis did not produce structured output. Final agent response: {final_agent_response}")
            current_status = AgentStatus(status="error", message="Audio analysis failed or produced unstructured output.")
            return ProcessResult(
                success=False,
                message=f"Legion agent could not produce a structured analysis report. Agent's final response: '{final_agent_response}'",
                data={"agent_response": final_agent_response}
            )

    except Exception as e:
        logger.error(f"Error during audio analysis: {e}", exc_info=True)
        current_status = AgentStatus(status="error", message=f"Error during audio analysis: {str(e)}", detail=str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error during analysis: {str(e)}")
    finally:
        if current_status.status == "processing": # Ensure status is reset if not explicitly set
            current_status = AgentStatus(status="ready", message="Operation finished.")


@app.post("/master_audio", response_model=ProcessResult)
async def master_audio_endpoint(request: MasterAudioRequest):
    """
    Triggers the dynamic segment mastering process for an audio file.
    """
    global current_status
    if current_status.status == "processing":
        raise HTTPException(status_code=429, detail="Legion is currently busy. Please wait for the current operation to complete.")

    logger.info(f"Received mastering request for: {request.input_file_path}")
    current_status = AgentStatus(status="processing", message=f"Mastering audio file: {request.input_file_path}")

    if not agent_instance or current_status.status == "error":
        detail_msg = current_status.message if current_status.status == "error" else "Legion agent not initialized."
        current_status = AgentStatus(status="error", message=detail_msg)
        raise HTTPException(status_code=500, detail=detail_msg)
    
    if not os.path.exists(request.input_file_path):
        current_status = AgentStatus(status="ready", message="Mastering failed: Input file not found.")
        raise HTTPException(status_code=404, detail=f"Input audio file not found at: {request.input_file_path}")

    try:
        # Determine output path, if not provided by user
        output_file_path = request.output_file_path
        if not output_file_path:
            base_name = os.path.splitext(os.path.basename(request.input_file_path))[0]
            output_dir = os.path.dirname(request.input_file_path)
            output_file_path = os.path.join(output_dir, f"{base_name}_MASTERED.wav")
            
        initial_message_content = f"Master the audio file at '{request.input_file_path}' and save the output to '{output_file_path}'. Use the dynamic segment mastering pipeline."
        initial_messages = [HumanMessage(content=initial_message_content)]
        
        final_state: AgentState = await agent_instance.ainvoke({"messages": initial_messages})

        mastering_output_data = {"input_file": request.input_file_path, "output_file": output_file_path}
        
        # Check agent's final message or tool outputs for confirmation of mastering success
        success_message_found = False
        for message in reversed(final_state["messages"]):
            if isinstance(message, ToolMessage) and message.content:
                try:
                    content_dict = json.loads(message.content)
                    if "success" in content_dict and content_dict["success"] is True:
                        MasteringToolOutput.model_validate(content_dict) # Validate against schema
                        mastering_output_data.update(content_dict)
                        success_message_found = True
                        break
                except (json.JSONDecodeError, ValueError) as e:
                    logger.debug(f"Could not parse or validate tool message content as mastering output: {e}")
            elif isinstance(message, AIMessage) and message.content:
                if "Mastered file successfully saved" in message.content or "Master Completed" in message.content: # Heuristic check
                    success_message_found = True
                    break
        
        if success_message_found:
            current_status = AgentStatus(status="ready", message="Audio mastering completed successfully.")
            return ProcessResult(
                success=True, 
                message=f"Audio mastering completed. Output saved to: {output_file_path}", 
                data=mastering_output_data
            )
        else:
            final_agent_response = final_state["messages"][-1].content if final_state["messages"] and isinstance(final_state["messages"][-1], BaseMessage) else "No specific output from agent."
            logger.warning(f"LangGraph mastering did not produce clear success. Final agent response: {final_agent_response}")
            current_status = AgentStatus(status="error", message="Audio mastering failed or agent could not confirm success.")
            return ProcessResult(
                success=False,
                message=f"Legion agent could not confirm successful mastering. Agent's final response: '{final_agent_response}'",
                data={"agent_response": final_agent_response}
            )

    except Exception as e:
        logger.error(f"Error during audio mastering: {e}", exc_info=True)
        current_status = AgentStatus(status="error", message=f"Error during audio mastering: {str(e)}", detail=str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error during mastering: {str(e)}")
    finally:
        if current_status.status == "processing": # Ensure status is reset if not explicitly set
            current_status = AgentStatus(status="ready", message="Operation finished.")

@app.post("/chat", response_model=ProcessResult)
async def chat_endpoint(request: ChatRequest):
    """
    Passes a conversational message through the LLM Router.
    Default: NVIDIA API (meta/llama-3.1-70b-instruct via OpenClaw-compatible endpoint).
    Optional: Add ?provider=gemini or ?provider=lmstudio to use alternative backends.
    
    DSP tools are available for the LLM to call (analyze_audio, apply_mastering).
    """
    from llm_router import create_router, LLMRouter

    global current_status
    if current_status.status == "processing":
        raise HTTPException(status_code=429, detail="Legion is currently busy. Please wait for the current operation to complete.")
    
    logger.info(f"Received chat message: {request.message}")
    current_status = AgentStatus(status="processing", message="Processing chat via LLM Router...")

    try:
        # Get provider from request or default to nvidia
        provider = getattr(request, 'provider', None) or os.getenv("LLM_PROVIDER", "nvidia")
        router = create_router(provider)

        # Build system prompt with loaded context (NOT re-uploaded every call)
        system_prompt = _build_system_prompt()

        # Define DSP tools in OpenAI-compatible format (works with NVIDIA and converts for Gemini)
        tools = [
            LLMRouter.build_tool_schema(
                name="analyze_audio_structure",
                description="Dynamically computes authentic transient/beat section boundaries and profiles them for an audio file. Returns structured JSON with sections, RMS, crest factor, spectral data.",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Absolute path to the audio file to analyze."}
                    },
                    "required": ["file_path"],
                },
            ),
            LLMRouter.build_tool_schema(
                name="apply_dynamic_mastering",
                description="Applies the dynamic segment mastering pipeline to an audio file using LanceDB baselines and Pedalboard for professional-grade processing.",
                parameters={
                    "type": "object",
                    "properties": {
                        "input_file_path": {"type": "string", "description": "Absolute path to the input audio file for mastering."},
                        "output_file_path": {"type": "string", "description": "Optional output path. Defaults to input_MASTERED.wav."},
                    },
                    "required": ["input_file_path"],
                },
            ),
        ]

        # Send chat request through the router
        messages = [{"role": "user", "content": request.message}]
        response = await router.chat(messages=messages, tools=tools, system_prompt=system_prompt)

        # Handle tool calls if the LLM decided to use one
        if response.get("tool_calls"):
            tool_results = []
            for tc in response["tool_calls"]:
                func_name = tc["name"]
                args = tc["arguments"]
                logger.info(f"LLM requested tool call: {func_name}({args})")

                try:
                    if func_name == "analyze_audio_structure":
                        result = await analyze_audio_structure_tool.ainvoke({"file_path": args["file_path"]})
                        tool_result = result.model_dump() if hasattr(result, 'model_dump') else result
                    elif func_name == "apply_dynamic_mastering":
                        invoke_args = {"input_file_path": args["input_file_path"]}
                        if "output_file_path" in args:
                            invoke_args["output_file_path"] = args["output_file_path"]
                        result = await apply_dynamic_mastering_tool.ainvoke(invoke_args)
                        tool_result = result.model_dump() if hasattr(result, 'model_dump') else result
                    else:
                        tool_result = {"error": f"Unknown tool: {func_name}"}
                    
                    tool_results.append({"tool": func_name, "result": tool_result})
                except Exception as tool_err:
                    tool_results.append({"tool": func_name, "error": str(tool_err)})

            # Send tool results back for a final response
            followup_messages = messages + [
                {"role": "assistant", "content": json.dumps(response.get("tool_calls", []))},
                {"role": "user", "content": f"Tool results: {json.dumps(tool_results)}. Please summarize the results."},
            ]
            final_response = await router.chat(messages=followup_messages, system_prompt=system_prompt)
            final_text = final_response.get("content", "Tool executed but no summary generated.")
        else:
            final_text = response.get("content", "No response generated.")

        # Save output (same pattern as ask_antigravity_codegen.py)
        base_out_file = r"C:\WEB CASE STUDY\antigravity_codegen_output.md"
        out_file = base_out_file
        if os.path.exists(out_file):
            base, ext = os.path.splitext(base_out_file)
            i = 1
            while os.path.exists(f"{base}_{i}{ext}"):
                i += 1
            out_file = f"{base}_{i}{ext}"
            
        with open(out_file, "w", encoding="utf-8") as out:
            out.write(final_text)
        
        logger.info(f"Saved output to {out_file} via {response.get('provider', 'unknown')} / {response.get('model', 'unknown')}")
        
        current_status = AgentStatus(status="ready", message=f"Chat response generated via {response.get('provider', 'unknown')}.")
        return ProcessResult(success=True, message=final_text)

    except Exception as e:
        logger.error(f"Error during chat: {e}", exc_info=True)
        current_status = AgentStatus(status="error", message=f"Error during chat: {str(e)}", detail=str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error during chat: {str(e)}")
    finally:
        if current_status.status == "processing":
            current_status = AgentStatus(status="ready", message="Operation finished.")


# ---------------------------------------------------------------------------
# System prompt builder — loads context files ONCE, not per-call uploads
# ---------------------------------------------------------------------------
_cached_system_prompt: Optional[str] = None

def _build_system_prompt() -> str:
    """
    Builds a system prompt from local context files.
    Cached after first call so we don't re-read every message.
    """
    global _cached_system_prompt
    if _cached_system_prompt is not None:
        return _cached_system_prompt

    parts = [
        "You are the Legion Sonic Engine, an AI assistant specialized in audio analysis, "
        "mastering, and music production. You have access to DSP tools for analyzing and "
        "mastering audio files. You are part of the Antigravity Swarm — a distributed AI "
        "system running on Ray with Pydantic-validated data flowing between actors.",
        "",
        "Key capabilities:",
        "- analyze_audio_structure: Compute section boundaries, RMS, crest factor, spectral data",
        "- apply_dynamic_mastering: Master audio with LanceDB baselines + Pedalboard DSP",
        "",
    ]

    # Load context files if they exist (lightweight — just the key ones)
    context_files = [
        (r"C:\WEB CASE STUDY\LEGION_MANIFEST.md", "LEGION MANIFEST"),
        (r"C:\WEB CASE STUDY\current_session_chat.md", "CURRENT SESSION"),
    ]

    for fpath, label in context_files:
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                # Truncate to avoid blowing up context windows
                if len(content) > 8000:
                    content = content[:8000] + "\n... [truncated]"
                parts.append(f"\n--- {label} ---\n{content}")
            except Exception as e:
                logger.warning(f"Could not load context file {fpath}: {e}")

    _cached_system_prompt = "\n".join(parts)
    return _cached_system_prompt

if __name__ == "__main__":
    # For local development: run with `python api_bridge.py`
    # Ensure you have `uvicorn` installed: `pip install uvicorn`
    # Default port is 8000
    logger.info("Starting Legion Sonic Engine API Bridge...")
    # To run with auto-reload for development: uvicorn api_bridge:app --reload --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)


@app.post("/analyze_audio", response_model=ProcessResult)
async def analyze_audio_endpoint(request: AnalyzeAudioRequest):
    """
    Triggers the LangGraph agent to analyze an audio file's structure.
    """
    global current_status
    if current_status.status == "processing":
        raise HTTPException(status_code=429, detail="Legion is currently busy. Please wait for the current operation to complete.")
    
    logger.info(f"Received analysis request for: {request.file_path}")
    current_status = AgentStatus(status="processing", message=f"Analyzing audio file: {request.file_path}")

    if not agent_instance or current_status.status == "error":
        detail_msg = current_status.message if current_status.status == "error" else "Legion agent not initialized."
        current_status = AgentStatus(status="error", message=detail_msg)
        raise HTTPException(status_code=500, detail=detail_msg)

    if not os.path.exists(request.file_path):
        current_status = AgentStatus(status="ready", message="Analysis failed: File not found.")
        raise HTTPException(status_code=404, detail=f"Audio file not found at: {request.file_path}")

    try:
        # LangGraph agent is designed to handle the conversation and tool calls.
        initial_message_content = f"Please analyze the structural sections and key characteristics of the audio file located at '{request.file_path}'. Provide the full analysis report."
        initial_messages = [HumanMessage(content=initial_message_content)] # Start with a HumanMessage

        # Invoke the LangGraph agent
        final_state: AgentState = await agent_instance.ainvoke({"messages": initial_messages})

        analysis_output = None
        # Attempt to extract structured analysis from the final state's messages
        for message in reversed(final_state["messages"]):
            if isinstance(message, ToolMessage) and message.content:
                try:
                    content_dict = json.loads(message.content)
                    # Check if the content matches our MasterTrackStructuralProfile schema
                    if "total_sections_found" in content_dict and "segment_data" in content_dict:
                        # Validate against the Pydantic model
                        MasterTrackStructuralProfile.model_validate(content_dict)
                        analysis_output = content_dict
                        break
                except (json.JSONDecodeError, ValueError) as e:
                    logger.debug(f"Could not parse or validate tool message content as analysis profile: {e}")
            elif isinstance(message, AIMessage) and message.content:
                # Agent might summarize the tool output directly in its AIMessage
                try:
                    parsed_content = json.loads(message.content)
                    if "total_sections_found" in parsed_content: # Heuristic check
                        MasterTrackStructuralProfile.model_validate(parsed_content) # Validate
                        analysis_output = parsed_content
                        break
                except (json.JSONDecodeError, ValueError):
                    pass


        if analysis_output:
            current_status = AgentStatus(status="ready", message="Audio analysis completed successfully.")
            return ProcessResult(success=True, message="Audio analysis completed.", data=analysis_output)
        else:
            final_agent_response = final_state["messages"][-1].content if final_state["messages"] and isinstance(final_state["messages"][-1], BaseMessage) else "No specific output from agent."
            logger.warning(f"LangGraph analysis did not produce structured output. Final agent response: {final_agent_response}")
            current_status = AgentStatus(status="error", message="Audio analysis failed or produced unstructured output.")
            return ProcessResult(
                success=False,
                message=f"Legion agent could not produce a structured analysis report. Agent's final response: '{final_agent_response}'",
                data={"agent_response": final_agent_response}
            )

    except Exception as e:
        logger.error(f"Error during audio analysis: {e}", exc_info=True)
        current_status = AgentStatus(status="error", message=f"Error during audio analysis: {str(e)}", detail=str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error during analysis: {str(e)}")
    finally:
        if current_status.status == "processing": # Ensure status is reset if not explicitly set
            current_status = AgentStatus(status="ready", message="Operation finished.")


@app.post("/master_audio", response_model=ProcessResult)
async def master_audio_endpoint(request: MasterAudioRequest):
    """
    Triggers the dynamic segment mastering process for an audio file.
    """
    global current_status
    if current_status.status == "processing":
        raise HTTPException(status_code=429, detail="Legion is currently busy. Please wait for the current operation to complete.")

    logger.info(f"Received mastering request for: {request.input_file_path}")
    current_status = AgentStatus(status="processing", message=f"Mastering audio file: {request.input_file_path}")

    if not agent_instance or current_status.status == "error":
        detail_msg = current_status.message if current_status.status == "error" else "Legion agent not initialized."
        current_status = AgentStatus(status="error", message=detail_msg)
        raise HTTPException(status_code=500, detail=detail_msg)
    
    if not os.path.exists(request.input_file_path):
        current_status = AgentStatus(status="ready", message="Mastering failed: Input file not found.")
        raise HTTPException(status_code=404, detail=f"Input audio file not found at: {request.input_file_path}")

    try:
        # Determine output path, if not provided by user
        output_file_path = request.output_file_path
        if not output_file_path:
            base_name = os.path.splitext(os.path.basename(request.input_file_path))[0]
            output_dir = os.path.dirname(request.input_file_path)
            output_file_path = os.path.join(output_dir, f"{base_name}_MASTERED.wav")
            
        initial_message_content = f"Master the audio file at '{request.input_file_path}' and save the output to '{output_file_path}'. Use the dynamic segment mastering pipeline."
        initial_messages = [HumanMessage(content=initial_message_content)]
        
        final_state: AgentState = await agent_instance.ainvoke({"messages": initial_messages})

        mastering_output_data = {"input_file": request.input_file_path, "output_file": output_file_path}
        
        # Check agent's final message or tool outputs for confirmation of mastering success
        success_message_found = False
        for message in reversed(final_state["messages"]):
            if isinstance(message, ToolMessage) and message.content:
                try:
                    content_dict = json.loads(message.content)
                    if "success" in content_dict and content_dict["success"] is True:
                        MasteringToolOutput.model_validate(content_dict) # Validate against schema
                        mastering_output_data.update(content_dict)
                        success_message_found = True
                        break
                except (json.JSONDecodeError, ValueError) as e:
                    logger.debug(f"Could not parse or validate tool message content as mastering output: {e}")
            elif isinstance(message, AIMessage) and message.content:
                if "Mastered file successfully saved" in message.content or "Master Completed" in message.content: # Heuristic check
                    success_message_found = True
                    break
        
        if success_message_found:
            current_status = AgentStatus(status="ready", message="Audio mastering completed successfully.")
            return ProcessResult(
                success=True, 
                message=f"Audio mastering completed. Output saved to: {output_file_path}", 
                data=mastering_output_data
            )
        else:
            final_agent_response = final_state["messages"][-1].content if final_state["messages"] and isinstance(final_state["messages"][-1], BaseMessage) else "No specific output from agent."
            logger.warning(f"LangGraph mastering did not produce clear success. Final agent response: {final_agent_response}")
            current_status = AgentStatus(status="error", message="Audio mastering failed or agent could not confirm success.")
            return ProcessResult(
                success=False,
                message=f"Legion agent could not confirm successful mastering. Agent's final response: '{final_agent_response}'",
                data={"agent_response": final_agent_response}
            )

    except Exception as e:
        logger.error(f"Error during audio mastering: {e}", exc_info=True)
        current_status = AgentStatus(status="error", message=f"Error during audio mastering: {str(e)}", detail=str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error during mastering: {str(e)}")
    finally:
        if current_status.status == "processing": # Ensure status is reset if not explicitly set
            current_status = AgentStatus(status="ready", message="Operation finished.")

@app.post("/chat", response_model=ProcessResult)
async def chat_endpoint(request: ChatRequest):
    """
    Passes a conversational message through the LLM Router.
    Default: NVIDIA API (meta/llama-3.1-70b-instruct via OpenClaw-compatible endpoint).
    Optional: Add ?provider=gemini or ?provider=lmstudio to use alternative backends.
    
    DSP tools are available for the LLM to call (analyze_audio, apply_mastering).
    """
    from llm_router import create_router, LLMRouter

    global current_status
    if current_status.status == "processing":
        raise HTTPException(status_code=429, detail="Legion is currently busy. Please wait for the current operation to complete.")
    
    logger.info(f"Received chat message: {request.message}")
    current_status = AgentStatus(status="processing", message="Processing chat via LLM Router...")

    try:
        # Get provider from request or default to nvidia
        provider = getattr(request, 'provider', None) or os.getenv("LLM_PROVIDER", "nvidia")
        router = create_router(provider)

        # Build system prompt with loaded context (NOT re-uploaded every call)
        system_prompt = _build_system_prompt()

        # Define DSP tools in OpenAI-compatible format (works with NVIDIA and converts for Gemini)
        tools = [
            LLMRouter.build_tool_schema(
                name="analyze_audio_structure",
                description="Dynamically computes authentic transient/beat section boundaries and profiles them for an audio file. Returns structured JSON with sections, RMS, crest factor, spectral data.",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Absolute path to the audio file to analyze."}
                    },
                    "required": ["file_path"],
                },
            ),
            LLMRouter.build_tool_schema(
                name="apply_dynamic_mastering",
                description="Applies the dynamic segment mastering pipeline to an audio file using LanceDB baselines and Pedalboard for professional-grade processing.",
                parameters={
                    "type": "object",
                    "properties": {
                        "input_file_path": {"type": "string", "description": "Absolute path to the input audio file for mastering."},
                        "output_file_path": {"type": "string", "description": "Optional output path. Defaults to input_MASTERED.wav."},
                    },
                    "required": ["input_file_path"],
                },
            ),
        ]

        # Send chat request through the router
        messages = [{"role": "user", "content": request.message}]
        response = await router.chat(messages=messages, tools=tools, system_prompt=system_prompt)

        # Handle tool calls if the LLM decided to use one
        if response.get("tool_calls"):
            tool_results = []
            for tc in response["tool_calls"]:
                func_name = tc["name"]
                args = tc["arguments"]
                logger.info(f"LLM requested tool call: {func_name}({args})")

                try:
                    if func_name == "analyze_audio_structure":
                        result = await analyze_audio_structure_tool.ainvoke({"file_path": args["file_path"]})
                        tool_result = result.model_dump() if hasattr(result, 'model_dump') else result
                    elif func_name == "apply_dynamic_mastering":
                        invoke_args = {"input_file_path": args["input_file_path"]}
                        if "output_file_path" in args:
                            invoke_args["output_file_path"] = args["output_file_path"]
                        result = await apply_dynamic_mastering_tool.ainvoke(invoke_args)
                        tool_result = result.model_dump() if hasattr(result, 'model_dump') else result
                    else:
                        tool_result = {"error": f"Unknown tool: {func_name}"}
                    
                    tool_results.append({"tool": func_name, "result": tool_result})
                except Exception as tool_err:
                    tool_results.append({"tool": func_name, "error": str(tool_err)})

            # Send tool results back for a final response
            followup_messages = messages + [
                {"role": "assistant", "content": json.dumps(response.get("tool_calls", []))},
                {"role": "user", "content": f"Tool results: {json.dumps(tool_results)}. Please summarize the results."},
            ]
            final_response = await router.chat(messages=followup_messages, system_prompt=system_prompt)
            final_text = final_response.get("content", "Tool executed but no summary generated.")
        else:
            final_text = response.get("content", "No response generated.")

        # Save output (same pattern as ask_antigravity_codegen.py)
        base_out_file = r"C:\WEB CASE STUDY\antigravity_codegen_output.md"
        out_file = base_out_file
        if os.path.exists(out_file):
            base, ext = os.path.splitext(base_out_file)
            i = 1
            while os.path.exists(f"{base}_{i}{ext}"):
                i += 1
            out_file = f"{base}_{i}{ext}"
            
        with open(out_file, "w", encoding="utf-8") as out:
            out.write(final_text)
        
        logger.info(f"Saved output to {out_file} via {response.get('provider', 'unknown')} / {response.get('model', 'unknown')}")
        
        current_status = AgentStatus(status="ready", message=f"Chat response generated via {response.get('provider', 'unknown')}.")
        return ProcessResult(success=True, message=final_text)

    except Exception as e:
        logger.error(f"Error during chat: {e}", exc_info=True)
        current_status = AgentStatus(status="error", message=f"Error during chat: {str(e)}", detail=str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error during chat: {str(e)}")
    finally:
        if current_status.status == "processing":
            current_status = AgentStatus(status="ready", message="Operation finished.")


# ---------------------------------------------------------------------------
# System prompt builder — loads context files ONCE, not per-call uploads
# ---------------------------------------------------------------------------
_cached_system_prompt: Optional[str] = None

def _build_system_prompt() -> str:
    """
    Builds a system prompt from local context files.
    Cached after first call so we don't re-read every message.
    """
    global _cached_system_prompt
    if _cached_system_prompt is not None:
        return _cached_system_prompt

    parts = [
        "You are the Legion Sonic Engine, an AI assistant specialized in audio analysis, "
        "mastering, and music production. You have access to DSP tools for analyzing and "
        "mastering audio files. You are part of the Antigravity Swarm — a distributed AI "
        "system running on Ray with Pydantic-validated data flowing between actors.",
        "",
        "Key capabilities:",
        "- analyze_audio_structure: Compute section boundaries, RMS, crest factor, spectral data",
        "- apply_dynamic_mastering: Master audio with LanceDB baselines + Pedalboard DSP",
        "",
    ]

    # Load context files if they exist (lightweight — just the key ones)
    context_files = [
        (r"C:\WEB CASE STUDY\LEGION_MANIFEST.md", "LEGION MANIFEST"),
        (r"C:\WEB CASE STUDY\current_session_chat.md", "CURRENT SESSION"),
    ]

    for fpath, label in context_files:
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                # Truncate to avoid blowing up context windows
                if len(content) > 8000:
                    content = content[:8000] + "\n... [truncated]"
                parts.append(f"\n--- {label} ---\n{content}")
            except Exception as e:
                logger.warning(f"Could not load context file {fpath}: {e}")

    _cached_system_prompt = "\n".join(parts)
    return _cached_system_prompt

if __name__ == "__main__":
    # For local development: run with `python api_bridge.py`
    # Ensure you have `uvicorn` installed: `pip install uvicorn`
    # Default port is 8000
    logger.info("Starting Legion Sonic Engine API Bridge...")
    # To run with auto-reload for development: uvicorn api_bridge:app --reload --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)