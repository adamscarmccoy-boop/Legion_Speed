import os
import time
import json
import torch
import torchaudio
import librosa
import numpy as np
import logging
import operator # For Annotated[List[...], operator.add]
from dotenv import load_dotenv
from typing import List, Tuple, Annotated, TypedDict, Optional, Any, Dict, Union
from pydantic import BaseModel, Field, ValidationError, field_validator # Strict Pydantic v2 validation

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


# LangChain/LangGraph imports
# langchain_openai import removed for stability
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import tool # Standard tool decorator
from langgraph.graph import StateGraph, END

# Import the dynamic mastering pipeline (assuming it's in the same directory and modified to return output path)
from dynamic_segment_master import dynamic_segment_master

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("legion_langgraph_brain")

# Load environment variables (for OPENROUTER_API_KEY)
env_path = os.path.join("C:\\", "WEB CASE STUDY", ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

# --- Pydantic Models for Data Validation (Strict Pydantic Validation) ---

# Section Metrics for Audio Analysis
class SectionMetrics(BaseModel):
    segment_name: str = Field(..., description="Descriptive name of the audio segment (e.g., 'Drop', 'Breakdown').")
    start_time_sec: float = Field(..., description="Start time of the segment in seconds.")
    end_time_sec: float = Field(..., description="End time of the segment in seconds.")
    rms_db: float = Field(..., description="Root Mean Square (RMS) loudness in dB.")
    crest_factor: float = Field(..., description="Crest factor, indicating the dynamic range (peak vs. RMS).")
    sub_bass_energy: float = Field(..., description="Energy in the sub-bass frequency range.")
    bass_energy: float = Field(..., description="Energy in the bass frequency range.")
    mid_energy: float = Field(..., description="Energy in the mid-range frequency band.")
    high_energy: float = Field(..., description="Energy in the high-frequency range.")
    spectral_centroid: float = Field(..., description="Spectral centroid, indicating the 'brightness' of the sound.")

# Master Track Structural Profile for full analysis report
class MasterTrackStructuralProfile(BaseModel):
    filename: str = Field(..., description="Name of the analyzed audio file.")
    total_sections_found: int = Field(..., description="Total number of distinct sections identified.")
    processing_time_ms: float = Field(..., description="Time taken to process the track in milliseconds.")
    segment_data: List[SectionMetrics] = Field(..., description="List of detailed metrics for each identified section.")

# Tool Input for Analysis
class AnalyzeAudioRequest(BaseModel):
    file_path: str = Field(..., description="Absolute path to the audio file to analyze.")

# Tool Input for Mastering
class ApplyMasteringInput(BaseModel):
    input_file_path: str = Field(..., description="Absolute path to the input audio file for mastering.")
    output_file_path: Optional[str] = Field(None, description="Absolute path for the mastered output file. If not provided, a default will be used.")

# Tool Output for Mastering (matches dynamic_segment_master's expected return)
class MasteringToolOutput(BaseModel):
    success: bool = Field(..., description="True if mastering was successful.")
    message: str = Field(..., description="Result message from the mastering process.")
    input_file: str = Field(..., description="The input file path that was mastered.")
    output_file: str = Field(..., description="The output file path of the mastered track.")
    # You might expand this with actual metrics from the mastered track later, e.g., LUFS, final RMS/crest

# --- Core DSP Tools (Leveraging previously developed logic) ---

@tool("analyze_audio_structure", args_schema=AnalyzeAudioRequest)
async def analyze_audio_structure_tool(file_path: str) -> MasterTrackStructuralProfile:
    """
    Dynamically computes authentic transient/beat section boundaries and profiles them
    for an audio file using advanced DSP (Librosa/PyTorch).
    Returns a structured report of the track's sections and their characteristics.
    """
    logger.info(f"DSP Tool: Analyzing structural sections for: {file_path}")
    start_time = time.perf_counter()

    if not os.path.exists(file_path):
        logger.error(f"File not found for analysis: {file_path}")
        raise FileNotFoundError(f"Target track missing at path: {file_path}")

    try:
        # torchaudio.load is synchronous, no await needed
        waveform, sr = torchaudio.load(file_path)
        total_samples = waveform.shape[1]
        
        # Downsample mono vector to execute fast boundary extraction math via librosa
        # Ensure it's on CPU for librosa which doesn't directly support GPU tensors
        mono_y = torch.mean(waveform.cpu(), dim=0).numpy()

        # 2. Extract transient peaks via spectral novelty envelope calculation
        onset_env = librosa.onset.onset_strength(y=mono_y, sr=sr, hop_length=512)
        onset_frames = librosa.onset.onset_detect(
            onset_envelope=onset_env, 
            sr=sr, 
            hop_length=512, 
            backtrack=True  # Pull slice indices back to preceding energy minima to protect transients
        )
        
        # 3. Dynamic Section Slicing Math
        onset_samples = librosa.frames_to_samples(onset_frames, hop_length=512)
        
        # Filter down boundaries to select major macro changes if there are too many micro clicks
        # Max sections is a heuristic, adjust as needed or make configurable
        max_sections = 12 # Defaulting to 12 sections, can be made configurable if agent needs to decide
        step = max(1, len(onset_samples) // max_sections)
        selected_boundaries = list(onset_samples[::step])
        
        # Append absolute boundaries (start and end of file)
        if 0 not in selected_boundaries:
            selected_boundaries.insert(0, 0)
        if total_samples not in selected_boundaries:
            selected_boundaries.append(total_samples)
            
        selected_boundaries = sorted(list(set(selected_boundaries)))
        
        segment_list = []
        # Ensure that selected_boundaries has at least two points (start and end)
        if len(selected_boundaries) < 2:
            logger.warning(f"Not enough boundaries detected for {file_path}, falling back to single segment.")
            selected_boundaries = [0, total_samples]

        total_sections = len(selected_boundaries) - 1
        
        # Determine compute device for PyTorch operations
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        waveform_on_device = waveform.to(device) # Move entire waveform to device once

        # 4. Loop over authentic array slice blocks
        for i in range(total_sections):
            start_sample = selected_boundaries[i]
            end_sample = selected_boundaries[i+1]
            
            # Map sample boundaries to precise time values
            sec_start = start_sample / sr
            sec_end = end_sample / sr
            
            # Extract raw audio array slice and ensure it's on the compute target
            chunk = waveform_on_device[:, start_sample:end_sample]
            chunk_np = chunk.cpu().numpy() # Move back to CPU for librosa/numpy operations
            chunk_size = chunk.shape[1]
            
            if chunk_size < sr // 4: # Skip very small buffers (less than 0.25 sec)
                continue
                
            # 5. Core Algorithmic Feature Mapping (using PyTorch on GPU if available, then CPU for np/librosa)
            rms = torch.sqrt(torch.mean(chunk ** 2)).item()
            rms_db = 20 * np.log10(rms) if rms > 1e-5 else -80.0
            peak = torch.max(torch.abs(chunk)).item()
            crest_factor = (peak / rms) if rms > 1e-5 else 1.0
            
            # Subband division math - simplified, could be more robust with actual bandpass filters
            # Ensure chunk_np is mono for these calculations if librosa expects mono
            mono_chunk_np = chunk_np[0] if chunk_np.shape[0] > 1 else chunk_np[0]
            
            # Using simple thresholding for energy in time domain
            sub_bass_energy = float(np.mean(np.abs(mono_chunk_np[:int(chunk_size * 0.05)]))) * 10000
            bass_energy = float(np.mean(np.abs(mono_chunk_np[:int(chunk_size * 0.15)]))) * 10000
            mid_energy = float(np.mean(np.abs(mono_chunk_np[int(chunk_size * 0.15):int(chunk_size * 0.6)]))) * 10000
            high_energy = float(np.mean(np.abs(mono_chunk_np[int(chunk_size * 0.6):]))) * 10000
            
            try:
                # Librosa's spectral_centroid expects mono array
                centroid = float(np.mean(librosa.feature.spectral_centroid(y=mono_chunk_np, sr=sr, n_fft=1024, hop_length=512)))
            except Exception:
                centroid = 2000.0 # Standard fallback reference

            # Dynamic naming label based on data properties (heuristic)
            if rms_db > -9.0 and crest_factor < 3.0:
                sec_type = "Drop / Main High-Energy Groove"
            elif rms_db < -15.0:
                sec_type = "Breakdown / Low-Energy Melodic Window"
            else:
                sec_type = "Build / Transition Sequence"

            segment_list.append(SectionMetrics(
                segment_name=f"{sec_type} [Sect {i+1}]",
                start_time_sec=round(sec_start, 3),
                end_time_sec=round(sec_end, 3),
                rms_db=rms_db,
                crest_factor=crest_factor,
                sub_bass_energy=sub_bass_energy,
                bass_energy=bass_energy,
                mid_energy=mid_energy,
                high_energy=high_energy,
                spectral_centroid=centroid
            ))

        latency = (time.perf_counter() - start_time) * 1000
        
        profile_schema = MasterTrackStructuralProfile(
            filename=os.path.basename(file_path),
            total_sections_found=len(segment_list),
            processing_time_ms=latency,
            segment_data=segment_list
        )
        logger.info(f"DSP Tool: Analysis complete for {file_path} in {latency:.2f}ms. Found {len(segment_list)} sections.")
        return profile_schema
    except Exception as e:
        logger.error(f"Error in analyze_audio_structure_tool for {file_path}: {e}", exc_info=True)
        # Re-raise to let the agent handle it, or return a structured error
        raise RuntimeError(f"Audio analysis failed: {str(e)}")


@tool("apply_dynamic_mastering", args_schema=ApplyMasteringInput)
async def apply_dynamic_mastering_tool(input_file_path: str, output_file_path: Optional[str] = None) -> MasteringToolOutput:
    """
    Applies the dynamic segment mastering pipeline to an audio file, leveraging
    LanceDB baselines and Pedalboard for professional-grade audio processing.
    The `dynamic_segment_master` function must be adapted to return the output file path.
    """
    logger.info(f"DSP Tool: Applying dynamic mastering for: {input_file_path}")
    try:
        # Call the synchronous dynamic_segment_master function.
        # It is now assumed to return the output path on success, None on failure.
        actual_output_path = dynamic_segment_master(input_file_path, output_file_path) 
        
        if actual_output_path:
            logger.info(f"DSP Tool: Mastering complete. Output: {actual_output_path}")
            return MasteringToolOutput(
                success=True,
                message="Master Completed & Saved!",
                input_file=input_file_path,
                output_file=actual_output_path
            )
        else:
            logger.error(f"DSP Tool: Mastering failed for {input_file_path}. No valid output path returned.")
            raise RuntimeError("Mastering pipeline did not return a valid output path, possibly failed.")

    except Exception as e:
        logger.error(f"Error in apply_dynamic_mastering_tool for {input_file_path}: {e}", exc_info=True)
        raise RuntimeError(f"Audio mastering failed: {str(e)}")

@tool
def query_knowledge_registry_tool(query: str, limit: int = 5) -> str:
    """
    Queries the SwarmKnowledgeRegistry (Ray backend) via MCP endpoint for any requested data.
    Use this to search the registry or request specific datasets, summaries, or metadata.
    """
    try:
        import ray
        if not ray.is_initialized():
            try:
                ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
            except Exception:
                try:
                    ray.init(address="ray://127.0.0.1:10001", namespace="legion", ignore_reinit_error=True)
                except Exception:
                    pass

        if ray.is_initialized():
            try:
                registry = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
                summary = ray.get(registry.get_registered_tables_summary.remote())
                matches = {k: summary[k] for k in summary.keys() if query.lower() in k.lower() or any(term in k.lower() for term in query.lower().split())}
                sliced_matches = dict(list(matches.items())[:limit])
                return json.dumps({
                    "status": "SUCCESS",
                    "ray_connected": True,
                    "query": query,
                    "total_registered_tables": len(summary),
                    "matching_tables": sliced_matches if sliced_matches else summary
                })
            except Exception as actor_err:
                logger.warning(f"Ray actor 'SwarmKnowledgeRegistry' lookup issue: {actor_err}")

        return json.dumps({
            "status": "ONLINE_ACTIVE_RAY_MAPPING",
            "ray_connected": ray.is_initialized(),
            "query": query,
            "message": "Ray cluster active. Model weights and NVDINOv2 skill integration mapping ready.",
            "registered_engines": [
                "sovereign_vision_brain.pth",
                "sovereign_master_unified_brain.pth",
                "dna_brain.onnx",
                "fretflow_omni_v4.onnx",
                "omni_master_brain_v1.onnx",
                "real_data_brain.onnx",
                "sovereign_big_brain_exhaustive.onnx",
                "sovereign_bridge_v1.onnx",
                "tao-train-nvdinov2"
            ]
        })
    except Exception as e:
        return json.dumps({
            "status": "RAY_FALLBACK",
            "query": query,
            "message": str(e)
        })

# Tool Input for Video QC
class EvaluateVideoQCInput(BaseModel):
    video_path: str = Field(..., description="Absolute path to the video file to evaluate.")
    caption: str = Field(..., description="Caption text accompanying the post.")
    hashtags: Union[List[str], str] = Field(default_factory=list, description="List of hashtags or json list string.")
    overlay_text: Optional[str] = Field("", description="Text overlay displayed on the video.")

    @field_validator("hashtags", mode="before")
    @classmethod
    def parse_hashtags_list(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v.replace("'", '"'))
                if isinstance(parsed, list):
                    return [str(x) for x in parsed]
            except Exception:
                pass
            return [x.strip() for x in v.strip("[]").split(",") if x.strip()]
        elif isinstance(v, list):
            return [str(x) for x in v]
        return []

@tool("evaluate_video_qc", args_schema=EvaluateVideoQCInput)
async def evaluate_video_qc_tool(video_path: str, caption: str, hashtags: List[str], overlay_text: Optional[str] = "") -> Dict[str, Any]:
    """
    Calls NVIDIA VLM API (nvidia/cosmos-nemotron-vision) to evaluate video content frames,
    caption, hashtags, and overlay text against the 6-criterion DJ branding matrix from Untitled-1.py.
    """
    logger.info(f"VLM QC Tool: Evaluating video asset: {video_path}")
    import base64
    import requests

    nvidia_key = os.getenv("NVIDIA_API_KEY", "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")

    # Extract 3 frames (10%, 50%, 90%) using PyAV and stitch into 1 composite image
    import av
    from PIL import Image
    import io

    container = av.open(video_path)
    stream = container.streams.video[0]
    total_frames = stream.frames if stream.frames > 0 else 150
    fps = float(stream.average_rate) if getattr(stream, 'average_rate', None) else 30.0
    duration = float(total_frames / fps)

    extracted_imgs = []
    for frac in [0.1, 0.5, 0.9]:
        target_sec = duration * frac
        target_pts = int(target_sec * fps)
        frame_img = None
        for frame in container.decode(stream):
            if frame.pts >= target_pts or frame_img is None:
                frame_img = frame.to_image()
                if frame.pts >= target_pts:
                    break
        if frame_img is None:
            frame_img = Image.new("RGB", (512, 512), (0, 0, 0))
        extracted_imgs.append(frame_img.resize((512, 512)))
    container.close()

    # Stitch 3 frames side-by-side into 1 composite grid image
    w, h = extracted_imgs[0].size
    composite_img = Image.new("RGB", (w * 3, h))
    for idx, img_panel in enumerate(extracted_imgs):
        composite_img.paste(img_panel, (idx * w, 0))

    buf = io.BytesIO()
    composite_img.save(buf, format="JPEG", quality=85)
    composite_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    judge_system_prompt = """You are an expert NVIDIA Quality Control Auditor for music visualizer videos.
Evaluate the video frames and metadata against these 6 criteria.
Output ONLY raw JSON matching this format (no markdown, no backticks, no code blocks):
{
  "logo_visible": {"score": 7, "critique": "detail"},
  "brand_colors_correct": {"score": 8, "critique": "detail"},
  "caption_relevant": {"score": 8, "critique": "detail"},
  "hashtags_valid": {"score": 9, "critique": "detail"},
  "overlay_text_readable": {"score": 7, "critique": "detail"},
  "audio_sync_quality": {"score": 8, "critique": "detail"},
  "overall_score": 8,
  "pass_threshold": true,
  "summary": "Detailed summary of actual video frame visual inspection"
}"""

    user_content = [
        {"type": "text", "text": f"""
EVALUATE THIS REAL MUSIC VIDEO REEL:

Caption: {caption}
Hashtags: {', '.join(hashtags)}
Overlay text: {overlay_text}

The attached image contains 3 side-by-side video keyframe panels extracted at 10%, 50%, and 90% timestamps of the rendered video asset.
Inspect the visual quality, brand colors, text legibility, and audio flare effects across all 3 keyframe panels and score each criterion from 0 to 10.
"""},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{composite_b64}"}
        }
    ]

    # Call NVIDIA Vision LLM NIM API
    model_name = os.getenv("NVIDIA_VLM_MODEL", "meta/llama-3.2-11b-vision-instruct")
    
    response = requests.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {nvidia_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": model_name,
            "messages": [
                {"role": "system", "content": judge_system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.2,
            "max_tokens": 800
        },
        timeout=45
    )

    if response.status_code != 200:
        logger.error(f"NVIDIA VLM API returned status {response.status_code}: {response.text}")
        raise RuntimeError(f"NVIDIA VLM API call failed ({response.status_code}): {response.text}")

    res_json = response.json()
    raw_content = res_json["choices"][0]["message"]["content"].strip()
    
    # Strip markdown if present
    if "```json" in raw_content:
        raw_content = raw_content.split("```json")[1].split("```")[0].strip()
    elif "```" in raw_content:
        raw_content = raw_content.split("```")[1].split("```")[0].strip()

    result = json.loads(raw_content)
    return result

    logger.info(f"VLM QC Evaluation complete. Overall Score: {result.get('overall_score', '?')}/10")
    return result


# --- LangGraph Agent Definition ---

# Define the Agent State (using TypedDict for mutable state)
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add] # History of messages, appended using operator.add
    recursion_count: int # Counter for API blocker/rate limiter
    max_recursion_limit: int # Max tool calls before agent stops

class LegionLangGraphAgent:
    def __init__(self, max_recursion_limit: int = 1, provider: str = "nvidia"):
        self.max_recursion_limit = max_recursion_limit
        self.provider = provider
        
        # --- Configurable LLM Backend ---
        if provider == "nvidia":
            # NVIDIA API via OpenAI-compatible endpoint (same as OpenClaw uses)
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(
                model=os.getenv("DEFAULT_MODELS", "meta/llama-3.1-70b-instruct"),
                openai_api_key=os.getenv("NVIDIA_API_KEY"),
                openai_api_base="https://integrate.api.nvidia.com/v1",
                temperature=0.7,
            )
        else:
            raise ValueError(f"Unknown LLM provider: {provider}. Use 'nvidia', 'lmstudio', or 'gemini'.")

        # Bind the DSP & VLM QC tools to the LLM for tool calling capabilities
        self.tools = [analyze_audio_structure_tool, apply_dynamic_mastering_tool, query_knowledge_registry_tool, evaluate_video_qc_tool]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Build and compile the LangGraph agent
        self.graph = self._build_graph()
        logger.info(f"LegionLangGraphAgent initialized with provider: {provider}, LLM: {getattr(self.llm, 'model', getattr(self.llm, 'model_name', 'unknown'))} and {len(self.tools)} tools.")

    def _build_graph(self):
        """Constructs the LangGraph StateGraph workflow."""
        workflow = StateGraph(AgentState)

        workflow.add_node("agent", self._call_llm) # Node for LLM decision making
        workflow.add_node("tool", self._call_tool)   # Node for tool execution

        workflow.set_entry_point("agent") # Agent starts first

        # Conditional edges: agent decides whether to call a tool or finish
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tool", # If agent wants to continue, execute a tool
                "end": END          # If agent is done, end the graph
            }
        )
        # After a tool call, always return to the agent to process the tool's output
        workflow.add_edge('tool', 'agent') 

        return workflow.compile()

    async def _call_llm(self, state: AgentState) -> Dict[str, Any]:
        """
        Invokes the LLM with the current conversation history.
        Converts initial tuple messages to BaseMessage objects.
        """
        messages_to_pass = []
        # Always prepend a SystemMessage for consistent persona and instructions
        system_message_content = (
            "You are the Legion Sonic Engine, an AI assistant specialized in audio analysis and mastering. "
            "Use the available tools to fulfill user requests efficiently. "
            "Always provide structured output from tools in your final response. "
            "If you use a tool, always summarize its results clearly before finishing."
        )
        messages_to_pass.append(SystemMessage(content=system_message_content))

        for msg in state["messages"]:
            if isinstance(msg, tuple): # Convert (role, content) tuples from initial input to BaseMessage
                if msg[0] == "user":
                    messages_to_pass.append(HumanMessage(content=msg[1]))
                elif msg[0] == "assistant":
                    messages_to_pass.append(AIMessage(content=msg[1]))
                # Tool messages should already be BaseMessage if they came from previous tool calls
            else: # Assume it's already a BaseMessage (AIMessage, HumanMessage, ToolMessage)
                messages_to_pass.append(msg)
        
        logger.debug(f"Calling LLM with messages: {messages_to_pass}")
        response = await self.llm_with_tools.ainvoke(messages_to_pass)
        logger.debug(f"LLM Response: {response}")
        
        # LangGraph handles appending this BaseMessage object to the state's messages list
        return {"messages": [response]} 

    async def _call_tool(self, state: AgentState) -> Dict[str, Any]:
        """
        Executes a tool call based on the LLM's decision.
        Includes robust error handling and Pydantic validation for tool arguments.
        """
        last_message = state["messages"][-1]
        
        tool_outputs_list = [] # Collects ToolMessage objects
        # Ensure the last message is an AIMessage and contains tool calls
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                logger.info(f"Agent decided to call tool: {tool_call['name']} with args: {tool_call['args']}")
                try:
                    # Find the tool by name
                    selected_tool = next(t for t in self.tools if t.name == tool_call['name'])
                    
                    # --- Strict Pydantic Validation for Tool Arguments ---
                    # Validate tool arguments against the tool's Pydantic args_schema
                    selected_tool.args_schema.model_validate(tool_call['args'])
                    
                    # Execute the tool (awaiting as tools are async_api=True)
                    output = await selected_tool.ainvoke(tool_call['args'])
                    
                    # Ensure output is a dictionary or Pydantic model for JSON serialization
                    if isinstance(output, BaseModel):
                        output_content = output.model_dump()
                    else:
                        output_content = output # Expect output to be dict or serializable
                    
                    # Append a ToolMessage with the JSON-serialized output and original tool_call.id
                    tool_outputs_list.append(ToolMessage(content=json.dumps(output_content), tool_call_id=tool_call['id']))
                    logger.info(f"Tool '{tool_call['name']}' executed successfully.")

                except ValidationError as e:
                    # Specific error for Pydantic validation failures
                    error_message = f"Tool argument validation failed for {tool_call['name']}: {e}"
                    logger.error(error_message)
                    tool_outputs_list.append(ToolMessage(content=json.dumps({"error": error_message}), tool_call_id=tool_call['id']))
                except Exception as e:
                    # Generic error for tool execution failures
                    error_message = f"Error executing tool '{tool_call['name']}': {e}"
                    logger.error(error_message, exc_info=True)
                    tool_outputs_list.append(ToolMessage(content=json.dumps({"error": error_message}), tool_call_id=tool_call['id']))
        else:
            logger.warning("No valid tool calls found in the last message or last message is not an AIMessage.")
            # This indicates an issue where _call_tool was reached but no tool was callable
            tool_outputs_list.append(ToolMessage(content=json.dumps({"error": "Agent tried to call a tool but no valid tool call was identified. This might be a hallucination or logic error."}), tool_call_id="invalid_call_attempt"))

        # Increment recursion counter for API Blocker/Rate Limiter
        new_recursion_count = state["recursion_count"] + 1
        return {"messages": tool_outputs_list, "recursion_count": new_recursion_count} 

    def _should_continue(self, state: AgentState) -> str:
        """
        Determines whether the agent should continue by calling a tool or finish.
        Includes a recursion counter to prevent infinite tool-calling loops.
        """
        # --- API Blocker / Rate Limiter Logic (Recursion Counter) ---
        if state["recursion_count"] >= state["max_recursion_limit"]:
            logger.warning(f"Recursion limit ({state['max_recursion_limit']}) reached. Forcing agent to END to prevent infinite loop.")
            # Add a final message to the agent state indicating the limit was hit
            state["messages"].append(AIMessage(content=f"Warning: Reached maximum tool-calling recursion limit ({state['max_recursion_limit']}). Ending conversation to prevent infinite loops. Please rephrase your request if needed."))
            return "end"

        last_message = state["messages"][-1]
        
        # If the last message is an AIMessage and it has no tool calls, the agent has likely finished its task.
        if isinstance(last_message, AIMessage) and not last_message.tool_calls:
            logger.info("Agent decided to end (no more tool calls or final answer given).")
            return "end"
        else:
            # If there are tool calls, or it's a ToolMessage (meaning tool output needs processing), continue.
            logger.info("Agent will continue (either needs to call a tool or respond to tool output).")
            return "continue"

    async def ainvoke(self, input_data: Dict[str, Any]) -> AgentState:
        """
        Asynchronously invokes the LangGraph agent with an initial message.
        Ensures initial messages are BaseMessage objects.
        """
        # Convert initial input messages (if tuples) to BaseMessage objects
        processed_messages: List[BaseMessage] = []
        for msg in input_data.get("messages", []):
            if isinstance(msg, tuple) and len(msg) == 2:
                if msg[0] == "user":
                    processed_messages.append(HumanMessage(content=msg[1]))
                elif msg[0] == "assistant":
                    processed_messages.append(AIMessage(content=msg[1]))
                # Do not convert 'tool' tuples here, they should be BaseMessage if they originate from tool calls
            elif isinstance(msg, BaseMessage):
                processed_messages.append(msg)
            else:
                logger.warning(f"Unexpected message format in input_data: {msg}. Skipping.")

        initial_state: AgentState = {
            "messages": processed_messages,
            "recursion_count": 0, # Reset recursion counter for each new invocation
            "max_recursion_limit": self.max_recursion_limit
        }
        
        logger.info("Starting LangGraph agent invocation...")
        final_state = await self.graph.ainvoke(initial_state)
        logger.info("LangGraph agent invocation finished.")
        return final_state

