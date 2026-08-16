"""
MONTY RAG CODER DEMO
A demonstration of the coding assistant that works with your RAG v2 setup
"""

import os
import json
from openai import OpenAI

# ==============================================================================
# CONFIGURATION
# ==============================================================================
# Connect to your LM Studio instance
LM_STUDIO_URL = "http://127.0.0.1:1234/v1"
client = OpenAI(base_url=LM_STUDIO_URL, api_key="lm-studio")
LLM_MODEL = "nvidia/nemotron-3-nano-4b"  # Adjust based on your loaded model

# Your workspace
WORKSPACE_ROOT = r"C:\WEB CASE STUDY"

# ==============================================================================
# CORE FUNCTIONALITY
# ==============================================================================

def chat_with_context(prompt: str) -> str:
    """
    Send a prompt to your LM Studio instance.
    Your RAG/prompt/memory plugins will automatically provide context.
    """
    print(f"\n🤖 Sending request to LM Studio ({LLM_MODEL})...")
    
    # System message that works with your RAG setup
    system_message = """You are an expert software engineer and coding assistant.
    
You have access to a Retrieval-Augmented Generation (RAG) system that provides:
- Context from the user's codebase and documentation
- Conversation memory for continuity
- Custom prompts that define your behavior and role

Your capabilities include:
- Writing, reviewing, and debugging code
- Explaining technical concepts
- Helping with architecture and design decisions
- Working within the user's specified workspace

When writing code:
1. Follow best practices and the user's coding style
2. Include appropriate comments and documentation
3. Consider error handling and edge cases
4. Ensure code is secure and efficient
5. Place files in appropriate locations within the workspace

Always leverage your RAG context to provide accurate, relevant assistance."""

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.2,  # Low temperature for consistent code generation
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error communicating with LM Studio: {str(e)}"

def write_code_to_file(filename: str, code: str) -> dict:
    """Write code to a file in the workspace."""
    try:
        # Ensure we're within the workspace for safety
        filepath = os.path.join(WORKSPACE_ROOT, filename)
        
        # Prevent directory traversal attacks
        if not os.path.abspath(filepath).startswith(os.path.abspath(WORKSPACE_ROOT)):
            return {"status": "error", "message": "Access denied: File must be within workspace"}
        
        # Create directory if needed
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Write the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
        
        return {
            "status": "success", 
            "message": f"File written successfully: {filepath}",
            "filepath": filepath
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to write file: {str(e)}"}

def run_demo():
    """Run a demonstration of the coder's capabilities."""
    print("=" * 70)
    print("🎯 MONTY RAG CODER - Demonstration")
    print("=" * 70)
    
    # Test connection first
    try:
        test_response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print("✅ Successfully connected to LM Studio")
    except Exception as e:
        print(f"❌ Failed to connect to LM Studio at {LM_STUDIO_URL}")
        print(f"   Error: {str(e)}")
        print("   Please ensure LM Studio is running with local server started")
        return
    
    demo_prompt = """Create a Python script that:
1. Connects to a DuckDB database at C:\STUDIES\data\metadata\sonic_core.duckdb
2. Lists all tables in the database
3. For each table, shows the schema and row count
4. Handles potential errors gracefully
5. Includes proper documentation and comments

Make sure to use the duckdb library and follow Python best practices."""

    print(f"\n📝 Demo Prompt:")
    print(demo_prompt)
    print("\n" + "="*50)
    print("🤖 Generating response...")
    
    response = chat_with_context(demo_prompt)
    
    print(f"🤖 Response:\n{response}")
    print("="*50)
    
    # Save the response to a file
    filename = "duckdb_explorer.py"
    result = write_code_to_file(filename, response)
    
    if result["status"] == "success":
        print(f"✅ {result['message']}")
        print(f"\n📁 You can find the generated script at: {result['filepath']}")
        print(f"💡 To run it: python {result['filepath']}")
    else:
        print(f"❌ {result['message']}")

if __name__ == "__main__":
    run_demo()