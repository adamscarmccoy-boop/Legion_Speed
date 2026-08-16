import sys
from openai import OpenAI
from swarm_cognitive_tools import SWARM_TOOL_SCHEMAS, dispatch_swarm_tool

# Initialize connection to your local LM Studio engine (Port 1234)
client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")

def ask_nemotron_how_to_be_faster(user_query: str):
    """Exposes sensory tools to Nemotron and lets the model reason and act."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are the autonomic orchestrator of this local GPU-accelerated supercomputer. "
                "Use your sensory tools to check VRAM, C++ logs, and Ray latencies. "
                "Diagnose bottlenecks, verify your hypotheses with benchmarks, and compile your final report."
            )
        },
        {"role": "user", "content": user_query}
    ]

    # Hand the sensory tool menu directly to the 16K model
    response = client.chat.completions.create(
        model="nvidia/nemotron-3-nano-4b",
        messages=messages,
        tools=SWARM_TOOL_SCHEMAS,  # The JSON schemas we imported [cite: 1]
        temperature=0.0            # Zero-entropy sampling for strict system math [cite: 1]
    )

    choice = response.choices.message
    
    if choice.tool_calls:
        for tool_call in choice.tool_calls:
            print(f"⚡ [NEMOTRON ACTS]: Executing sensory tool '{tool_call.function.name}'...")
            
            # Execute the tool on the metal and grab the raw telemetry
            tool_output = dispatch_swarm_tool(tool_call.function.name, json.loads(tool_call.function.arguments))
            
            print(f"📥 [TELEMETRY RETRIEVED]: {tool_output[:200]}...")
            
            # Feed the real-world metrics back to Nemotron's context window!
            messages.append({"role": "assistant", "content": "", "tool_calls": [tool_call]})
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_output
            })
            
        # Let Nemotron process the real data and deliver the final verified solution
        final_response = client.chat.completions.create(
            model="nvidia/nemotron-3-nano-4b",
            messages=messages
        )
        print(f"\n🏁 [NEMOTRON ANALYSIS]:\n{final_response.choices.message.content}")