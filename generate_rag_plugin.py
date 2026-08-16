import os
import sys
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

load_dotenv()
api_key = os.getenv("AISTUDIO_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: API key not found in .env")
    sys.exit(1)

client = genai.Client(api_key=api_key)

contents_to_send = []

# Upload the architecture document we just generated
arch_file = r"C:\WEB CASE STUDY\gemini_endgame_architecture.md"
if os.path.exists(arch_file):
    print("Uploading architecture context...")
    f = client.files.upload(
        file=arch_file,
        config=types.UploadFileConfig(mime_type="text/plain", display_name="gemini_endgame_architecture.md")
    )
    contents_to_send.append(f)

prompt = """
You are the lead architect for the Sovereign Audio Intelligence system.
I have uploaded the `gemini_endgame_architecture.md` file which contains the architecture you designed for our native Node.js LM Studio plugin (rag-v2).

I need you to write the COMPLETE, working TypeScript code for the 5 core files.
No placeholders. Implement the full DuckDB, LanceDB, Monty stub, and AIStudioRouter logic, and tie them together in promptPreprocessor.ts.

You MUST format your output EXACTLY using these delimiters so my script can parse and save the files automatically:

@@@FILE: src/services/LanceDBService.ts@@@
[typescript code here]
@@@END@@@

Generate the following files:
1. src/services/LanceDBService.ts
2. src/services/DuckDBService.ts
3. src/services/MontyNativeService.ts
4. src/services/AIStudioRouter.ts
5. src/promptPreprocessor.ts
"""

contents_to_send.append(prompt)

print("Consulting AI Studio (gemini-2.5-flash) to generate the full codebase... This may take a moment.")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=contents_to_send
)

print("\n--- TOKEN GENERATION METRICS ---")
if hasattr(response, 'usage_metadata') and response.usage_metadata:
    print(f"Prompt Tokens: {response.usage_metadata.prompt_token_count}")
    print(f"Candidate Tokens: {response.usage_metadata.candidates_token_count}")
    print(f"Total Tokens: {response.usage_metadata.total_token_count}")
print("--------------------------------\n")

text = response.text

print("\nParsing and creating files...")
pattern = r"@@@FILE:\s*(.*?)\s*@@@(.*?)@@@END@@@"
matches = re.findall(pattern, text, re.DOTALL)

if not matches:
    print("❌ Failed to parse files from response. Output was:")
    print(text)
    sys.exit(1)

base_dir = r"C:\WEB CASE STUDY\rag-v2"
for filename, code in matches:
    filepath = os.path.join(base_dir, filename.strip())
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Clean up markdown formatting if the model wrapped it in ```typescript
    code = code.strip()
    if code.startswith("```typescript"):
        code = code[13:]
    if code.startswith("```ts"):
        code = code[4:]
    if code.endswith("```"):
        code = code[:-3]
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code.strip())
    print(f"✅ Created {filepath}")

print("\nAll files successfully generated and saved to disk!")