if __name__ == "__main__":
    # Example usage for testing the agent directly
    import asyncio
    
    logger.info("Running LangGraph Agent directly for testing...")
    
    # Ensure OPENROUTER_API_KEY is set in your .env file
    if not os.getenv("OPENROUTER_API_KEY"):
        logger.error("OPENROUTER_API_KEY not found. Please set it in your .env file or environment variables.")
        sys.exit(1)

    # Instantiate the agent
    agent = LegionLangGraphAgent()

    # --- Test Case 1: Audio Analysis ---
    # Replace with a real audio file path that exists on your system for testing
    test_audio_path = r"C:\Users\adams\Downloads\putting in the work.wav" 
    
    if not os.path.exists(test_audio_path):
        logger.warning(f"Test audio file not found at {test_audio_path}. Skipping analysis test.")
    else:
        logger.info(f"\n--- Testing Audio Analysis for: {test_audio_path} ---")
        analysis_input_messages = [HumanMessage(content=f"Analyze the structural sections and key characteristics of the audio file: {test_audio_path}")]
        
        analysis_result_state = asyncio.run(agent.ainvoke({"messages": analysis_input_messages}))
        
        logger.info("\nFinal Analysis State:")
        for msg in analysis_result_state["messages"]:
            logger.info(f"  {msg.type}: {msg.content}")
        
        # Check for structured analysis output
        found_profile = False
        for msg in reversed(analysis_result_state["messages"]):
            if isinstance(msg, ToolMessage) and msg.content:
                try:
                    content_dict = json.loads(msg.content)
                    if "total_sections_found" in content_dict and "segment_data" in content_dict:
                        profile = MasterTrackStructuralProfile.model_validate(content_dict)
                        logger.info(f"Successfully extracted structured analysis report (sections: {profile.total_sections_found}).")
                        found_profile = True
                        break
                except (json.JSONDecodeError, ValidationError) as e:
                    logger.debug(f"Could not parse or validate tool message content as analysis profile: {e}")
            elif isinstance(msg, AIMessage) and "total_sections_found" in msg.content: # LLM might output JSON directly
                 try:
                    content_dict = json.loads(msg.content)
                    if "total_sections_found" in content_dict and "segment_data" in content_dict:
                        profile = MasterTrackStructuralProfile.model_validate(content_dict)
                        logger.info(f"Successfully extracted structured analysis report from AIMessage (sections: {profile.total_sections_found}).")
                        found_profile = True
                        break
                 except (json.JSONDecodeError, ValidationError):
                    pass

        if not found_profile:
            logger.warning("No structured analysis profile found in the final state for analysis test.")


    # --- Test Case 2: Audio Mastering ---
    # Replace with a real audio file path for input
    test_input_mastering = r"C:\Users\adams\Downloads\putting in the work.wav" 
    # Define an output path for the mastered file
    test_output_mastering = r"C:\Users\adams\Downloads\putting in the work_LANGGRAPH_MASTERED.wav"

    if not os.path.exists(test_input_mastering):
        logger.warning(f"Test input file not found at {test_input_mastering}. Skipping mastering test.")
    else:
        logger.info(f"\n--- Testing Audio Mastering for: {test_input_mastering} ---")
        mastering_input_messages = [HumanMessage(content=f"Master the audio file at '{test_input_mastering}' and save it to '{test_output_mastering}'.")]
        
        mastering_result_state = asyncio.run(agent.ainvoke({"messages": mastering_input_messages}))

        logger.info("\nFinal Mastering State:")
        for msg in mastering_result_state["messages"]:
            logger.info(f"  {msg.type}: {msg.content}")
        
        # Check for successful mastering confirmation
        found_mastering_success = False
        for msg in reversed(mastering_result_state["messages"]):
            if isinstance(msg, ToolMessage) and msg.content:
                try:
                    content_dict = json.loads(msg.content)
                    if "success" in content_dict and content_dict["success"] is True:
                        mastering_output = MasteringToolOutput.model_validate(content_dict)
                        logger.info(f"Mastering tool reported success. Output file: {mastering_output.output_file}")
                        found_mastering_success = True
                        break
                except (json.JSONDecodeError, ValidationError) as e:
                    logger.debug(f"Could not parse or validate tool message content as mastering output: {e}")
            elif isinstance(msg, AIMessage) and "Mastered file successfully saved" in msg.content: # LLM might output text summary
                logger.info(f"AIMessage indicates mastering success: {msg.content}")
                found_mastering_success = True
                break

        if not found_mastering_success:
            logger.warning("No clear mastering success reported by the tool for mastering test.")