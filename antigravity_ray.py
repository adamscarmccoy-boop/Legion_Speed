import asyncio
import os
import sys
from google.antigravity import Agent, LocalAgentConfig

async def main():
    # 1. Direct validation that the shell environment variable is actively mapped
    if "GEMINI_API_KEY" not in os.environ:
        print("[!] FATAL: GEMINI_API_KEY environment variable is completely empty.", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Confirmed variable exists in current shell memory. Length: {len(os.environ['GEMINI_API_KEY'])} chars.")
    print("[*] Initiating connection to Google cloud infrastructure via native SDK handlers...")

    # 2. LocalAgentConfig automatically reads GEMINI_API_KEY internally from the environment scope
    config = LocalAgentConfig()

    try:
        # 3. Open the secure agent communication loop
        async with Agent(config) as agent:
            prompt = "Verify connection and report current server-side active parameter matrix."
            
            print("[*] Transmitting request over native wire...")
            response = await agent.chat(prompt)
            
            print("\n[+] Cloud Execution Response:\n")
            print(response)

    except Exception as e:
        print(f"\n[-] Native SDK Engine Panicked: {str(e)}", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())
