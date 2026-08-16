"""
LM STUDIO UNIFIED MCP SERVER
=============================

Enhanced version of your existing MCP servers that uses LM Studio (port 1234) 
for BOTH embeddings AND text generation, creating a unified AI-powered system.

This builds upon your existing:
- mcp_rag_server.py (LanceDB + LM Studio embeddings)
- mcp_swarm_gateway_v2.py (orchestration of multiple services)

But adds LM Studio text generation to reduce dependency on external orchestration.
"""

import os

# ==============================================================================
# SOVEREIGN LIFE-CYCLE STABILIZER (AUTO-INJECTED)
# Prevents dangling stdout/stdio pipes and GCS registry locks on Windows exit
# ==============================================================================
import atexit
import signal

def clean_exit_handler(*args, **kwargs):
    import sys
    sys.stderr.write("\n[LMS LIFECYCLE] Exit triggered. Flushing system streams...\n")
    sys.stderr.flush()
    try:
        import ray
        if ray.is_initialized():
            sys.stderr.write("[LMS LIFECYCLE] Active Ray session detected. Disconnecting...\n")
            ray.shutdown()
    except Exception:
        pass
    # Avoid raising SystemExit inside an atexit callback (which causes RuntimeWarnings)
    if args and isinstance(args[0], int):
        sys.exit(0)

atexit.register(clean_exit_handler)
signal.signal(signal.SIGINT, clean_exit_handler)
signal.signal(signal.SIGTERM, clean_exit_handler)
# ==============================================================================

import sys
import json
import logging
import requests
import subprocess
import time
from typing import List, Dict, Any, Optional

# Configure logging to stderr to protect stdio MCP transport
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("LMStudioUnifiedMCP")

# ============================================================================
# CONFIGURATION - USING YOUR EXISTING SETUP
# ============================================================================

# LM Studio Configuration (YOU ARE ALREADY USING THIS FOR EMBEDDINGS)
LM_STUDIO_HOST = os.getenv("LM_STUDIO_HOST", "http://127.0.0.1:1234")
LM_STUDIO_EMBEDDING_MODEL = os.getenv("LM_STUDIO_EMBEDDING_MODEL", "text-embedding-snowflake-arctic-embed-l-v2.0")
LM_STUDIO_LLM_MODEL = os.getenv("LM_STUDIO_LLM_MODEL", "nvidia/nemotron-3-nano-4b")  # YOUR LOADED MODEL

# Your existing data paths (KEEP THESE - they're valuable)
LANCEDB_PATH = os.getenv(
    "LANCEDB_PATH",
    r"C:\STUDIES_BACKUP\vectors\lancedb_store"
)
DUCKDB_PATH = os.getenv(
    "DUCKDB_PATH", 
    r"C:\STUDIES\data\metadata\sonic_core.duckdb"
)

# Optional: Keep connections to your other services as fallbacks/options
MCP_API_BASE = os.getenv("MCP_API_BASE", "http://127.0.0.1:8001")
MCP_TOOLS_EXEC = os.getenv("MCP_TOOLS_EXEC", "http://127.0.0.1:8002/tools/execute")

# ============================================================================
# LM STUDIO HELPER FUNCTIONS
# ============================================================================

def _lmstudio_embedding(text: str) -> List[float]:
    """Get embedding from LM Studio - you're already doing this!"""
    payload = {
        "model": LM_STUDIO_EMBEDDING_MODEL,
        "input": text
    }
    
    try:
        response = requests.post(
            f"{LM_STUDIO_HOST}/v1/embeddings",
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]
    except Exception as e:
        log.error(f"LM Studio embedding failed: {e}")
        raise

