"""
LM STUDIO DIRECT INTEGRATION
============================

A simplified approach that makes LM Studio (port 1234) the central AI engine,
building on your existing working setup where LM Studio is already providing 
embeddings via http://127.0.0.1:1234/v1/embeddings

This eliminates unnecessary complexity and makes everything flow through 
your existing LM Studio instance.
"""

import os
import sys
import json
import logging
import requests
import subprocess
from typing import List, Dict, Any, Optional

# Configure logging to stderr to protect any potential stdio usage
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("LMStudioDirect")

# ============================================================================
# CONFIGURATION - BUILDING ON YOUR WORKING SETUP
# ============================================================================

# YOUR LM STUDIO INSTANCE - THIS IS ALREADY WORKING
LM_STUDIO_HOST = os.getenv("LM_STUDIO_HOST", "http://127.0.0.1:1234")
LM_STUDIO_EMBEDDING_MODEL = os.getenv("LM_STUDIO_EMBEDDING_MODEL", "text-embedding-snowflake-arctic-embed-l-v2.0")
LM_STUDIO_LLM_MODEL = os.getenv("LM_STUDIO_LLM_MODEL", "nvidia/nemotron-3-nano-4b")  # YOUR LOADED MODEL

# YOUR EXISTING DATA PATHS - KEEP THESE AS THEY'RE VALUABLE
LANCEDB_PATH = os.getenv(
    "LANCEDB_PATH",
    r"C:\STUDIES_BACKUP\vectors\lancedb_store"
)
DUCKDB_PATH = os.getenv(
    "DUCKDB_PATH", 
    r"C:\STUDIES\data\metadata\sonic_core.duckdb"
)

# ============================================================================
# LM STUDIO HELPER FUNCTIONS - USING YOUR WORKING ENDPOINTS
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
                       0.2,
                       stop: Optional[List[str]] = None) -> str:
    """Get text completion from LM Studio - THE MISSING PIECE YOU WANTED"""
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
# CORE FUNCTIONALITY - LEVERAGING YOUR EXISTING STRENGTHS
# ============================================================================

def get_lancedb_connection():
    """Get LanceDB connection - keeping your valuable vector search"""
    try:
        import lancedb
        return lancedb.connect(LANCEDB_PATH)
    except ImportError:
        raise Exception("LanceDB not installed. Install with: pip install lancedb")
    except Exception as e:
        log.error(f"Failed to connect to LanceDB at {LANCEDB_PATH}: {e}")
        raise

def get_duckdb_connection():
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
# SIMPLE, DIRECT TOOLS - EVERYTHING FLOWS THROUGH LM STUDIO
# ============================================================================

def lmstudio_generate_code(prompt: str, context: str = "", max_tokens: int = 1024) -> str:
    """
    Generate code using LM Studio with optional context.
    DIRECT LM STUDIO CALL - NO MIDDLEWARE
    """
    try:
        # Build prompt with context
        full_prompt = f"""You are an expert programmer. Generate clean, working code.

CONTEXT:
{context}

TASK:
{prompt}

WRITE ONLY THE CODE - NO EXTRA TEXT UNLESS SPECIFICALLY REQUESTED.
"""
        
        result = lmstudio_completion(
            prompt=full_prompt,
            max_tokens=max_tokens,
            temperature=0.1  # Low temperature for code
        )
        
        return result.strip()
        
    except Exception as e:
        return f"Error generating code: {str(e)}"

def lmstudio_explain_code(code: str, detail_level: str = "medium") -> str:
    """
    Explain code using LM Studio.
    DIRECT LM STUDIO CALL
    """
    try:
        detail_prompts = {
            "brief": "Briefly explain what this code does:",
            "medium": "Explain what this code does, how it works, and its purpose:",
            "detailed": "Explain this code in detail including purpose, algorithm, inputs/outputs, complexity, and edge cases:"
        }
        
        prompt = f"""{detail_prompts.get(detail_level, detail_prompts["medium"])}

CODE:
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
        return f"Error explaining code: {str(e)}"

def lmstudio_debug_error(error_message: str, code_context: str = "") -> str:
    """
    Debug errors using LM Studio.
    DIRECT LM STUDIO CALL
    """
    try:
        prompt = f"""You are an expert debugging assistant. Analyze this error and provide solutions.

