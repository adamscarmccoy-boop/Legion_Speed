"""
Legion Sonic Engine - LangGraph Audio Agent
Fixed version with NVIDIA, LM Studio, and Gemini provider support.
"""

import os
import sys
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
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END

# Import your dynamic mastering pipeline
from dynamic_segment_master import dynamic_segment_master

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("legion_langgraph_brain")

# --- Load .env ---
env_path = os.path.join("C:\\", "WEB CASE STUDY", ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()


# ──────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────

class SectionMetrics(BaseModel):
    segment_name: str = Field(..., description="Descriptive name of the audio segment.")
    start_time_sec: float = Field(..., description="Start time in seconds.")
    end_time_sec: float = Field(..., description="End time in seconds.")
    rms_db: float = Field(..., description="RMS loudness in dB.")
    crest_factor: float = Field(..., description="Crest factor (peak vs RMS).")
    sub_bass_energy: float = Field(..., description="Sub-bass frequency energy.")
    bass_energy: float = Field(..., description="Bass frequency energy.")
    mid_energy: float = Field(..., description="Mid-range frequency energy.")
    high_energy: float = Field(..., description="High-frequency energy.")
    spectral_centroid: float = Field(..., description="Spectral centroid (brightness).")


class MasterTrackStructuralProfile(BaseModel):
    filename: str = Field(..., description="Name of the analyzed audio file.")
    total_sections_found: int = Field(..., description="Total sections identified.")
    processing_time_ms: float = Field(..., description="Processing time in ms.")
    segment_data: List[SectionMetrics] = Field(..., description="Per-section metrics.")


class AnalyzeAudioRequest(BaseModel):
    file_path: str = Field(..., description="Absolute path to the audio file.")


class ApplyMasteringInput(BaseModel):
    input_file_path: str = Field(..., description="Input audio file path.")
    output_file_path: Optional[str] = Field(None, description="Output file path.")


class MasteringToolOutput(BaseModel):
    success: bool = Field(..., description="True if mastering succeeded.")
    message: str = Field(..., description="Result message.")
    input_file: str = Field(..., description="Input file path.")
    output_file: str = Field(..., description="Output file path.")


# ──────────────────────────────────────────────
# DSP Tools
# ──────────────────────────────────────────────

@tool("analyze_audio_structure", args_schema=AnalyzeAudioRequest)
async def analyze_audio_structure_tool(file_path: str) -> MasterTrackStructuralProfile:
    """Analyzes structural sections of an audio file using DSP (Librosa/PyTorch)."""
    logger.info(f"DSP Tool: Analyzing: {file_path}")
    start_time = time.perf_counter()

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Track missing: {file_path}")

    try:
        waveform, sr = torchaudio.load(file_path)
        total_samples = waveform.shape[1]
        mono_y = torch.mean(waveform.cpu(), dim=0).numpy()

        onset_env = librosa.onset.onset_strength(y=mono_y, sr=sr, hop_length=512)
        onset_frames = librosa.onset.onset_detect(
            onset_envelope=onset_env, sr=sr, hop_length=512, backtrack=True
        )
        onset_samples = librosa.frames_to_samples(onset_frames, hop_length=512)

        max_sections = 12
        step = max(1, len(onset_samples) // max_sections)
        selected_boundaries = list(onset_samples[::step])

        if 0 not in selected_boundaries:
            selected_boundaries.insert(0, 0)
        if total_samples not in selected_boundaries:
            selected_boundaries.append(total_samples)

        selected_boundaries = sorted(list(set(selected_boundaries)))

        if len(selected_boundaries) < 2:
            selected_boundaries = [0, total_samples]

        total_sections = len(selected_boundaries) - 1
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        waveform_on_device = waveform.to(device)
        segment_list = []

        for i in range(total_sections):
            start_sample = selected_boundaries[i]
            end_sample = selected_boundaries[i + 1]
            sec_start = start_sample / sr
            sec_end = end_sample / sr

            chunk = waveform_on_device[:, start_sample:end_sample]
            chunk_np = chunk.cpu().numpy()
            chunk_size = chunk.shape[1]

            if chunk_size < sr // 4:
                continue

            rms = torch.sqrt(torch.mean(chunk ** 2)).item()
            rms_db = 20 * np.log10(rms) if rms > 1e-5 else -80.0
            peak = torch.max(torch.abs(chunk)).item()
            crest_factor = (peak / rms) if rms > 1e-5 else 1.0

            mono_chunk_np = chunk_np[0] if chunk_np.shape[0] > 1 else chunk_np[0]
            sub_bass_energy = float(np.mean(np.abs(mono_chunk_np[:int(chunk_size * 0.05)]))) * 10000
            bass_energy = float(np.mean(np.abs(mono_chunk_np[:int(chunk_size * 0.15)]))) * 10000
            mid_energy = float(np.mean(np.abs(mono_chunk_np[int(chunk_size * 0.15):int(chunk_size * 0.6)]))) * 10000
            high_energy = float(np.mean(np.abs(mono_chunk_np[int(chunk_size * 0.6):]))) * 10000

            try:
                centroid = float(np.mean(
                    librosa.feature.spectral_centroid(y=mono_chunk_np, sr=sr, n_fft=1024, hop_length=512)
                ))
            except Exception:
                centroid = 2000.0

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
                spectral_centroid=centroid,
            ))

        latency = (time.perf_counter() - start_time) * 1000
        profile = MasterTrackStructuralProfile(
            filename=os.path.basename(file_path),
            total_sections_found=len(segment_list),
            processing_time_ms=latency,
            segment_data=segment_list,
        )
        logger.info(f"Analysis done: {latency:.2f}ms, {len(segment_list)} sections.")
        return profile

    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise RuntimeError(f"Audio analysis failed: {str(e)}")


