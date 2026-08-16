import os
import json
from pathlib import Path

def process_transcript_to_dataset(brain_path: str, output_path: str):
    """
    Parses all Antigravity IDE transcript.jsonl files in the brain directory
    and extracts USER_INPUT and MODEL tool calls/responses into a ShareGPT format dataset.
    """
    brain_dir = Path(brain_path)
    
    dataset = []
    
    # Find all transcript.jsonl files
    log_files = list(brain_dir.rglob("transcript.jsonl"))
    
    if not log_files:
        print(f"❌ Could not find any transcripts in {brain_dir}")
        return

    print(f"📖 Found {len(log_files)} transcripts to process...")
    
    for log_file in log_files:
        current_conversation = []
    
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                step = json.loads(line)
                step_type = step.get("type", "")
                
                # Extract User messages
                if step_type == "USER_INPUT":
                    content = step.get("content", "")
                    if content:
                        current_conversation.append({
                            "from": "human",
                            "value": content
                        })
                
                # Extract Model responses/tool calls
                elif step_type == "PLANNER_RESPONSE":
                    content = step.get("content", "")
                    tools = step.get("tool_calls", [])
                    
                    value_str = content
                    if tools:
                        tool_str = json.dumps([{"name": t.get("name"), "args": t.get("arguments")} for t in tools], indent=2)
                        value_str += f"\n[TOOL CALLS]\n{tool_str}"
                    
                    if value_str:
                        current_conversation.append({
                            "from": "gpt",
                            "value": value_str
                        })
                
                except Exception as e:
                    print(f"Skipping line due to error: {e}")

        # If we collected a valid conversation, save it as a single JSON line
        if current_conversation:
            dataset.append({
                "conversations": current_conversation
            })
        
    with open(output_path, "w", encoding="utf-8") as out:
        for entry in dataset:
            out.write(json.dumps(entry) + "\n")
            
    print(f"✅ Extracted {len(current_conversation)} turns into {output_path}")

if __name__ == "__main__":
    # Point to the root brain directory to parse ALL past sessions
    BRAIN_DIR = os.path.expanduser("~/.gemini/antigravity-ide/brain")
    
    OUTPUT_FILE = "antigravity_training_dataset.jsonl"
    
    process_transcript_to_dataset(BRAIN_DIR, OUTPUT_FILE)
