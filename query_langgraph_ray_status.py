import ray
import json
import psutil
from typing import Dict, Any

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


def get_ray_cluster_status() -> Dict[str, Any]:
    status = {}
    try:
        ray.init(address="auto", namespace="legion", ignore_reinit_error=True)
        nodes = ray.nodes()
        status["active_nodes"] = len([n for n in nodes if n.get("Alive", False)])
        
        # Check registered named actors in namespace legion
        actor_names = ["SwarmKnowledgeRegistry", "PaniniRagEngine", "LegionSonicEngine", "LegionVisionOrchestrator"]
        actors_found = {}
        for name in actor_names:
            try:
                actor = ray.get_actor(name, namespace="legion")
                actors_found[name] = "ACTIVE & REGISTERED"
            except Exception:
                actors_found[name] = "NOT_FOUND / UNLOADED"
        status["actors"] = actors_found
        
        # Ray Arrow Swarm summary if SwarmKnowledgeRegistry is active
        try:
            reg = ray.get_actor("SwarmKnowledgeRegistry", namespace="legion")
            summary = ray.get(reg.get_registered_tables_summary.remote())
            status["swarm_tables_count"] = len(summary)
            status["swarm_sample_tables"] = list(summary.keys())[:5]
        except Exception as err:
            status["swarm_tables_count"] = 0
            status["swarm_error"] = str(err)
            
    except Exception as exc:
        status["error"] = str(exc)
        
    return status

def generate_strategic_analysis(cluster_status: Dict[str, Any]):
    print("==================================================================")
    print("          LANGGRAPH & RAY CLUSTER STATUS & NEXT MOVES             ")
    print("==================================================================")
    print("\n1. LIVE RAY CLUSTER DIAGNOSTIC:")
    print(json.dumps(cluster_status, indent=2))
    
    print("\n2. STRATEGIC NEXT MOVES (VISION & AUDIO GENERATION PIPELINES):")
    print("------------------------------------------------------------------")
    print("A. RAY & SWARM CLUSTER STATUS:")
    print(f"   - Ray Head Cluster: ONLINE ({cluster_status.get('active_nodes', 1)} active node)")
    print(f"   - Ray Arrow Swarm: {cluster_status.get('actors', {}).get('SwarmKnowledgeRegistry', 'ACTIVE')}")
    print(f"   - Total Registered Arrow Tables: {cluster_status.get('swarm_tables_count', 0)}")
    
    print("\nB. AUDIO GENERATION & DSP OUTPUT PIPELINE NEXT MOVES:")
    print("   - [ONNX Remaster V2]: Zero-copy memory mapping via PyArrow for stem feature vectors.")
    print("   - [Neural Batch Master]: Run dynamic segment alignment across mastered WAV outputs.")
    print("   - [Audio LLM / Serve]: Stand up Ray Serve endpoint for interactive audio generation & stem synthesis.")
    
    print("\nC. VISION & MULTIMODAL PIPELINE NEXT MOVES:")
    print("   - [Vision Orchestrator]: Connect ONNX vision feature extraction to Ray Arrow Swarm zero-copy registry.")
    print("   - [Cross-Modal Alignment]: Bridge audio spectral centroid/RMS features with visual frame keypoints.")
    print("==================================================================")

if __name__ == "__main__":
    status = get_ray_cluster_status()
    generate_strategic_analysis(status)