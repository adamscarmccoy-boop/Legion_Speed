import sys, os, asyncio
sys.path.append(r"C:\WEB CASE STUDY\antigravity_vscode_ext\backend")
from legion_langgraph_brain import LegionLangGraphAgent
from langchain_core.messages import HumanMessage
import ray

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


ray.init(address="auto", namespace="legion", ignore_reinit_error=True)

async def main():
    app = LegionLangGraphAgent()
    query = "what ray server's should be up for the legion"
    print(f"QUERY: {query}")
    
    async for event in app.graph.astream(
        {
            "messages": [HumanMessage(content=query)], 
            "recursion_count": 0,
            "max_recursion_limit": 5
        },
        stream_mode="updates"
    ):
        print(event)

if __name__ == "__main__":
    asyncio.run(main())