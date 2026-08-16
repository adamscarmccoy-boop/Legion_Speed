import os
import sys
import json
import asyncio

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.insert(0, r"C:\WEB CASE STUDY\antigravity_vscode_ext\backend")

from legion_langgraph_brain import (
    LegionLangGraphAgent,
    analyze_audio_structure_tool,
    query_knowledge_registry_tool,
    evaluate_video_qc_tool,
    AnalyzeAudioRequest,
    EvaluateVideoQCInput
)
from langchain_core.messages import HumanMessage

async def run_all_points():
    print("===============================================================")
    print("  RUNNING LEGION LANGCHAIN / LANGGRAPH PYDANTIC POINTS")
    print("===============================================================")

    # Point 1: Swarm Knowledge Registry Tool (Ray Backend)
    print("\n🔹 POINT 1: Query Knowledge Registry Tool (Ray Connected)")
    res_point1 = query_knowledge_registry_tool.invoke({"query": "audio_manifest_vectors", "limit": 5})
    print(f"  Result: {res_point1}")

    # Point 2: Analyze Audio Structure Tool (Pydantic Validation)
    print("\n🔹 POINT 2: Audio Structure Analysis Tool (Pydantic Schema)")
    audio_file = r"C:\WEB CASE STUDY\sovereign_capture.wav"
    if os.path.exists(audio_file):
        req_pydantic = AnalyzeAudioRequest(file_path=audio_file)
        print(f"  Pydantic Input Validated: {req_pydantic}")
        res_point2 = await analyze_audio_structure_tool.ainvoke({"file_path": audio_file})
        print(f"  Analyzed Sections Found: {res_point2.total_sections_found}")
        for sec in res_point2.segment_data[:3]:
            print(f"    - [{sec.segment_name}] {sec.start_time_sec:.1f}s - {sec.end_time_sec:.1f}s | RMS: {sec.rms_db:.2f}dB | Centroid: {sec.spectral_centroid:.0f}Hz")
    else:
        print(f"  ⚠️ Audio file {audio_file} missing. Skipping live audio DSP step.")

    # Point 3: VLM QC Judge Tool (Pydantic Validation)
    print("\n🔹 POINT 3: Evaluate Video QC Tool (Pydantic Schema)")
    video_file = r"C:\WEB CASE STUDY\mastered_output\remix_test\adamscarmccoy_official_vip_reel.mp4"
    qc_input = EvaluateVideoQCInput(
        video_path=video_file,
        caption="ADAM SCAR McCOY — Official VIP Live Set | Dropping Exclusive Tracks Now 🔥",
        hashtags=["#AdamScarMcCoy", "#EDM", "#HouseMusic", "#DJLife"],
        overlay_text="ADAM SCAR McCOY LIVE VIP"
    )
    print(f"  Pydantic Input Validated: {qc_input.model_dump()}")
    res_point3 = await evaluate_video_qc_tool.ainvoke({
        "video_path": video_file,
        "caption": qc_input.caption,
        "hashtags": qc_input.hashtags,
        "overlay_text": qc_input.overlay_text
    })
    print(f"  QC Evaluation Result:\n{json.dumps(res_point3, indent=2)}")

    # Point 4: LangGraph Agent Node Invocation with NVIDIA Provider
    print("\n🔹 POINT 4: Invoking Full LegionLangGraphAgent Graph (NVIDIA NIM Provider)")
    agent = LegionLangGraphAgent(provider="nvidia")
    state = {
        "messages": [
            HumanMessage(content="Evaluate system state: query knowledge registry for audio_manifest_vectors and run VLM QC on C:\\WEB CASE STUDY\\mastered_output\\remix_test\\adamscarmccoy_official_vip_reel.mp4.")
        ],
        "recursion_count": 0,
        "max_recursion_limit": 3
    }
    
    print("  Executing Graph.ainvoke...")
    graph_res = await agent.graph.ainvoke(state)
    print("  Graph Execution Complete!")
    print("  Final Agent Output Messages:")
    for msg in graph_res.get("messages", []):
        sender = msg.__class__.__name__
        print(f"    [{sender}]: {str(msg.content)[:300]}...")

    print("\n===============================================================")
    print("  ✅ ALL LANGCHAIN / LANGGRAPH PYDANTIC POINTS EXECUTED CLEANLY")
    print("===============================================================")

if __name__ == "__main__":
    asyncio.run(run_all_points())
