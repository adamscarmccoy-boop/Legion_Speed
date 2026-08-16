import asyncio
import sys
sys.stdout.reconfigure(encoding="utf-8")
from mcp import ClientSession
from mcp.client.sse import sse_client

async def run():
    print("Connecting to MCP SSE endpoint on 8003...")
    try:
        async with sse_client("http://localhost:8003/sse") as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                tools = await session.list_tools()
                print("TOOLS AVAILABLE:", [t.name for t in tools.tools])
                
                print("\nCalling swarm_code_search with 'ray[serve]'...")
                res = await session.call_tool("swarm_code_search", {"search_term": "ray[serve]", "limit": 10})
                
                if hasattr(res, 'content') and res.content:
                    print("RESULT:")
                    print(res.content[0].text)
                else:
                    print("RESULT:", res)
    except Exception as e:
        print(f"Error testing MCP server: {e}")

if __name__ == "__main__":
    asyncio.run(run())
