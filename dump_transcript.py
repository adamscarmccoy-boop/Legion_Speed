import json
import os

log_path = r'C:\Users\adams\.gemini\antigravity-ide\brain\861ee326-6442-4397-ae7f-b35fcbd4ddb2\.system_generated\logs\transcript_full.jsonl'
out_path = r'C:\WEB CASE STUDY\conversation_history.md'

if not os.path.exists(log_path):
    print('Log path does not exist')
else:
    with open(log_path, 'r', encoding='utf-8') as f, open(out_path, 'w', encoding='utf-8') as out:
        out.write('# Conversation Timeline\n\n')
        for line in f:
            if not line.strip(): continue
            try:
                data = json.loads(line)
                step_type = data.get('type')
                content = data.get('content', '')
                step_index = data.get('step_index')
                
                if step_type == 'USER_INPUT':
                    out.write(f'## USER (Step {step_index}):\n{content}\n\n')
                elif step_type == 'PLANNER_RESPONSE':
                    out.write(f'## AGENT (Step {step_index}):\n{content}\n\n')
            except Exception as e:
                pass
    print(f'Wrote {out_path}')
