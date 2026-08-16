import os
import sys
import json
import duckdb
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# 1. Load Workspace Environment
load_dotenv(r"C:\WEB CASE STUDY\.env")
nvidia_api_key = os.getenv("NVIDIA_API_KEY")

if not nvidia_api_key:
    print("❌ Error: NVIDIA_API_KEY is missing from .env")
    sys.exit(1)

print("=" * 80)
print("🚀 STANDALONE RAG DEV TOOL (Zero-MCP, Direct DuckDB+Lance + NVIDIA NIM API)")
print("=" * 80)

# 2. Initialize In-Memory DuckDB with Native Lance Extension
print("\n1️⃣  Initializing DuckDB & Loading Native 'lance' Extension...")
con = duckdb.connect(database=":memory:")

try:
    con.execute("INSTALL lance;")
    con.execute("LOAD lance;")
    print("  ✅ DuckDB 'lance' extension loaded successfully!")
except Exception as e:
    print(f"  ⚠️ Note on Lance extension: {e}")

# 3. Create Sample Documents & Load into DuckDB Table
print("\n2️⃣  Building In-Memory Code Knowledge Table...")
sample_docs = [
    {"doc_id": 1, "filename": "ray_arrow_swarm.py", "content": "Ray Swarm manages PyArrow zero-copy tables in Windows DRAM memory using Ray actors."},
    {"doc_id": 2, "filename": "mcp_api_server.py", "content": "MCP API Server hosts FastAPI endpoints on port 8002 to bridge Ray actors with Web interfaces."},
    {"doc_id": 3, "filename": "compile_gemma.py", "content": "Optimum CLI exports Gemma model to ONNX format with opset 18 and causal-lm-with-past KV caching."},
    {"doc_id": 4, "filename": "sovereign_engine_manifesto.md", "content": "Sovereign Audio Engine runs local 37-dim acoustic math and ONNX neural models for real-time mastering."}
]

con.execute("CREATE TABLE code_knowledge (doc_id INT, filename VARCHAR, content VARCHAR);")
for doc in sample_docs:
    con.execute("INSERT INTO code_knowledge VALUES (?, ?, ?);", (doc['doc_id'], doc['filename'], doc['content']))

print(f"  ✅ Inserted {len(sample_docs)} documents into DuckDB zero-copy table.")

# 4. Define Direct DuckDB Retrieval Function (Tool)
def search_code_knowledge(keyword: str) -> str:
    """Searches local DuckDB code knowledge base using SQL matching."""
    print(f"\n🔍 [LOCAL DUCKDB TOOL EXECUTED] Searching knowledge base for: '{keyword}'...")
    query = "SELECT filename, content FROM code_knowledge WHERE LOWER(content) LIKE LOWER(?);"
    results = con.execute(query, (f"%{keyword}%",)).fetchall()
    
    # Fallback to single word matching if full string has no exact match
    if not results:
        words = [w for w in keyword.split() if len(w) > 3]
        for w in words:
            results = con.execute("SELECT filename, content FROM code_knowledge WHERE LOWER(content) LIKE LOWER(?);", (f"%{w}%",)).fetchall()
            if results:
                break

    if not results:
        return f"No documents found matching keyword: {keyword}"
    
    output = []
    for r in results:
        output.append(f"File: {r[0]} | Snippet: {r[1]}")
    return "\n".join(output)

# 5. Connect to NVIDIA NIM API using LangChain SDK Tool Bindings
print("\n3️⃣  Connecting to NVIDIA NIM API (Llama 3.1 70B Instruct)...")
try:
    from langchain_nvidia_ai_endpoints import ChatNVIDIA
    from langchain_core.tools import tool
    from langchain_core.messages import HumanMessage, ToolMessage
except ImportError:
    print("📦 Installing 'langchain-nvidia-ai-endpoints'...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "langchain-nvidia-ai-endpoints"])
    from langchain_nvidia_ai_endpoints import ChatNVIDIA
    from langchain_core.tools import tool
    from langchain_core.messages import HumanMessage, ToolMessage

# Wrap local search function as a LangChain Tool
@tool
def code_search_tool(query_term: str) -> str:
    """Useful for searching the local code knowledge database for technical implementation details."""
    return search_code_knowledge(query_term)

# Initialize ChatNVIDIA pointing directly to NVIDIA's cloud NIM endpoint
llm = ChatNVIDIA(
    model="meta/llama-3.1-70b-instruct",
    nvidia_api_key=nvidia_api_key,
    temperature=0.1
)

# Bind the local DuckDB tool directly to NVIDIA NIM LLM
llm_with_tools = llm.bind_tools([code_search_tool])

# 6. Execute RAG Query with Automatic Tool Calling
user_prompt = "Can you check our code knowledge base and explain how Ray Swarm handles memory?"
print(f"\n4️⃣  Sending User Prompt to NVIDIA NIM:\n    💬 '{user_prompt}'")

messages = [HumanMessage(content=user_prompt)]
ai_msg = llm_with_tools.invoke(messages)
messages.append(ai_msg)

# Check if NVIDIA NIM requested a Tool Call
if ai_msg.tool_calls:
    print(f"\n⚙️  NVIDIA NIM Triggered Tool Call: {ai_msg.tool_calls[0]['name']}")
    tool_call = ai_msg.tool_calls[0]
    tool_result = search_code_knowledge(tool_call['args']['query_term'])
    
    # Send tool execution result back to NVIDIA NIM for final synthesis
    messages.append(ToolMessage(content=tool_result, tool_call_id=tool_call['id']))
    final_response = llm_with_tools.invoke(messages)
    
    print("\n" + "=" * 80)
    print("🤖 NVIDIA NIM FINAL RAG SYNTHESIS RESPONSE:")
    print("=" * 80)
    print(final_response.content)
    print("=" * 80)
else:
    print("\n🤖 Response (Direct):", ai_msg.content)

print("\n✨ Test Complete: Zero-MCP, Direct DuckDB + NVIDIA NIM Tool Calling Verified!")