@tool("apply_dynamic_mastering", args_schema=ApplyMasteringInput)
async def apply_dynamic_mastering_tool(
    input_file_path: str, output_file_path: Optional[str] = None
) -> MasteringToolOutput:
    """Applies dynamic segment mastering pipeline to an audio file."""
    logger.info(f"Mastering: {input_file_path}")
    try:
        actual_output_path = dynamic_segment_master(input_file_path, output_file_path)
        if actual_output_path:
            return MasteringToolOutput(
                success=True,
                message="Master Completed & Saved!",
                input_file=input_file_path,
                output_file=actual_output_path,
            )
        else:
            raise RuntimeError("Mastering returned no valid output path.")
    except Exception as e:
        logger.error(f"Mastering error: {e}", exc_info=True)
        raise RuntimeError(f"Mastering failed: {str(e)}")


@tool
def query_knowledge_registry_tool(query: str, limit: int = 5) -> str:
    """Queries the SwarmKnowledgeRegistry via MCP endpoint."""
    if r"C:\web case study" not in sys.path:
        sys.path.append(r"C:\web case study")
    from mcp_server import query_knowledge_registry
    try:
        return query_knowledge_registry(query, limit)
    except Exception as e:
        return f"Error querying registry: {e}"


# ──────────────────────────────────────────────
# LangGraph Agent
# ──────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    recursion_count: int
    max_recursion_limit: int


