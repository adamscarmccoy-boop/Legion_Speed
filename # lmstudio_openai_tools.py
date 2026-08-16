# lmstudio_openai_tools.py - OpenAI Tool Gateway for LM Studio
import json
from openai import OpenAI

# Point OpenAI client directly to your local LM Studio port
client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",  # LM Studio standard REST port
    api_key="lm-studio"  # local server doesn't validate key
)

# 1. Define Tool Schemas (OpenAI Format)
tools = [
    {
        "type": "function",
        "function": {
            "name": "analyze_audio_dsp",
            "description": "Extract RMS, peak, LUFS, and crest factor from audio file",
            "parameters": {
                "type": "object",
                "properties": {
                    "audio_path": {"type": "string", "description": "Path to .wav file"},
                    "target_lufs": {"type": "number", "default": -6.0}
                },
                "required": ["audio_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_ray_registry",
            "description": "Query SwarmKnowledgeRegistry actor in Ray 'legion' namespace",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Vector or SQL query"}
                },
                "required": ["query"]
            }
        }
    }
]

# 2. Execution Function Handlers
def execute_tool(tool_name, args):
    print(f"⚡ [POST-PROMPT TOOL EXEC] Executing {tool_name} with args: {args}")
    if tool_name == "analyze_audio_dsp":
        return {"status": "SUCCESS", "lufs": -8.2, "crest_factor": 7.4, "sub_peak_45hz": -3.1}
    elif tool_name == "query_ray_registry":
        return {"plasma_ref": "obj_9f82a13b4c10", "matched_stems": ["kick_mono_150hz.wav"]}
    return {"error": "Unknown tool"}

# 3. Stream Inference with Tool Invocation Loop
def run_query(user_prompt):
    messages = [
        {"role": "system", "content": "You are Sovereign Core. Use tools to execute actions."},
        {"role": "user", "content": user_prompt}
    ]

    response = client.chat.completions.create(
        model="local-model",  # LM Studio auto-routes to loaded Q4_K_M model
        messages=messages,
        tools=tools,
        tool_choice="auto",
        temperature=0.1
    )

    message = response.choices[0].message

    # Check if model requested a tool call
    if message.tool_calls:
        for tool_call in message.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)
            
            # Execute tool locally
            tool_result = execute_tool(func_name, func_args)

            # Append assistant message & tool response back to thread
            messages.append(message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result)
            })

        # Final pass after tool execution
        final_response = client.chat.completions.create(
            model="local-model",
            messages=messages
        )
        return final_response.choices[0].message.content

    return message.content

# Run Test
if __name__ == "__main__":
    result = run_query("Analyze the DSP for C:\\WEB CASE STUDY\\kick.wav and check Ray registry for matched stems.")
    print("\n[SOVEREIGN OUTPUT]:", result)