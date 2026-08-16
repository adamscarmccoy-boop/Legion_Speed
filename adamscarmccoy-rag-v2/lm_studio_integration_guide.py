"""
LM STUDIO INTEGRATION GUIDE FOR YOUR EXISTING RAG v2 SYSTEM
===========================================================

YOUR SYSTEM ALREADY USES LM STUDIO ON PORT 1234 FOR EMBEDDINGS:
- In mcp_rag_server.py: _server.py: Line ~140 uses _embed_snowflake() 
- Which calls: http://127.0.0.1:1234/v1/embeddings
- With model: "text-embedding-snowflake-arctic-embed-l-v2.0"

YOU CAN EXTEND THIS TO USE LM STUDIO FOR TEXT GENERATION TOO:
Add this to ANY of your MCP servers (mcp_rag_server.py or mcp_swarm_gateway_v2.py)

HOW TO ADD TEXT GENERATION CAPABILITY:

1. ADD THIS FUNCTION TO YOUR MCP SERVER:
"""

def _generate_text_lmstudio(prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
    """Generate text using LM Studio's completion endpoint."""
    import requests
    import json
    
    payload = {
        "model": "nvidia/nemotron-3-nano-4b",  # YOUR LOADED MODEL
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:1234/v1/completions",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["text"]
    except Exception as e:
        return f"LM Studio generation error: {str(e)}"

2. ADD THIS TOOL TO YOUR MCP SERVER (using @mcp.tool() decorator):

@mcp.tool()
def generate_code_with_context(prompt: str, context_snippets: str = "") -> str:
    """
    Generate code using LM Studio with optional RAG context.
    Uses your existing embedding search + LM Studio generation.
    """
    # Use your existing semantic search to get context
    context = semantic_code_search(prompt, limit=3) if not context_snippets else context_snippets
    
    # Build enhanced prompt
    full_prompt = f"""You are an expert programmer. Use the following code context to inform your response:

{context}

USER REQUEST: {prompt}

Provide a complete, working solution. Include necessary imports and comments."""

    # Generate using LM Studio
    return _generate_text_lmstudio(full_prompt, max_tokens=1024, temperature=0.2)

3. OR ADD A PURE GENERATION TOOL:

@mcp.tool()
def lmstudio_generate(prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
    """
    Direct text generation using your loaded LM Studio model.
    Model: nvidia/nemotron-3-nano-4b (as seen in your logs)
    """
    return _generate_text_lmstudio(prompt, max_tokens, temperature)

KEY POINTS:
- Uses EXISTING infrastructure: http://127.0.0.1:1234/v1/completions
- Leverages YOUR loaded model: nvidia/nemotron-3-nano-4b
- Works alongside your existing embedding calls
- No new servers needed - extends what you already have
- Can be added to either mcp_rag_server.py OR mcp_swarm_gateway_v2.py

USAGE EXAMPLES FROM LM STUDIO CHAT:
1. "Use generate_code_with_context to create a DuckDB query for audio file metadata"
2. "Use lmstudio_generate to explain how this FFT algorithm works"
3. "Use generate_code_with_context to write a Ray task that processes audio chunks"

YOUR SYSTEM IS ALREADY 90% THERE - JUST ADD THE GENERATION LAYER!