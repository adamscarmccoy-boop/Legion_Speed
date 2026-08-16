Absolutely! To configure Ray with a specific namespace and set up Ray Serve for backing up services, you'll primarily modify your `ray.init()` calls and add `ray.serve` deployment code.

Here's how to edit your existing Ray initialization and a new code block for Ray Serve:

---

### 1. **Integrating the `legion` Namespace into Ray Initialization**

The `namespace` argument in `ray.init()` ensures that all subsequent Ray actors, tasks, and (if specified) Serve deployments operate within that isolated environment. This prevents naming conflicts and helps organize your distributed applications.

**Existing Code Snippets to Update:**

**a) In `legion_langgraph_brain.py` (and similar files where `ray.init()` is called):**

```python
import os
import time
import json
import torch
import torchaudio
import librosa
import numpy as np
import logging
import operator
from dotenv import load_dotenv
from typing import List, Tuple, Annotated, TypedDict, Optional, Any, Dict

from pydantic import BaseModel, Field, ValidationError

# LangChain/LangGraph imports
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END

# Import the dynamic mastering pipeline
from dynamic_segment_master import dynamic_segment_master

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("legion_langgraph_brain")

env_path = os.path.join("C:\\", "WEB CASE STUDY", ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

# ... (Pydantic Models and other code) ...

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

# --- LangGraph Agent Definition ---

# Define the Agent State (using TypedDict for mutable state)
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add] # History of messages, appended using operator.add
    recursion_count: int # Counter for API blocker/rate limiter
    max_recursion_limit: int # Max tool calls before agent stops

class LegionLangGraphAgent:
    def __init__(self, max_recursion_limit: int = 5): # Default recursion limit
        self.max_recursion_limit = max_recursion_limit
        
        # --- Google AI Studio API Swap ---
        self.llm = ChatGoogleGenerativeAI(
            model="gemma-4-31b-it", # Using the large Gemma model natively on Google AI Studio
            google_api_key=os.getenv("GOOGLE_API_KEY"), # Requires GOOGLE_API_KEY in your .env
            temperature=0.7, # Balanced creativity
            # streaming=False # Optional
        )
        # Bind the DSP tools to the LLM for tool calling capabilities
        self.tools = [analyze_audio_structure_tool, apply_dynamic_mastering_tool]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Build and compile the LangGraph agent
        self.graph = self._build_graph()
        logger.info(f"LegionLangGraphAgent initialized with LLM: {getattr(self.llm, 'model', getattr(self.llm, 'model_name', 'unknown'))} and {len(self.tools)} tools.")

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
                logger.info(f"Agent decided to call tool: {tool_call.name} with args: {tool_call.args}")
                try:
                    # Find the tool by name
                    selected_tool = next(t for t in self.tools if t.name == tool_call.name)
                    
                    # --- Strict Pydantic Validation for Tool Arguments ---
                    # Validate tool arguments against the tool's Pydantic args_schema
                    tool_input_model = selected_tool.args_schema.model_validate(tool_call.args)
                    
                    # Execute the tool (awaiting as tools are async_api=True)
                    output = await selected_tool.ainvoke(tool_input_model)
                    
                    # Ensure output is a dictionary or Pydantic model for JSON serialization
                    if isinstance(output, BaseModel):
                        output_content = output.model_dump()
                    else:
                        output_content = output # Expect output to be dict or serializable
                    
                    # Append a ToolMessage with the JSON-serialized output and original tool_call.id
                    tool_outputs_list.append(ToolMessage(content=json.dumps(output_content), tool_call_id=tool_call.id))
                    logger.info(f"Tool '{tool_call.name}' executed successfully.")

                except ValidationError as e:
                    # Specific error for Pydantic validation failures
                    error_message = f"Tool argument validation failed for {tool_call.name}: {e}"
                    logger.error(error_message)
                    tool_outputs_list.append(ToolMessage(content=json.dumps({"error": error_message}), tool_call_id=tool_call.id))
                except Exception as e:
                    # Generic error for tool execution failures
                    error_message = f"Error executing tool '{tool_call.name}': {e}"
                    logger.error(error_message, exc_info=True)
                    tool_outputs_list.append(ToolMessage(content=json.dumps({"error": error_message}), tool_call_id=tool_call.id))
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
    import sys
    
    # Ensure background cluster context is initialized with the "legion" namespace
    if not ray.is_initialized():
        ray.init(namespace="legion")
    
    logger.info("Running LangGraph Agent directly for testing...")
    
    # Ensure OPENROUTER_API_KEY is set in your .env file
    if not os.getenv("OPENROUTER_API_KEY"):
        logger.error("OPENROUTER_API_KEY not found. Please set it in your .env file or environment variables.")
        sys.exit(1)

    # Instantiate the agent
    agent = LegionLangGraphAgent()

    # ... (Test Cases) ...
```

