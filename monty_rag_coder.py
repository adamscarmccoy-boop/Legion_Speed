"""
MONTY RAG CODER
A coding assistant that works with your existing RAG v2 setup (prompt/memory plugins)
"""

import os
import json
import sys
from datetime import datetime
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

def chat_with_llm(prompt: str, system_override: str = None) -> str:
    """
    Send a prompt to your LM Studio instance.
    Your RAG v2 plugins (prompt/memory) will automatically provide context.
    """
    # Default system message that works with RAG setup
    system_message = system_override or """You are an expert software engineer and coding assistant.

You have access to a Retrieval-Augmented Generation (RAG) system that provides:
- Context from the user's codebase and documentation
- Conversation memory for continuity
- Custom prompts that define your behavior and role

Your capabilities include:
- Writing, reviewing, and debugging code in multiple languages
- Explaining technical concepts and architectures
- Helping with design decisions and best practices
- Working within the user's specified workspace
- Assisting with debugging and troubleshooting

When working with code:
1. Follow best practices and the user's coding style
2. Include appropriate comments and documentation
3. Consider error handling, edge cases, and security
4. Ensure code is efficient and maintainable
5. Place files in appropriate locations within the workspace
6. Explain your reasoning and approach

Always leverage your RAG context to provide accurate, relevant assistance."""

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.2,  # Low temperature for consistent, focused responses
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

def read_file(filename: str) -> dict:
    """Read a file from the workspace."""
    try:
        filepath = os.path.join(WORKSPACE_ROOT, filename)
        if not os.path.abspath(filepath).startswith(os.path.abspath(WORKSPACE_ROOT)):
            return {"status": "error", "message": "Access denied: File must be within workspace"}
        
        if not os.path.exists(filepath):
            return {"status": "error", "message": f"File not found: {filepath}"}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "status": "success",
            "content": content,
            "filepath": filepath
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to read file: {str(e)}"}