def _lmstudio_completion(prompt: str, max_tokens: int = 1024, temperature: float = 0.2, 
                        stop: Optional[List[str]] = None) -> str:
    """Get text completion from LM Studio - THIS IS THE NEW PIECE YOU WANTED"""
    payload = {
        "model": LM_STUDIO_LLM_MODEL,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }
    
    if stop:
        payload["stop"] = stop
        
    try:
        response = requests.post(
            f"{LM_STUDIO_HOST}/v1/completions",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["text"]
    except Exception as e:
        log.error(f"LM Studio completion failed: {e}")
        raise

def _lmstudio_chat_completion(messages: List[Dict[str, str]], max_tokens: int = 1024, 
                             temperature: float = 0.2) -> str:
    """Get chat completion from LM Studio"""
    payload = {
        "model": LM_STUDIO_LLM_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }
    
    try:
        response = requests.post(
            f"{LM_STUDIO_HOST}/v1/chat/completions",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        log.error(f"LM Studio chat completion failed: {e}")
        raise

# ============================================================================
# CORE FUNCTIONALITY - BUILDING ON YOUR EXISTING STRENGTHS
# ============================================================================

def _get_lancedb_connection():
    """Get LanceDB connection - keeping your valuable vector search"""
    try:
        import lancedb
        return lancedb.connect(LANCEDB_PATH)
    except ImportError:
        raise Exception("LanceDB not installed. Install with: pip install lancedb")
    except Exception as e:
        log.error(f"Failed to connect to LanceDB at {LANCEDB_PATH}: {e}")
        raise

def _get_duckdb_connection():
    """Get DuckDB connection - keeping your valuable analytical store"""
    try:
        import duckdb
        return duckdb.connect(DUCKDB_PATH)
    except ImportError:
        raise Exception("DuckDB not installed. Install with: pip install duckdb")
    except Exception as e:
        log.error(f"Failed to connect to DuckDB at {DUCKDB_PATH}: {e}")
        raise

# ============================================================================
# MCP SERVER SETUP
# ============================================================================

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("ERROR: MCP not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

mcp = FastMCP("LMStudio_Unified_RAG_Server")

# ============================================================================
# TOOLS - COMBINING YOUR STRENGTHS WITH LM STUDIO POWER
# ============================================================================

@mcp.tool()
def lmstudio_generate_code(prompt: str, context: str = "", max_tokens: int = 1024) -> str:
    """
    Generate code using LM Studio with optional context.
    This replaces the need for complex orchestration in many cases.
    
    Args:
        prompt: What you want the code to do
        context: Optional context from your knowledge bases
        max_tokens: Maximum tokens to generate
    
    Returns:
        Generated code from LM Studio
    """
    try:
        # Build enhanced prompt
        full_prompt = f"""You are an expert programmer. Generate clean, working code.

CONTEXT:
{context}

REQUEST:
{prompt}

RESPOND WITH ONLY THE CODE - NO EXPLANATIONS UNLESS ASKED FOR.
"""
        
        result = _lmstudio_completion(
            prompt=full_prompt,
            max_tokens=max_tokens,
            temperature=0.1  # Low temperature for code generation
        )
        
        return result.strip()
        
    except Exception as e:
        return f"Error generating code: {str(e)}"

@mcp.tool()
def lmstudio_explain_code(code: str, detail_level: str = "medium") -> str:
    """
    Use LM Studio to explain code - leveraging your model's reasoning.
    
    Args:
        code: Code to explain
        detail_level: "brief", "medium", or "detailed"
    
    Returns:
        Explanation of the code
    """
    try:
        detail_prompts = {
            "brief": "Briefly explain what this code does in 1-2 sentences:",
            "medium": "Explain what this code does, how it works, and its purpose:",
            "detailed": "Provide a detailed explanation including: purpose, algorithm, inputs/outputs, potential edge cases, and complexity analysis:"
        }
        
        prompt = f"""{detail_prompts.get(detail_level, detail_prompts["medium"])}

CODE TO EXPLAIN:
```python
{code}
```

EXPLANATION:
"""
        
        result = _lmstudio_completion(
            prompt=prompt,
            max_tokens=512,
            temperature=0.3
        )
        
        return result.strip()
        
    except Exception as e:
        return f"Error explaining code: {str(e)}"

@mcp.tool()
def lmstudio_debug_error(error_message: str, code_context: str = "") -> str:
    """
    Use LM Studio to help debug errors - leveraging its training on programming issues.
    
    Args:
        error_message: The error message or traceback
        code_context: Optional code that produced the error
    
    Returns:
        Debugging suggestions and potential fixes
    """
    try:
        prompt = f"""You are an expert debugging assistant. Analyze this error and provide solutions.

ERROR:
{error_message}

CODE CONTEXT:
{code_context}

Provide:
1. Likely cause of the error
2. Specific steps to fix it
3. Code example of the fix if applicable
4. Prevention tips for the future

DEBUGGING ANALYSIS:
"""
        
        result = _lmstudio_completion(
            prompt=prompt,
            max_tokens=768,
            temperature=0.2
        )
        
        return result.strip()
        
    except Exception as e:
        return f"Error in debugging analysis: {str(e)}"

@mcp.tool()
def lmstudio_rag_enhanced_search(query: str, use_chain_of_thought: bool = True) -> str:
    """
    Enhanced search that uses LM Studio's reasoning to improve results.
    Combines your LanceDB vector search with LM Studio's understanding.
    
    Args:
        query: Search query
        use_chain_of_thought: Whether to use reasoning to refine search
    
    Returns:
        Search results with AI-enhanced relevance filtering
    """
    try:
        # Step 1: Get vector embedding from LM Studio (your existing strength)
        query_vector = _lmstudio_embedding(query)
        
        # Step 2: Search LanceDB
        db = _get_lancedb_connection()
        table_names = db.table_names()
        
        if not table_names:
            return "No tables found in LanceDB"
            
        # Use the first table or a specific one if you know it
        table_name = table_names[0]  # You can make this configurable
        table = db.open_table(table_name)
        
        # Perform vector search
        results = table.search(query_vector).limit(10).to_pandas()
        
        if results.empty:
            return f"No results found for query: {query}"
            
        # Step 3: Use LM Studio to rank and filter results (THE ENHANCEMENT)
        if use_chain_of_thought and len(results) > 0:
            # Prepare results for analysis
            results_text = ""
            for idx, row in results.iterrows():
                # Extract relevant fields - adjust based on your schema
                content = str(row.get('content', row.get('code', str(row))))[:500]
                results_text += f"Result {idx+1}: {content}\n\n"
            
            # Ask LM Studio to rank and filter
            ranking_prompt = f"""Given the original query: "{query}"

And these search results:
{results_text}

Rank the results by relevance to the query (most relevant first) and return ONLY the top 3 most relevant results in the same format. If a result is not relevant, omit it.

RANKED RESULTS:
"""
            
            ranked_result = _lmstudio_completion(
                prompt=ranking_prompt,
                max_tokens=512,
                temperature=0.1
            )
            
            return f"ENHANCED SEARCH RESULTS FOR: '{query}'\n\n{ranked_result}"
        else:
            # Return raw results
            return f"SEARCH RESULTS FOR: '{query}'\n\n{results.to_string()}"
            
    except Exception as e:
        return f"Error in enhanced search: {str(e)}"

@mcp.tool()
def lmstudio_generate_from_documentation(query: str, doc_source: str = "") -> str:
    """
    Generate code or answers based on documentation using LM Studio's reasoning.
    
    Args:
        query: What you want to know or create
        doc_source: Optional documentation context
    
    Returns:
        Generated answer or code based on documentation understanding
    """
    try:
        # If no doc source provided, try to get relevant docs from your knowledge base
        if not doc_source:
            # Search for documentation in your databases
            doc_context = lmstudio_rag_enhanced_search(f"documentation {query}", use_chain_of_thought=False)
        else:
            doc_context = doc_source
            
        # Use LM Studio to synthesize answer from documentation
        prompt = f"""Based on the following documentation, answer the user's question or fulfill their request.

DOCUMENTATION:
{doc_context}

REQUEST:
{query}

RESPONSE:
"""
        
        result = _lmstudio_completion(
            prompt=prompt,
            max_tokens=768,
            temperature=0.2
        )
        
        return result.strip()
        
    except Exception as e:
        return f"Error generating from documentation: {str(e)}"

@mcp.tool()
def lmstudio_refactor_code(code: str, goal: str = "improve readability") -> str:
    """
    Use LM Studio to refactor or improve code.
    
    Args:
        code: Code to refactor
        goal: What to optimize for (readability, performance, safety, etc.)
    
    Returns:
        Refactored code
    """
    try:
        prompt = f"""You are an expert software engineer. Refactor the following code to {goal}.

ORIGINAL CODE:
```python
{code}
```

REFACTORED CODE ({goal}):
```python
"""
        
        result = _lmstudio_completion(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.1
        )
        
        # Extract just the code block
        if "```python" in result:
            start = result.find("```python") + 9
            end = result.find("```", start)
            if end != -1:
                return result[start:end].strip()
        
        return result.strip()
        
    except Exception as e:
        return f"Error refactoring code: {str(e)}"

@mcp.tool()
def lmstudio_design_architecture(requirements: str, constraints: str = "") -> str:
    """
    Use LM Studio's reasoning to design software architecture.
    
    Args:
        requirements: What the system should do
        constraints: Any constraints (performance, tech stack, etc.)
    
    Returns:
        Architecture design and recommendations
    """
    try:
        prompt = f"""You are a software architect. Design a solution based on these requirements and constraints.

REQUIREMENTS:
{requirements}

CONSTRAINTS:
{constraints if constraints else "None specified"}

Provide:
1. High-level architecture overview
2. Key components and their responsibilities
3. Data flow description
4. Technology recommendations
5. Implementation considerations

ARCHITECTURE DESIGN:
"""
        
        result = _lmstudio_completion(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.3
        )
        
        return result.strip()
        
    except Exception as e:
        return f"Error designing architecture: {str(e)}"

@mcp.tool()
def hybrid_search_and_generate(query: str, search_limit: int = 5) -> str:
    """
    Combines your existing vector search with LM Studio generation for powerful results.
    This is the BEST OF BOTH WORLDS: your data + AI reasoning.
    
    Args:
        query: What to search for and generate about
        search_limit: How many initial results to retrieve
    
    Returns:
        AI-generated answer grounded in your data
    """
    try:
        # Step 1: Your existing strength - vector search
        query_vector = _lmstudio_embedding(query)
        db = _get_lancedb_connection()
        table_names = db.table_names()
        
        if not table_names:
            return "No data sources available"
            
        # Search across relevant tables
        all_results = []
        for table_name in table_names[:3]:  # Limit to first 3 tables for performance
            try:
                table = db.open_table(table_name)
                results = table.search(query_vector).limit(search_limit).to_pandas()
                if not results.empty:
                    results['source_table'] = table_name
                    all_results.append(results)
            except Exception as e:
                log.warning(f"Could not search table {table_name}: {e}")
                continue
        
        if not all_results:
            return f"No results found for query: {query}"
            
        # Combine results
        import pandas as pd
        combined_results = pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()
        
        # Step 2: Prepare context for LM Studio
        context_parts = []
        for idx, row in combined_results.head(10).iterrows():  # Limit context size
            # Extract text content - adjust based on your actual schema
            content_fields = ['content', 'code', 'description', 'text', 'document']
            content = ""
            for field in content_fields:
                if field in row and pd.notna(row[field]) and str(row[field]).strip():
                    content = str(row[field])[:300]  # Limit length
                    break
            
            if not content:
                content = str(row.to_dict())[:300]
                
            source_info = f"[Source: {row.get('source_table', 'unknown')}]" if 'source_table' in row else ""
            context_parts.append(f"{source_info} {content}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Step 3: Use LM Studio to synthesize answer from the retrieved context
        prompt = f"""Based on the following information from your knowledge base, provide a comprehensive answer to the query.

INFORMATION FROM KNOWLEDGE BASE:
{context}

QUERY:
{query}

Provide a thorough, accurate answer that synthesizes the relevant information. If the information is insufficient to fully answer the question, answer:
"""
        
        result = _lmstudio_completion(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.2
        )
        
        return f"HYBRID SEARCH & GENERATION RESULT\nQuery: {query}\n\n{result.strip()}"
        
    except Exception as e:
        return f"Error in hybrid search and generate: {str(e)}"

# ============================================================================
# OPTIONAL: LEGACY COMPATIBILITY - KEEP YOUR EXISTING SERVICE CALLS AS FALLBACKS
# ============================================================================

def _call_mcp_api(endpoint: str, payload: dict) -> dict:
    """Fallback to your existing MCP API server if needed"""
    try:
        response = requests.post(f"{MCP_API_BASE}/{endpoint}", json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log.warning(f"MCP API call to {endpoint} failed: {e}")
        return {"error": str(e)}

@mcp.tool()
def legacy_delegate_to_swarm(instruction: str) -> str:
    """
    Legacy compatibility: Delegate to your existing swarm system.
    Kept for backward compatibility, but prefer the direct LM Studio approaches above.
    """
    try:
        result = _call_mcp_api("tools/execute", {
            "tool": "swarm_orchestrator",
            "parameters": {"instruction": instruction}
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Legacy swarm delegation failed: {str(e)}"

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    log.info("Starting LM Studio Unified MCP Server...")
    log.info(f"LM Studio Host: {LM_STUDIO_HOST}")
    log.info(f"Embedding Model: {LM_STUDIO_EMBEDDING_MODEL}")
    log.info(f"LLM Model: {LM_STUDIO_LLM_MODEL}")
    log.info(f"LanceDB Path: {LANCEDB_PATH}")
    log.info(f"DuckDB Path: {DUCKDB_PATH}")
    
    # Test LM Studio connection on startup
    try:
        test_embedding = _lmstudio_embedding("test connection")
        log.info(f"LM Studio connection successful. Embedding dimension: {len(test_embedding)}")
        
        test_completion = _lmstudio_completion("Say 'hello' in one word:", max_tokens=10)
        log.info(f"LM Studio completion test: {test_completion.strip()}")
        
    except Exception as e:
        log.error(f"Failed to connect to LM Studio: {e}")
        log.error("Make sure LM Studio is running with local server started (Developer -> Start Local Server)")
        # Don't exit - let the server start anyway, connections will fail gracefully
    
    # Run the server
    try:
        mcp.run()
    except KeyboardInterrupt:
        log.info("Server shutting down...")
    except Exception as e:
        log.error(f"Server error: {e}")
        sys.exit(1)