**b) In your Ray Actor files (e.g., for `HeadlessAudioEngineActor`, `HeadlessStructuralAudioEngine`):**

```python
import os
import time
import torch
import torchaudio
import librosa
import numpy as np
import ray
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# Initialize background Ray environment if it isn't already running
if not ray.is_initialized():
    ray.init(namespace="legion") # <--- ADD THIS LINE

# ==========================================
# Pydantic Target Metrics Validation Layer
# ==========================================
class SegmentMetrics(BaseModel):
    segment_name: str
    rms_db: float
    crest_factor: float
    sub_bass_energy: float
    bass_energy: float
    mid_energy: float
    high_energy: float
    spectral_centroid: float

class MasterTrackProfile(BaseModel):
    filename: str
    processing_time_ms: float
    segment_data: List[SegmentMetrics]


# ==========================================
# Headless Audio Engine Ray Actor Definition
# ==========================================
@ray.remote(num_gpus=1 if torch.cuda.is_available() else 0)
class HeadlessAudioEngineActor:
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"📦 Ray Actor initialized on headless node device: {self.device}")

    def profile_track(self, file_path: str, segment_count: int = 4) -> dict:
        """Loads a file from disk and parses it completely in the background"""
        start_time = time.perf_counter()
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file missing at path: {file_path}")

        # Headless disk ingestion
        waveform, sr = torchaudio.load(file_path)
        
        # Split data into even multi-segment chunks across time-axis
        total_samples = waveform.shape[1]
        chunk_size = total_samples // segment_count
        
        segment_list = []
        
        # Loop through each time slice completely headless
        for i in range(segment_count):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size
            
            # Slice audio tensor and push to compute target
            chunk = waveform[:, start_idx:end_idx].to(self.device)
            chunk_np = chunk.cpu().numpy()
            
            # Sub-band extraction via manual slice math
            # Calculate Root-Mean-Square energy
            rms = torch.sqrt(torch.mean(chunk ** 2)).item()
            rms_db = 20 * np.log10(rms) if rms > 1e-5 else -80.0
            
            # Calculate Crest Factor (Transient snap)
            peak = torch.max(torch.abs(chunk)).item()
            crest_factor = (peak / rms) if rms > 1e-5 else 1.0
            
            # Basic frequency boundary estimations using absolute array mean variance
            sub_bass_energy = float(np.mean(np.abs(chunk_np[:, :int(chunk_size * 0.05)]))) * 10000
            bass_energy = float(np.mean(np.abs(chunk_np[:, :int(chunk_size * 0.15)]))) * 10000
            mid_energy = float(np.mean(np.abs(chunk_np[:, int(chunk_size * 0.15):int(chunk_size * 0.6)]))) * 10000
            high_energy = float(np.mean(np.abs(chunk_np[:, int(chunk_size * 0.6):]))) * 10000
            
            # Spectral Centroid estimation via Librosa
            try:
                centroid = float(np.mean(librosa.feature.spectral_centroid(y=chunk_np[0], sr=sr)))
            except Exception:
                centroid = 2000.0 # Standard fallback reference
                
            # Compile values into structured segment dictionaries
            segment_list.append(SegmentMetrics(
                segment_name=f"Segment {i+1} / Data Window",
                rms_db=rms_db,
                crest_factor=crest_factor,
                sub_bass_energy=sub_bass_energy,
                bass_energy=bass_energy,
                mid_energy=mid_energy,
                high_energy=high_energy,
                spectral_centroid=centroid
            ))
            
        latency = (time.perf_counter() - start_time) * 1000
        
        # Instantiate master Pydantic schema validation model
        master_profile = MasterTrackProfile(
            filename=os.path.basename(file_path),
            processing_time_ms=latency,
            segment_data=segment_list
        )
        
        # Return standard raw JSON dict to the main thread
        return master_profile.model_dump()

print("✅ Headless Ray Actor setup complete and verified.")
```