ERROR:
{error_message}

CODE CONTEXT:
{code_context}

Provide:
1. Likely cause
2. Specific fix steps
3. Code example of fix
4. Prevention tips

DEBUGGING ANALYSIS:
"""
        
        result = lmstudio_completion(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.2
        )
        
        return result.strip()
        
    except Exception as e:
        return f"Error in debugging: {str(e)}"

def lmstudio_ask_anything(question: str, context: str = "") -> str:
    """
    Ask LM Studio any question - with optional context from your knowledge bases.
    THIS IS THE CORE OF YOUR REQUEST - EVERYTHING THROUGH LM STUDIO 1234
    """
    try:
        # Build prompt with context
        if context:
            full_prompt = f"""Context information:
{context}

Question: {question}

Answer:"""
        else:
            full_prompt = f"""Question: {question}

Answer:"""
        
        result = lmstudio_completion(
            prompt=full_prompt,
            max_tokens=1024,
            temperature=0.3
        )
        
        return result.strip()
        
    except Exception as e:
        return f"Error asking question: {str(e)}"

def lmstudio_rag_search_and_answer(query: str) -> str:
    """
    Combines your existing vector search (LanceDB/DuckDB) with LM Studio reasoning.
    1. Use your existing embedding search to get relevant context
    2. Send that context + question to LM Studio for answer generation
    """
    try:
        # STEP 1: Get relevant context from your knowledge bases using YOUR WORKING EMBEDDINGS
        query_vector = lmstudio_embedding(query)
        
        context_parts = []
        
        # Search LanceDB
        try:
            db = get_lancedb_connection()
            table_names = db.table_names()
            if table_names:
                # Search first table or specify which one
                table = db.open_table(table_names[0])
                results = table.search(query_vector).limit(5).to_pandas()
                if not results.empty:
                    for _, row in results.iterrows():
                        # Extract text content - adjust based on your schema
                        content = str(row.get('content', row.get('code', str(row))))[:300]
                        context_parts.append(content)
        except Exception as e:
            log.warning(f"LanceDB search warning: {e}")
        
        # Search DuckDB (optional - only if you want to include it)
        try:
            # This would be a simple text search in DuckDB for now
            # You could enhance this with vector search in DuckDB too
            pass
        except Exception as e:
            log.warning(f"DuckDB search warning: {e}")
        
        # STEP 2: Send context + question to LM Studio for final answer
        context = "\n\n---\n\n".join(context_parts) if context_parts else "No specific context found."
        
        prompt = f"""Based on the following information, answer the question accurately and helpfully.

INFORMATION:
{context}

QUESTION:
{question}

ANSWER:
"""
        
        result = lmstudio_completion(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.2
        )
        
        return result.strip()
        
    except Exception as e:
        return f"Error in RAG search and answer: {str(e)}"

def lmstudio_improve_code(code: str, goal: str = "improve readability") -> str:
    """
    Improve/refactor code using LM Studio.
    DIRECT LM STUDIO CALL
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
        return f"Error improving code: {str(e)}"

# ============================================================================
# SIMPLE INTERFACE FOR TESTING
# ============================================================================

