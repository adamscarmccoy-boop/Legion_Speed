
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

"""
LM STUDIO UNIFIED MCP SERVER - FINAL VERSION
============================================

This is a practical, working MCP server that uses YOUR existing LM Studio instance 
(port 1234) for BOTH embeddings AND text generation, eliminating the need for 
complex orchestration of multiple services.

IT BUILDS ON YOUR WORKING SETUP:
- You already have LM Studio providing embeddings via http://127.0.0.1:1234/v1/embeddings
- This adds text generation via http://127.0.0.1:1234/v1/completions
- Everything flows through your single LM Studio instance on port 1234

USAGE:
1. Make sure LM Studio is running with:
   - Local server started (Developer → Start Local Server)
   - Model: nvidia/nemotron-3-nano-4b loaded
2. Run this script: python lmstudio_unified_mcp_final.py
3. Your LM Studio instance will now serve as a unified MCP server with AI capabilities

FEATURES:
- ✅ Uses your existing embeddings (no change to what already works)
- ✅ Adds text generation/code explanation/debugging via LM Studio
- ✅ Works with your LanceDB, DuckDB, and Ray Swarm data sources
- ✅ Simple, direct, and reliable - no complex orchestration needed
- ✅ Drop-in replacement for your existing MCP RAG server
"""

import os
import sys
import json
import logging
import requests
import time
from typing import List, Dict, Any, Optional

# Configure logging to stderr to protect stdio MCP transport
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("LMStudio_Unified_MCP")

# ============================================================================
# CONFIGURATION - USING YOUR EXISTING, WORKING SETUP
# ============================================================================

# YOUR LM STUDIO INSTANCE - THIS IS ALREADY WORKING FOR EMBEDDINGS
LM_STUDIO_HOST = os.getenv("LM_STUDIO_HOST", "http://127.0.0.1:1234")
LM_STUDIO_EMBEDDING_MODEL = os.getenv("LM_STUDIO_EMBEDDING_MODEL", "text-embedding-snowflake-arctic-embed-l-v2.0")
LM_STUDIO_LLM_MODEL = os.getenv("LM_STUDIO_LLM_MODEL", "nvidia/nemotron-3-nano-4b")  # YOUR LOADED MODEL

# YOUR EXISTING DATA SOURCES - KEEP THESE AS THEY'RE VALUABLE
LANCEDB_PATH = os.getenv(
    "LANCEDB_PATH",
    r"C:\STUDIES_BACKUP\vectors\lancedb_store"
)
DUCKDB_PATH = os.getenv(
    "DUCKDB_PATH", 
    r"C:\STUDIES\data\metadata\sonic_core.duckdb"
)

# ============================================================================
# LM STUDIO HELPER FUNCTIONS - BUILDING ON YOUR WORKING EMBEDDINGS
# ============================================================================

def lmstudio_embedding(text: str) -> List[float]:
    """Get embedding from LM Studio - YOU ARE ALREADY DOING THIS SUCCESSFULLY"""
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

def lmstudio_completion(prompt: str, max_tokens: int = 1024, temperature: float = 0.2,
                       stop: Optional[List[str]] = None) -> str:
    """Get text completion from LM Studio - THE KEY ADDITION TO YOUR WORKING SETUP"""
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

