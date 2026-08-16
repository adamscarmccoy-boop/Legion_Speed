import lancedb
import ray
import json
import time
import sys

sys.path.insert(0, r"C:\WEB CASE STUDY")
sys.stdout.reconfigure(encoding="utf-8")

from acp_control_plane import ACPControlPlane, AgentRegistration, ACPEnvelope

def main():
    print("=" * 70)
    print(" EXECUTING LIVE MARKETING INTEL & ACP CONTROL PLANE ROUTING ")
    print("=" * 70)
    
    # 1. Initialize ACP Control Plane
    acp = ACPControlPlane()
    acp.register_agent(AgentRegistration(
        agent_id="marketing_engine",
        agent_name="Marketing Intel Swarm",
        capabilities=["viral_hook_eval", "market_target", "dsp_alignment"],
        endpoint_uri="http://127.0.0.1:8001/tools/execute",
        last_heartbeat=time.time()
    ))
    
    # 2. Query Marketing Intel Tables from LanceDB
    db_path = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag"
    db = lancedb.connect(db_path)
    
    trends = db.open_table("marketing_promo_trends").to_pandas().to_dict("records")
    intel = db.open_table("marketing_scraped_intel_2026").to_pandas().to_dict("records")
    
    top_strategy = max(trends, key=lambda x: x["viral_score"])
    top_rule = intel[0] # 1.2-Second Bass-Face Hook
    
    # 3. Dispatch ACP Envelope
    envelope = ACPEnvelope(
        trace_id="tr_mkt_9901",
        sender_id="marketing_engine",
        action="market_target",
        parameters={
            "strategy": top_strategy,
            "retention_rule": top_rule
        }
    )
    
    route_res = acp.route_envelope(envelope)
    
    print(f"\n[+] ACP Route Result: {json.dumps(route_res, indent=2)}")
    print(f"\n🔥 SELECTED STRATEGY : {top_strategy['style_category']} (Score: {top_strategy['viral_score']}/10)")
    print(f"📌 VIRAL HOOK        : \"{top_strategy['viral_hook']}\"")
    print(f"🎬 FORMAT & LAYOUT   : {top_strategy['format']}")
    print(f"👁️ VISUAL ELEMENTS   : {top_strategy['visual_elements']}")
    print(f"🔊 AUDIO SYNC        : {top_strategy['audio_sync']}")
    print(f"⚡ ALGORITHM RULE    : {top_rule['strategy_name']} -> {top_rule['retention_rule']}")
    print("=" * 70)

if __name__ == "__main__":
    main()