class LegionLangGraphAgent:
    def __init__(self, max_recursion_limit: int = 3, provider: str = "nvidia"):
        self.max_recursion_limit = max_recursion_limit
        self.provider = provider

        # ── NVIDIA NIM API ──
        if provider == "nvidia":
            from langchain_openai import ChatOpenAI
            nvidia_key = os.getenv("NVIDIA_API_KEY")
            if not nvidia_key:
                raise ValueError("NVIDIA_API_KEY not found in environment.")
            self.llm = ChatOpenAI(
                model=os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct"),
                openai_api_key=nvidia_key,
                openai_api_base="https://integrate.api.nvidia.com/v1",
                temperature=0.7,
            )
        # ── LM Studio (Local) ──
        elif provider == "lmstudio":
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(
                model="local-model",
                openai_api_key="lm-studio",
                openai_api_base=os.getenv("LMSTUDIO_API_BASE", "http://localhost:1234/v1"),
                temperature=0.7,
            )
        # ── Google Gemini ──
        elif provider == "gemini":
            self.llm = ChatGoogleGenerativeAI(
                model=os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=0.7,
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

        self.tools = [
            analyze_audio_structure_tool,
            apply_dynamic_mastering_tool,
            query_knowledge_registry_tool,
        ]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.graph = self._build_graph()
        logger.info(f"Agent ready: provider={provider}, tools={len(self.tools)}")

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", self._call_llm)
        workflow.add_node("tool", self._call_tool)
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {"continue": "tool", "end": END},
        )
        workflow.add_edge("tool", "agent")
        return workflow.compile()

    async def _call_llm(self, state: AgentState) -> Dict[str, Any]:
        messages_to_pass = [SystemMessage(content=(
            "You are the Legion Sonic Engine, an AI assistant specialized in "
            "audio analysis and mastering. Use available tools to fulfill user "
            "requests. Always summarize tool results clearly."
        ))]
        for msg in state["messages"]:
            if isinstance(msg, tuple):
                if msg[0] == "user":
                    messages_to_pass.append(HumanMessage(content=msg[1]))
                elif msg[0] == "assistant":
                    messages_to_pass.append(AIMessage(content=msg[1]))
            else:
                messages_to_pass.append(msg)

        response = await self.llm_with_tools.ainvoke(messages_to_pass)
        return {"messages": [response]}

    async def _call_tool(self, state: AgentState) -> Dict[str, Any]:
        last_message = state["messages"][-1]
        tool_outputs_list = []

        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                logger.info(f"Tool call: {tool_call['name']}, args: {tool_call['args']}")
                try:
                    selected_tool = next(t for t in self.tools if t.name == tool_call["name"])
                    selected_tool.args_schema.model_validate(tool_call["args"])
                    output = await selected_tool.ainvoke(tool_call["args"])

                    if isinstance(output, BaseModel):
                        output_content = output.model_dump()
                    else:
                        output_content = output

                    tool_outputs_list.append(
                        ToolMessage(
                            content=json.dumps(output_content, default=str),
                            tool_call_id=tool_call["id"],
                        )
                    )
                except ValidationError as e:
                    tool_outputs_list.append(ToolMessage(
                        content=json.dumps({"error": f"Validation: {e}"}),
                        tool_call_id=tool_call["id"],
                    ))
                except Exception as e:
                    tool_outputs_list.append(ToolMessage(
                        content=json.dumps({"error": f"Execution: {e}"}),
                        tool_call_id=tool_call["id"],
                    ))
        else:
            tool_outputs_list.append(ToolMessage(
                content=json.dumps({"error": "No valid tool call found."}),
                tool_call_id="invalid",
            ))

        return {
            "messages": tool_outputs_list,
            "recursion_count": state["recursion_count"] + 1,
        }

    def _should_continue(self, state: AgentState) -> str:
        if state["recursion_count"] >= state["max_recursion_limit"]:
            logger.warning("Recursion limit reached. Ending.")
            state["messages"].append(AIMessage(
                content="Maximum tool-calling limit reached. Please refine your request."
            ))
            return "end"
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and not last_message.tool_calls:
            return "end"
        return "continue"


# ──────────────────────────────────────────────
# Direct test (optional)
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    key = os.getenv("NVIDIA_API_KEY")
    if not key:
        logger.error("NVIDIA_API_KEY not set!")
        sys.exit(1)

    agent = LegionLangGraphAgent(provider="nvidia")
    test_msg = [HumanMessage(content="Hello! What tools do you have?")]
    result = asyncio.run(agent.graph.ainvoke({
        "messages": test_msg,
        "recursion_count": 0,
        "max_recursion_limit": 3,
    }))
    for msg in result["messages"]:
        logger.info(f"{msg.type}: {msg.content}")
