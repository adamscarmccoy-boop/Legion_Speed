#!/usr/bin/env python3
"""
=============================================================================
🏛️ SOVEREIGN KERNEL TOOL DISCOVERY ENGINE (kernel_discovery.py)
Automated reflection: Inspects Python docstrings + type hints -> Generates Gemini schemas.
=============================================================================
"""

import inspect
from typing import Callable, Dict, Any, List, Tuple
from google.genai import types

_TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}

def kernel_tool(name: Optional[str] = None, description: Optional[str] = None):
    """Decorator to register any Python function as a Kernel Tool automatically."""
    def decorator(fn: Callable):
        tool_name = name or fn.__name__
        tool_desc = description or (fn.__doc__ or "No description provided.").strip().split("\n")[0]
        
        sig = inspect.signature(fn)
        properties = {}
        required = []

        type_map = {
            str: "STRING",
            int: "INTEGER",
            float: "NUMBER",
            bool: "BOOLEAN",
            list: "ARRAY",
            dict: "OBJECT",
            Any: "STRING"
        }

        for param_name, param in sig.parameters.items():
            if param_name in ["self", "cls"]:
                continue
            
            p_type = type_map.get(param.annotation, "STRING")
            properties[param_name] = types.Schema(
                type=p_type,
                description=f"Parameter: {param_name}"
            )
            
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        _TOOL_REGISTRY[tool_name] = {
            "callable": fn,
            "declaration": types.FunctionDeclaration(
                name=tool_name,
                description=tool_desc,
                parameters=types.Schema(
                    type="OBJECT",
                    properties=properties,
                    required=required if required else None
                )
            )
        }
        return fn
    return decorator

def build_gemini_toolbox() -> Tuple[List[types.Tool], Dict[str, Callable]]:
    """Builds the complete Gemini types.Tool array and execution dispatch map."""
    declarations = [entry["declaration"] for entry in _TOOL_REGISTRY.values()]
    dispatch_map = {name: entry["callable"] for name, entry in _TOOL_REGISTRY.items()}
    
    tools = [types.Tool(function_declarations=declarations)] if declarations else []
    return tools, dispatch_map