def test_connections():
    """Test that your LM Studio instance is working"""
    print("🔌 Testing LM Studio connection...")
    try:
        # Test embedding (you know this works)
        test_emb = lmstudio_embedding("test")
        print(f"✅ Embedding works. Dimension: {len(test_emb)}")
        
        # Test completion (this is what you wanted to add)
        test_comp = lmstudio_completion("Say 'hello'", max_tokens=10)
        print(f"✅ Completion works: '{test_comp.strip()}'")
        
        return True
    except Exception as e:
        print(f"❌ LM Studio connection failed: {e}")
        print("Make sure:")
        print("  1. LM Studio is running")
        print("  2. Local server is started (Developer -> Start Local Server)")  
        print("  3. Model nvidia/nemotron-3-nano-4b is loaded")
        print("  4. You're accessing http://127.0.0.1:1234")
        return False

def interactive_mode():
    """Simple interactive mode to test the direct LM Studio integration"""
    print("\n" + "="*50)
    print("🚀 LM STUDIO DIRECT INTEGRATION - TEST MODE")
    print("="*50)
    
    if not test_connections():
        return
    
    print("\n💡 Available test functions:")
    print("  1. lmstudio_ask_anything(\"your question\")")
    print("  2. lmstudio_generate_code(\"write a python function to...\")")
    print("  3. lmstudio_explain_code(\"your code here\")")
    print("  4. lmstudio_debug_error(\"error message\")")
    print("  5. lmstudio_improve_code(\"your code\")")
    print("  6. lmstudio_rag_search_and_answer(\"your question\")")
    print("\n💡 Example: lmstudio_ask_anything(\"What is the capital of France?\")")
    print("💡 Type 'quit' to exit\n")
    
    while True:
        try:
            user_input = input("💬 Enter command or question: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not user_input:
                continue
                
            # Try to parse as function call
            if user_input.startswith('lmstudio_'):
                try:
                    # Simple parsing - in reality you'd want a proper parser
                    if '(' in user_input and user_input.endswith(')'):
                        func_name = user_input[:user_input.find('(')]
                        args_str = user_input[user_input.find('(')+1:-1]
                        
                        # Remove quotes if present
                        if args_str.startswith('"') and args_str.endswith('"'):
                            args_str = args_str[1:-1]
                        elif args_str.startswith("'") and args_str.endswith("'"):
                            args_str = args_str[1:-1]
                        
                        # Call the function
                        if func_name == "lmstudio_ask_anything":
                            result = lmstudio_ask_anything(args_str)
                        elif func_name == "lmstudio_generate_code":
                            result = lmstudio_generate_code(args_str)
                        elif func_name == "lmstudio_explain_code":
                            result = lmstudio_explain_code(args_str)
                        elif func_name == "lmstudio_debug_error":
                            result = lmstudio_debug_error(args_str)
                        elif func_name == "lmstudio_improve_code":
                            result = lmstudio_improve_code(args_str)
                        elif func_name == "lmstudio_rag_search_and_answer":
                            result = lmstudio_rag_search_and_answer(args_str)
                        else:
                            result = f"Unknown function: {func_name}"
                            
                        print(f"\n🤖 Result:\n{result}\n")
                    else:
                        # Treat as general question
                        result = lmstudio_ask_anything(user_input)
                        print(f"\n🤖 Result:\n{result}\n")
                except Exception as e:
                    print(f"❌ Error parsing command: {e}")
                    # Fall back to treating as general question
                    result = lmstudio_ask_anything(user_input)
                    print(f"\n🤖 Result:\n{result}\n")
            else:
                # Treat general input as a question
                result = lmstudio_ask_anything(user_input)
                print(f"\n🤖 Result:\n{result}\n")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            print("\n👋 Goodbye!")
            break

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("🚀 LM Studio Direct Integration")
    print("🔗 Everything flows through your existing LM Studio instance on port 1234")
    print("📝 Uses your working embedding endpoint + adds text generation")
    print("")
    
    # Test connection first
    if test_connections():
        print("\n✅ Ready to use LM Studio directly!")
        print("💡 Run interactive_mode() to test the functions")
        print("💡 Or import and use the functions in your own code")
    else:
        print("\n❌ Please fix LM Studio connection before proceeding")
        sys.exit(1)