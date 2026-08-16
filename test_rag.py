import sys
import os

# Add directory to pythonpath
sys.path.insert(0, r"C:\WEB CASE STUDY")
os.environ["LANCEDB_PATH"] = r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\ableton-session-intelligence\lancedb_web_intel_rag"

from mcp_rag_server import semantic_code_search

print("Testing RAG MCP tool for 'warden code'...")
try:
    result = semantic_code_search("warden code", limit=5)
    print("\n=== RAG SEARCH RESULT ===")
    print(result)
except Exception as e:
    print(f"\nError running search: {e}")

def get_warden_code_search_result() -> str:
    return semantic_code_search("warden code", limit=5)