def list_files(directory: str = "") -> dict:
    """List files in a directory within the workspace."""
    try:
        target_dir = os.path.join(WORKSPACE_ROOT, directory) if directory else WORKSPACE_ROOT
        if not os.path.abspath(target_dir).startswith(os.path.abspath(WORKSPACE_ROOT)):
            return {"status": "error", "message": "Access denied: Directory must be within workspace"}
        
        if not os.path.exists(target_dir):
            return {"status": "error", "message": f"Directory not found: {target_dir}"}
        
        files = []
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            if os.path.isfile(item_path):
                stat = os.stat(item_path)
                files.append({
                    "name": item,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "type": "file"
                })
            elif os.path.isdir(item_path):
                files.append({
                    "name": item,
                    "size": 0,
                    "modified": datetime.fromtimestamp(os.path.getmtime(item_path)).isoformat(),
                    "type": "directory"
                })
        
        # Sort: directories first, then files, both alphabetically
        files.sort(key=lambda x: (x["type"] == "file", x["name"].lower()))
        
        return {
            "status": "success",
            "directory": os.path.relpath(target_dir, WORKSPACE_ROOT),
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to list directory: {str(e)}"}

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def extract_code_from_response(response: str) -> str:
    """Extract code blocks from AI response if present."""
    # Look for code blocks marked with ```language or ```
    import re
    
    # Pattern to match code blocks
    pattern = r'```(?:\w+)?\n(.*?)\n```'
    matches = re.findall(pattern, response, re.DOTALL)
    
    if matches:
        # Return the largest code block (likely the main code)
        return max(matches, key=len).strip()
    
    # If no code blocks found, return the whole response (might be pure code)
    return response.strip()

def is_code_request(message: str) -> bool:
    """Check if the user's message is likely asking for code generation."""
    code_indicators = [
        'write', 'create', 'make', 'build', 'implement', 'code',
        'function', 'class', 'script', 'program', 'algorithm',
        'python', 'javascript', 'java', 'cpp', 'c++', 'html', 'css',
        'sql', 'api', 'website', 'app', 'software'
    ]
    
    message_lower = message.lower()
    return any(indicator in message_lower for indicator in code_indicators)

# ==============================================================================
# MAIN INTERFACE
# ==============================================================================

def interactive_mode():
    """Run an interactive coding session."""
    print("=" * 70)
    print("🤖 MONTY RAG CODER")
    print("🔗 Working with your existing RAG v2 setup")
    print("=" * 70)
    print(f"📡 Connected to: {LM_STUDIO_URL}")
    print(f"🧠 Model: {LLM_MODEL}")
    print(f"💾 Workspace: {WORKSPACE_ROOT}")
    print("💡 Your RAG v2 plugins provide context/prompt/memory automatically")
    print("📝 Special commands:")
    print("   /help  - Show help")
    print("   /ls    - List files in current directory")
    print("   /cd <dir> - Change directory (relative to workspace)")
    print("   /pwd   - Show current directory")
    print("   /read <file> - Read and display file contents")
    print("   /write <file> <code> - Write code to file")
    print("   /exit  - Exit the program")
    print("-" * 70)
    
    current_dir = ""
    
    while True:
        try:
            # Show prompt
            prompt_indicator = f"[{os.path.relpath(os.path.join(WORKSPACE_ROOT, current_dir), WORKSPACE_ROOT) or '.'}]> "
            user_input = input(f"\n💬 You: {prompt_indicator}").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith('/'):
                cmd_parts = user_input[1:].split(' ', 1)
                command = cmd_parts[0].lower()
                args = cmd_parts[1] if len(cmd_parts) > 1 else ""
                
                if command == 'exit' or command == 'quit':
                    print("\n👋 Goodbye!")
                    break
                    
                elif command == 'help':
                    print("\n📚 Available Commands:")
                    print("   /help      - Show this help")
                    print("   /ls        - List files in current directory")
                    print("   /cd <dir>  - Change directory (relative to workspace)")
                    print("   /pwd       - Show current directory")
                    print("   /read <file> - Read and display file contents")
                    print("   /write <file> <code> - Write code to file")
                    print("   /exit      - Exit the program")
                    print("")
                    print("💡 Tips:")
                    print("   - Just ask naturally for code help, explanations, etc.")
                    print("   - If response contains code, you'll be prompted to save it")
                    print("   - Your RAG v2 system provides context automatically")
                    
                elif command == 'ls':
                    result = list_files(current_dir)
                    if result["status"] == "success":
                        print(f"\n📁 Contents of '{result['directory'] or '.'}':")
                        for item in result["files"]:
                            icon = "📁" if item["type"] == "directory" else "📄"
                            size_str = f"{item['size']} B" if item["size"] < 1024 else f"{item['size']/1024:.1f} KB"
                            print(f"   {icon} {item['name']:<30} {size_str:>8} {item['modified']}")
                    else:
                        print(f"❌ {result['message']}")
                        
                elif command == 'pwd':
                    print(f"\n📍 Current directory: {current_dir or '.'}")
                    
                elif command == 'cd':
                    if not args:
                        print("❌ Usage: /cd <directory>")
                        continue
                    new_dir = os.path.join(current_dir, args) if current_dir else args
                    # Simple validation - in a real app, you'd check if directory exists
                    current_dir = new_dir
                    print(f"\n📂 Changed directory to: {current_dir or '.'}")
                    
                elif command == 'read':
                    if not args:
                        print("❌ Usage: /read <filename>")
                        continue
                    result = read_file(args)
                    if result["status"] == "success":
                        print(f"\n📄 Contents of '{result['filepath']}':")
                        print("-" * 50)
                        print(result["content"])
                        print("-" * 50)
                    else:
                        print(f"❌ {result['message']}")
                        
                elif command == 'write':
                    if not args:
                        print("❌ Usage: /write <filename> <code>")
                        print("   Example: /write hello.py print('Hello, World!')")
                        continue
                    
                    # Split into filename and code
                    parts = args.split(' ', 1)
                    if len(parts) < 2:
                        print("❌ Usage: /write <filename> <code>")
                        continue
                    
                    filename, code = parts
                    result = write_code_to_file(filename, code)
                    if result["status"] == "success":
                        print(f"✅ {result['message']}")
                    else:
                        print(f"❌ {result['message']}")
                
                else:
                    print(f"❌ Unknown command: {command}. Type /help for available commands.")
            
            else:
                # Treat as a natural language request
                print("\n🤔 Thinking with your RAG context...")
                response = chat_with_llm(user_input)
                print(f"\n🤖 Assistant:\n{response}")

                # Check if response likely contains code and offer to save
                if is_code_request(user_input) or ('```' in response and ('python' in response.lower() or 'def ' in response or 'class ' in response)):
                    print("\n💾 The response appears to contain code. Would you like to save it to a file?")
                    save_choice = input("Enter filename to save (or press Enter to skip): ").strip()
                    if save_choice:
                        # Extract code if possible, otherwise save whole response
                        code_to_save = extract_code_from_response(response)
                        result = write_code_to_file(save_choice, code_to_save)
                        if result["status"] == "success":
                            print(f"✅ {result['message']}")
                        else:
                            print(f"❌ {result['message']}")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except EOFError:
            print("\n👋 End of input. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")

def demo_mode():
    """Run a demonstration of the coder's capabilities."""
    print("=" * 70)
    print("🚀 MONTY RAG CODER - DEMONSTRATION MODE")
    print("=" * 70)

    demo_prompts = [
        "Create a simple Python script that reads a CSV file and prints basic statistics",
        "Explain the difference between supervised and unsupervised learning in machine learning",
        "Write a JavaScript function that validates an email address using regex",
        "Create a basic HTML template for a responsive landing page",
        "How would you implement a REST API endpoint for user authentication in Python Flask?"
    ]

    print("💡 Example prompts you could try:")
    for i, prompt in enumerate(demo_prompts, 1):
        print(f"   {i}. {prompt}")
    print()

    # Run a sample demonstration
    print("🎯 Running sample demonstration...")
    sample_prompt = "Create a Python class for a simple TODO list application with methods to add, remove, and list tasks"
    print(f"\n📝 Prompt: {sample_prompt}")
    print("\n🤖 Generating response with your RAG context...")

    response = chat_with_llm(sample_prompt)
    print(f"\n🤖 Response:\n{response}")

    # Offer to save the demo code
    print("\n💾 Would you like to save this code to a file?")
    save_choice = input("Enter filename (e.g., todo.py) or press Enter to skip: ").strip()
    if save_choice:
        code_to_save = extract_code_from_response(response)
        result = write_code_to_file(save_choice, code_to_save)
        if result["status"] == "success":
            print(f"✅ {result['message']}")
            print(f"📁 File saved to: {result['filepath']}")
        else:
            print(f"❌ {result['message']}")

def main():
    """Main entry point."""
    # Test connection to LM Studio
    print("🔌 Testing connection to LM Studio...")
    try:
        test_response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": "Say 'hello'"}],
            max_tokens=10
        )
        print("✅ Successfully connected to LM Studio")
    except Exception as e:
        print(f"❌ Failed to connect to LM Studio at {LM_STUDIO_URL}")
        print("   Please ensure:")
        print("   1. LM Studio is running")
        print("   2. Local server is started (Developer → Start Local Server)")
        print("   3. A model is loaded")
        print("   4. You're using the correct port (default: 1234)")
        print(f"   Error: {str(e)}")
        return

    # Choose mode
    print("\n🎯 Select mode:")
    print("   1. Interactive mode (recommended)")
    print("   2. Demonstration mode")
    print("   3. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            interactive_mode()
            break
        elif choice == "2":
            demo_mode()
            break
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()