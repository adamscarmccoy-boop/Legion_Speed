import sys
sys.path.append(r'C:\STUDIES_BACKUP\Legion-Jacked-Pipeline')
from mcp_server import query_knowledge_registry
import json

print("=== Testing SwarmKnowledgeRegistry via MCP ===")
result = query_knowledge_registry("summary", 5)
summary = json.loads(result)
print(f"Total tables available: {len(summary)}")
print("Sample tables:")
for k in list(summary.keys())[:8]:
    rows = summary[k]["rows"]
    cols = summary[k]["columns"][:4]
    print(f"  {k}: {rows} rows, cols: {cols}")

print("\n--- Querying system_data_audit_report ---")
row_result = query_knowledge_registry("system_data_audit_report", 3)
print(row_result[:800])