---

### 2. **Setting Up Ray Serve for Backup Services in the `legion` Namespace**

Ray Serve allows you to deploy scalable, fault-tolerant services on your Ray cluster. When you start Ray Serve within a namespace, all deployments created afterward will also belong to that namespace.

Here's an example of how you might set up a simple "Legion Status" service using Ray Serve, assuming you've initialized Ray with `namespace="legion"` as shown above:

```python
import ray
import ray.serve as serve
from typing import Dict, Any

# It's crucial that ray.init() is called with the namespace before serve.start()
# If Ray is not already initialized, this will initialize it with the namespace.
if not ray.is_initialized():
    ray.init(namespace="legion")

print(f"Ray initialized with namespace: {ray.get_runtime_context().namespace}")

# 1. Define your Serve Deployment
@serve.deployment(num_replicas=1, route_prefix="/legion-status")
class LegionStatusService:
    def __init__(self):
        # You can access other Ray actors in the same namespace here
        # For example, if you had a SocialActor in the "legion" namespace:
        # self.social_actor = ray.get_actor("SocialActor", namespace="legion")
        print("LegionStatusService deployment initialized.")

    async def __call__(self, request) -> Dict[str, Any]:
        """
        Handles incoming HTTP requests to this service.
        """
        print(f"Received request: {request.url}")
        status = {
            "service_name": "LegionStatusService",
            "status": "online",
            "message": "All core Legion services are operational within the 'legion' namespace.",
            "ray_namespace": ray.get_runtime_context().namespace,
            "timestamp": time.time()
        }
        # You could add calls to other actors here to get their status
        # e.g., social_status = await self.social_actor.ping.remote()
        # status["social_actor_status"] = social_status
        return status

# 2. Start Ray Serve and Deploy the Service
# serve.start() will automatically use the namespace set by ray.init()
# or you can explicitly specify it: serve.start(detached=True, namespace="legion")
serve.start(detached=True) # detached=True allows the script to exit while service runs

# Deploy the service
legion_status_app = LegionStatusService.deploy()

print("\n✅ Ray Serve started and 'LegionStatusService' deployed.")
print(f"Access your service at: http://localhost:8000/legion-status")
print("To stop the service and Serve: serve.shutdown()")

# Example of how you might interact with it (in a separate script or later)
# import requests
# response = requests.get("http://localhost:8000/legion-status").json()
# print(response)
```

**Explanation:**

*   **`ray.init(namespace="legion")`**: This is the crucial change. It sets up a dedicated logical space within your Ray cluster called "legion". All actors, tasks, and Serve deployments started *after* this initialization (without explicitly overriding the namespace) will belong to this space.
*   **`@serve.deployment`**: This decorator marks your `LegionStatusService` class as a Ray Serve deployment.
*   **`serve.start(detached=True)`**: This starts the Ray Serve controller. `detached=True` means that even if the Python script that launched Serve exits, the services will continue to run on the Ray cluster.
*   **`LegionStatusService.deploy()`**: This command deploys your service to the Ray Serve controller. Ray Serve then manages the lifecycle, scaling, and routing of your service.
*   **`ray.get_runtime_context().namespace`**: This allows any Ray task or actor to programmatically discover the namespace it is currently operating in, which is useful for debugging and dynamic configuration.

By implementing these changes, your Ray actors and Serve deployments will be logically grouped under the "legion" namespace, making your distributed architecture more organized and robust.