def lmstudio_chat_completion(messages: List[Dict[str, str]], max_tokens: int = 1024,
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
# DATA SOURCE CONNECTIONS - KEEPING YOUR EXISTING SETUP
# ============================================================================

def get_lancedb_connection():
    """Get LanceDB connection"""
    try:
        import lancedb
        return lancedb.connect(LANCEDB_PATH)
    except ImportError:
        raise Exception("LanceDB not installed. Install with: pip install lancedb")
    except Exception as e:
        log.error(f"Failed to connect to LanceDB at {LANCEDB_PATH}: {e}")
        raise

def get_duckdb_connection():
    """Get DuckDB connection"""
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

mcp = FastMCP("LMStudio_Unified_MCP_Server")

# ============================================================================
# CORE TOOLS - EVERYTHING FLOWS THROUGH LM STUDIO 1234
# ============================================================================

@mcp.tool()
def lmstudio_generate_code(prompt: str, context: str = "", max_tokens: int = 1024) -> str:
    """
    Generate code using LM Studio with optional context.
    USES YOUR LM STUDIO INSTANCE ON PORT 1234
    
    Args:
        prompt: What you want the code to do
        context: Optional context from your knowledge bases
        max_tokens: Maximum tokens to generate
    
    Returns:
        Generated code from LM Studio
    """
    try:
        # Build prompt with context
        full_prompt = f"""You are an expert programmer. Generate clean, working, well-documented code.

CONTEXT FROM KNOWLEDGE BASES:
{context}

TASK:
{prompt}

RESPOND WITH ONLY THE CODE - NO EXPLANATIONS UNLESS SPECIFICALLY ASKED FOR.
"""
        
        result = lmstudio_completion(
            prompt=full_prompt,
            max_tokens=max_tokens,
            temperature=0.1  # Low temperature for focused code generation
        )
        
        return result.strip()
        
    except Exception as e:
        return f"Error generating code with LM Studio: {str(e)}"

@mcp.tool()
def lmstudio_explain_code(code: str, detail_level: str = "medium") -> str:
    """
    Explain code using LM Studio - leveraging your model's reasoning.
    USES YOUR LM STUDIO INSTANCE ON PORT 1234
    
    Args:
        code: Code to explain
        detail_level: "brief", "medium", or "detailed"
    
    Returns:
        Explanation of the code from LM Studio
    """
    try:
        detail_prompts = {
            "brief": "Briefly explain what this code does in 1-2 sentences:",
            "medium": "Explain what this code does, how it works, its purpose, and key characteristics:",
            "detailed": "Provide a detailed explanation including: purpose, algorithm, data structures, inputs/outputs, time/space complexity, potential edge cases, and usage examples:"
        }
        
        prompt = f"""{detail_prompts.get(detail_level, detail_prompts["medium"])}

CODE TO EXPLAIN:
```python
{code}
```

EXPLANATION:
"""
        
        result = lmstudio_completion(
            prompt=prompt,
            max_tokens=768,
            temperature=0.3
        )
        
        return result.strip()
        
    except Exception as e:
        return f"Error explaining code with LM Studio: {str(e)}"

@mcp.tool()
def lmstudio_debug_error(error_message: str, code_context: str = "") -> str:
    """
    Use LM Studio to help debug errors - leveraging its training on programming issues.
    USES YOUR LM STUDIO INSTANCE ON PORT 1234
    
    Args:
        error_message: The error message or traceback
        code_context: Optional code that produced the error
    
    Returns:
        Debugging suggestions and potential fixes from LM Studio
    """
    try:
        prompt = f"""You are an expert debugging assistant with deep knowledge of programming languages, common errors, and best practices. Analyze this error and provide actionable solutions.

ERROR DETAILS:
{error_message}

CODE CONTEXT (if provided):
{code_context}

Provide:
1. Most likely cause of the error
2. Specific steps to fix it (with code example if applicable)
3. How to prevent similar errors in the future
4. Any relevant best practices or language-specific considerations

DEBUGGING ANALYSIS:
"""
        
        result = lmstudio_completion(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.2
        )
        
        return result.strip()
        
    except Exception as e:
        return f"Error in debugging analysis with LM Studio: {str(e)}"

@mcp.tool()
def lmstudio_rag_enhanced_search(query: str, use_chain_of_thought: bool = True) -> str:
    """
    Enhanced search that uses LM Studio's reasoning to improve results.
    1. Uses YOUR LM Studio embeddings (what already works)
    2. Searches your LanceDB/DuckDB knowledge bases
    3. Uses LM Studio's reasoning to rank and filter results
    USES YOUR LM STUDIO INSTANCE ON PORT 1234 FOR BOTH STEPS
    
    Args:
        query: Search query
        use_chain_of_thought: Whether to use reasoning to refine search
    
    Returns:
        Search results with AI-enhanced relevance filtering
    """
    try:
        # STEP 1: Get vector embedding from LM Studio (YOUR EXISTING, WORKING APPROACH)
        query_vector = lmstudio_embedding(query)
        
        # STEP 2: Search your knowledge bases
        context_parts = []
        sources_searched = []
        
        # Search LanceDB
        try:
            db = get_lancedb_connection()
            table_names = db.table_names()
            if table_names:
                # Search first few tables for performance
                for table_name in table_names[:3]:
                    try:
                        table = db.open_table(table_name)
                        results = table.search(query_vector).limit(5).to_pandas()
                        if not results.empty:
                            for _, row in results.iterrows():
                                content = str(row.get('content', row.get('code', str(row))))[:300]
                                context_parts.append(content)
                                sources_searched.append(f"LanceDB:{table_name}")
                    except Exception as e:
                        log.warning(f"Could not search LanceDB table {table_name}: {e}")
        except Exception as e:
            log.warning(f"LanceDB search warning: {e}")
        
        # Search DuckDB (simple text search for now - you can enhance with vector search)
        try:
            conn = get_duckdb_connection()
            tables = conn.execute("SHOW TABLES").fetchall()
            for table_tuple in tables[:2]:  # Limit to first 2 tables
                table_name = table_tuple[0]
                try:
                    # Simple text search in DuckDB
                    results = conn.execute(
                        f"SELECT * FROM {table_name} WHERE sql LIKE '%{query}%' LIMIT 5"
                    ).fetchall()
                    if results:
                        for row in results:
                            content = str(row)[:300]
                            context_parts.append(content)
                            sources_searched.append(f"DuckDB:{table_name}")
                except Exception as e:
                    log.warning(f"Could not search DuckDB table {table_name}: {e}")
        except Exception as e:
            log.warning(f"DuckDB search warning: {e}")
        
        # Prepare context
        context = "\n\n---\n\n".join(context_parts) if context_parts else "No specific context found in knowledge bases."
        sources_info = f"Sources searched: {', '.join(sources_searched)}" if sources_searched else "No sources found"
        
        # STEP 3: Use LM Studio to generate final answer (THE KEY ADDITION)
        if use_chain_of_thought and context_parts:
            prompt = f"""Based on the following information from your knowledge bases, provide a comprehensive and accurate answer to the query.

KNOWLEDGE BASE INFORMATION:
{context}

QUERY:
{query}

Provide a thorough answer that synthesizes the relevant information. If the information is insufficient to fully answer the question, clearly state what's missing and provide the best possible answer based on what's available.
"""
            
            result = lmstudio_completion(
                prompt=prompt,
                max_tokens=1024,
                temperature=0.2
            )
            
            return f"LM STUDIO ENHANCED RAG SEARCH\nQuery: {query}\n{sources_info}\n\n{result.strip()}"
        else:
            # Return raw search results if not using enhancement
            return f"RAW SEARCH RESULTS\nQuery: {query}\n{sources_info}\n\nContext found:\n{context}"
            
    except Exception as e:
        return f"Error in enhanced RAG search: {str(e)}"

@mcp.tool()
def hybrid_search_and_generate(query: str, search_limit: int = 5) -> str:
    """
    Combines your existing vector search with LM Studio generation.
    This is the COMBINATION OF YOUR STRENGTHS + LM STUDIO AI.
    USES YOUR LM STUDIO INSTANCE ON PORT 1234 FOR BOTH EMBEDDINGS AND GENERATION
    
    Args:
        query: What to search for and generate about
        search_limit: How many initial results to retrieve from each source
    
    Returns:
        AI-generated answer grounded in your data from LanceDB and DuckDB
    """
    try:
        # STEP 1: Your existing strength - vector search using LM Studio embeddings
        query_vector = lmstudio_embedding(query)
        
        context_parts = []
        sources_searched = []
        
        # Search LanceDB
        try:
            db = get_lancedb_connection()
            table_names = db.table_names()
            if table_names:
                for table_name in table_names[:3]:  # Limit to first 3 tables
                    try:
                        table = db.open_table(table_name)
                        results = table.search(query_vector).limit(search_limit).to_pandas()
                        if not results.empty:
                            for _, row in results.iterrows():
                                content = str(row.get('content', row.get('code', str(row))))[:400]
                                context_parts.append(content)
                                sources_searched.append(f"LanceDB:{table_name}")
                    except Exception as e:
                        log.warning(f"Could not search LanceDB table {table_name}: {e}")
        except Exception as e:
            log.warning(f"LanceDB search warning: {e}")
        
        # Search DuckDB 
        try:
            conn = get_duckdb_connection()
            tables = conn.execute("SHOW TABLES").fetchall()
            for table_tuple in tables[:2]:  # Limit to first 2 tables
                table_name = table_tuple[0]
                try:
                    # Simple search in DuckDB
                    results = conn.execute(
                        f"SELECT * FROM {table_name} LIMIT {search_limit}"
                    ).fetchall()
                    if results:
                        for row in results:
                            content = str(row)[:400]
                            context_parts.append(content)
                            sources_searched.append(f"DuckDB:{table_name}")
                except Exception as e:
                    log.warning(f"Could not search DuckDB table {table_name}: {e}")
        except Exception as e:
            log.warning(f"DuckDB search warning: {e}")
        
        if not context_parts:
            return f"No context found in knowledge bases for query: {query}"
        
        # Prepare context for LM Studio
        context = "\n\n---\n\n".join(context_parts)
        sources_info = f"Sources searched: {', '.join(sources_searched)}"
        
        # STEP 2: Use LM Studio to generate final answer from the retrieved context
        prompt = f"""You are an expert technical assistant with access to a specialized knowledge base containing code, documentation, and technical information.

KNOWLEDGE BASE INFORMATION:
{context}

USER QUERY:
{query}

Provide a thorough, accurate answer that synthesizes the relevant information from the knowledge base. 
If the information is insufficient to fully answer the question, clearly state what information is missing and provide the best possible answer based on what's available.
"""
        
        result = lmstudio_completion(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.2
        )
        
        return f"HYBRID SEARCH & GENERATION\nQuery: {query}\n{sources_info}\n\n{result.strip()}"
        
    except Exception as e:
        return f"Error in hybrid search and generate: {str(e)}"

@mcp.tool()
def lmstudio_improve_code(code: str, goal: str = "improve readability") -> str:
    """
    Improve/refactor code using LM Studio.
    USES YOUR LM STUDIO INSTANCE ON PORT 1234
    
    Args:
        code: Code to improve
        goal: What to optimize for (readability, performance, safety, etc.)
    
    Returns:
        Improved code from LM Studio
    """
    try:
        prompt = f"""You are an expert software engineer. Improve the following code to {goal}.

ORIGINAL CODE:
```python
{code}
```

IMPROVED CODE ({goal}):
```python
"""
        
        result = lmstudio_completion(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.1
        )
        
        # Extract just the code if wrapped in markdown
        if "```python" in result:
            start = result.find("```python") + 9
            end = result.find("```", start)
            if end != -1:
                return result[start:end].strip()
        
        return result.strip()
        
    except Exception as e:
        return f"Error improving code with LM Studio: {str(e)}"

@mcp.tool()
def lmstudio_design_architecture(requirements: str, context: str = "") -> str:
    """
    Use LM Studio to design software architecture or solutions.
    USES YOUR LM STUDIO INSTANCE ON PORT 1234
    
    Args:
        requirements: What the system or solution should accomplish
        context: Optional context from your knowledge bases
    
    Returns:
        Architecture design or solution proposal from LM Studio
    """
    try:
        # Get context if not provided
        if not context:
            context_result = lmstudio_rag_enhanced_search(f"architecture {requirements}", use_chain_of_thought=False)
            context = context_result
            
        prompt = f"""You are a senior software architect. Design a solution based on the following requirements and optionally incorporating relevant context from a knowledge base.

REQUIREMENTS:
{requirements}

CONTEXT FROM KNOWLEDGE BASE:
{context}

Provide:
1. High-level architecture overview
2. Key components, their responsibilities, and interactions
3. Data flow and control flow descriptions
4. Technology stack recommendations (if applicable)
5. Key considerations and potential challenges
6. Implementation approach or roadmap

ARCHITECTURE DESIGN:
"""
        
        result = lmstudio_completion(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.3
        )
        
        return result.strip()
        
    except Exception as e:
        return f"Error in design generation with LM Studio: {str(e)}"

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
        test_embedding = lmstudio_embedding("test connection")
        log.info(f"LM Studio connection successful. Embedding dimension: {len(test_embedding)}")
        
        test_completion = lmstudio_completion("Say 'hello' in one word:", max_tokens=10)
        log.info(f"LM Studio completion test: {test_completion.strip()}")
        
    except Exception as e:
        log.error(f"Failed to connect to LM Studio: {e}")
        log.error("Make sure LM Studio is running with local server started (Developer -> Start Local Server)")
        log.error("And ensure you have the nvidia/nemotron-3-nano-4b model loaded")
        # Don't exit - let the server start anyway, connections will fail gracefully
    
    # Run the server
    try:
        mcp.run()
    except KeyboardInterrupt:
        log.info("Server shutting down...")
    except Exception as e:
        log.error(f"Server error: {e}")
        sys.exit(1)