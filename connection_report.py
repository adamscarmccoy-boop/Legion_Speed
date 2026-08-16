"""Connection report — what's actually wired and what isn't."""
import os, sys, subprocess

def run_ps(ps_cmd):
    return subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_cmd],
        capture_output=True, text=True
    ).stdout

print("=" * 70)
print(" LEGION CONNECTION REPORT")
print("=" * 70)
print()

print("--- WHAT IS RUNNING ---")
print(run_ps(
    "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" "
    "| Select-Object ProcessId,CreationDate,CommandLine "
    "| Format-List | Out-String"
))

print("--- TCP LISTENERS ---")
print(run_ps(
    "Get-NetTCPConnection -State Listen "
    "| Select-Object LocalAddress,LocalPort,OwningProcess "
    "| Format-Table -AutoSize | Out-String"
))

print("--- LEGION_GRAPH IMPORTS ---")
sys.path.insert(0, r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline")
try:
    import legion_graph
    print(f"  status:  IMPORTED OK")
    print(f"  has app: {hasattr(legion_graph, 'app')}")
    if hasattr(legion_graph, "app"):
        print(f"  app type: {type(legion_graph.app).__name__}")
except Exception as e:
    print(f"  status:  IMPORT FAILS")
    print(f"  error:   {e}")

print()
print("--- MCP_SERVER IMPORTS LEGION_GRAPH? ---")
src = open(r"C:\STUDIES_BACKUP\Legion-Jacked-Pipeline\mcp_server.py",
           encoding="utf-8", errors="ignore").read()
print(f"  imports legion_graph: {'legion_graph' in src}")
print(f"  imports langgraph:    {'langgraph' in src}")
print(f"  uses StateGraph:      {'StateGraph' in src}")
print(f"  uses .invoke:         {'.invoke(' in src}")

print()
print("--- SONIC_CORE_V2.DUCKDB VIEWS ---")
import duckdb
con = duckdb.connect(r"C:\STUDIES_BACKUP\data\metadata\sonic_core_v2.duckdb", read_only=True)
for row in con.execute(
    "SELECT table_type, table_name FROM information_schema.tables "
    "WHERE table_schema='main' ORDER BY table_type, table_name"
).fetchall():
    print(f"  [{row[0]:<5}] {row[1]}")
print()
print("--- DATA INTEGRITY (sample_categories via DuckDB) ---")
n = con.execute("SELECT COUNT(*) FROM sample_categories").fetchone()[0]
print(f"  sample_categories rows reachable: {n:,}")
con.close()
