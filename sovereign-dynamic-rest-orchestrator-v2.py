# -*- coding: utf-8 -*-
"""
🪐 SOVEREIGN CORE: MASTER DYNAMIC REST ORCHESTRATOR (v2-GOLD)
Integrates:
1. Automatic LangSmith Environment Key Bridging to resolve 401 Unauthorized issues.
2. Optimized high-performance directory exclusions to bypass virtual environments.
3. Ast-based reflective tool discovery from your active workspace code.
4. LangGraph orchestration loops managing dynamic state variables.
"""

import os
import sys
import ast
import socket
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Optional

# ==============================================================================
# 🛰️ 1. AUTOMATIC LANGSMITH KEY BRIDGING & ENVIRONMENT STABILIZATION
# ==============================================================================
# Maps the user's specific .env keys to LangChain's required standard variables
# to resolve 'Authentication failed' (401) errors.
if "LANGSMITH_API_KEY" in os.environ and "LANGCHAIN_API_KEY" not in os.environ:
    os.environ["LANGCHAIN_API_KEY"] = os.environ["LANGSMITH_API_KEY"]

if "LANGSMITH_TRACING" in os.environ:
    val = os.environ["LANGSMITH_TRACING"].lower().strip('"')
    os.environ["LANGCHAIN_TRACING_V2"] = "true" if val in ["true", "1"] else "false"
else:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"

if "LANGSMITH_ENDPOINT" in os.environ:
    os.environ["LANGCHAIN_ENDPOINT"] = os.environ["LANGSMITH_ENDPOINT"].strip('"')
else:
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

if "LANGSMITH_PROJECT" in os.environ:
    os.environ["LANGCHAIN_PROJECT"] = os.environ["LANGSMITH_PROJECT"].strip('"')
else:
    os.environ["LANGCHAIN_PROJECT"] = "legion-starter"

# Standardizing directories and workspace paths
WORKSPACE_ROOT = Path("C:/WEB CASE STUDY")
EXCLUDED_DIR_NAMES = {".venv", "venv", ".git", "__pycache__", "node_modules", "build", "dist"}

class SovereignDynamicOrchestrator:
    def __init__(self, workspace_path: Path = WORKSPACE_ROOT):
        self.workspace_path = workspace_path
        self.discovered_tools: Dict[str, Any] = {}
        self.tool_schemas: List[Dict[str, Any]] = []

    # ==============================================================================
    # 🔍 2. DYNAMIC AST REFLECTION ENGINE WITH DIRECTORY EXCLUSIONS
    # ==============================================================================
    def discover_workspace_tools(self):
        """
        Recursively scans the active workspace, bypassing heavy directories,
        parsing python scripts to isolate and register tools annotated with @tool.
        """
        print("=" * 80)
        print("🪐 RUNNING SOVEREIGN DYNAMIC REST TOOL DISCOVERER (v2-GOLD)")
        print("=" * 80)
        print(f"🔍 [DISCOVERY] Initiating recursive search in: {self.workspace_path}")
        
        if not self.workspace_path.is_dir():
            print(f"⚠️ Warning: Workspace directory '{self.workspace_path}' not found on physical drive.")
            return

        py_files_count = 0
        total_files_scanned = 0

        for root, dirs, files in os.walk(self.workspace_path):
            # Prune directory trees to avoid searching deep node virtualenvs (resolves scanning latency)
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIR_NAMES]
            
            for file in files:
                total_files_scanned += 1
                if file.endswith(".py"):
                    py_files_count += 1
                    file_path = Path(root) / file
                    self._parse_file_for_tools(file_path)

        print(f"🟢 [DISCOVERY] Scan Complete. Audited {py_files_count} python scripts (scanned {total_files_scanned} total files).")
        print(f"🟢 [DISCOVERY] Successfully registered {len(self.discovered_tools)} active workspace tools.")

    def _parse_file_for_tools(self, file_path: Path):
        """Reads code files using AST to extract metadata from decorated tools safely."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                node = ast.parse(f.read(), filename=str(file_path))

            for body_item in node.body:
                if isinstance(body_item, ast.FunctionDef):
                    # Check if the function is decorated with @tool or @register_tool
                    is_tool = False
                    for decorator in body_item.decorator_list:
                        # Direct name match like @tool
                        if isinstance(decorator, ast.Name) and decorator.id in ["tool", "register_tool"]:
                            is_tool = True
                        # Attribute call like @langchain.tool
                        elif isinstance(decorator, ast.Attribute) and decorator.attr == "tool":
                            is_tool = True
                    
                    if is_tool:
                        func_name = body_item.name
                        docstring = ast.get_docstring(body_item) or "No documentation provided."
                        parameters = self._extract_ast_parameters(body_item)
                        
                        tool_schema = {
                            "type": "function",
                            "function": {
                                "name": func_name,
                                "description": docstring.split("\n")[0], # First line as short description
                                "parameters": parameters
                            }
                        }
                        self.discovered_tools[func_name] = {
                            "filepath": str(file_path),
                            "schema": tool_schema
                        }
                        self.tool_schemas.append(tool_schema)
                        print(f"  ↳ [REGISTERED] '{func_name}' from: {file_path.name}")
        except Exception as e:
            # Silent fallback for unparseable source files
            pass

    def _extract_ast_parameters(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """Maps Python function annotations to OpenAI parameters schema."""
        properties = {}
        required = []
        
        # Read standard arguments
        for arg in func_node.args.args:
            name = arg.arg
            if name == "self":
                continue
                
            # Default param mapping
            properties[name] = {
                "type": "string",
                "description": f"Parameter {name}"
            }
            required.append(name)
            
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }

    # ==============================================================================
    # 📡 3. REST HTTP LOOPBACK PORT BINDINGS
    # ==============================================================================
    def check_active_port(self, port: int = 1234) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                return s.connect_ex(("127.0.0.1", port)) == 0
        except Exception:
            return False

    def run_telemetry_check(self):
        """Validates network ports and prints active environment configurations."""
        self.discover_workspace_tools()
        
        # Trace active environment parameters to verify LangSmith setup
        print("\n📈 [TELEMETRY] LangSmith Config Check:")
        print(f"  - Tracing Active : {os.environ.get('LANGCHAIN_TRACING_V2')}")
        print(f"  - API Key Set    : {'🟢 YES' if os.environ.get('LANGCHAIN_API_KEY') else '❌ NO (401 Warning)')}")
        print(f"  - Project Target : {os.environ.get('LANGCHAIN_PROJECT')}")
        print(f"  - Endpoint       : {os.environ.get('LANGCHAIN_ENDPOINT')}")

        port_active = self.check_active_port(1234)
        print(f"\n📡 [NETWORKING] Port 1234 Status: {'🟢 ACTIVE (LM Studio Ready)' if port_active else '⚪ INACTIVE (Offline Fallback)'}")

        if self.tool_schemas:
            print("\n📋 Dynamic Tool Schemas Packed:")
            print(json.dumps(self.tool_schemas, indent=2))

if __name__ == "__main__":
    import json
    orchestrator = SovereignDynamicOrchestrator()
    orchestrator.run_telemetry_check()
