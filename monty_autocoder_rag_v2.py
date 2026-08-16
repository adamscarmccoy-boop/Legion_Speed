"""
MONTY AUTOCODER RAG v2
Designed to work with existing RAG/prompt/memory plugins
"""

import os
import json
import time
import socket
import subprocess
from openai import OpenAI

# ==============================================================================
# CONFIGURATION
# ==============================================================================
# Connect to your LM Studio instance (the local server)
LM_STUDIO_URL = "http://127.0.0.1:1234/v1"
client = OpenAI(base_url=LM_STUDIO_URL, api_key="lm-studio")
LLM_MODEL = "nvidia/nemotron-3-nano-4b"  # Adjust to match your loaded model

# Your workspace and data paths
WORKSPACE_ROOT = r"C:\WEB CASE STUDY"
STUDIES_DIR = r"C:\STUDIES"
LANCEDB_PATH = r"C:\STUDIES_BACKUP\vectors\lancedb_store"
DUCKDB_PATH = r"C:\STUDIES\data\metadata\sonic_core.duckdb"

# Ports to monitor (from your Legion docs)
TARGET_PORTS = [1234, 1010, 6379, 8000, 8001, 8005, 8265]

# ==============================================================================
# CORE FUNCTIONALITY
# ==============================================================================

def query_llm(prompt: str, context: str = "") -> str:
    """
    Query the LLM with optional context from your RAG system.
    Your RAG/prompt/memory plugins will handle context injection.
    """
    try:
        # In a real RAG setup, your plugins would prepend context here
        # For now, we'll send the prompt directly and let your plugins handle enrichment
        messages = [
            {"role": "system", "content": "You are a helpful AI coding assistant working within a RAG-enhanced environment. Your responses should be accurate, helpful, and leverage any available context from the RAG system."},
            {"role": "user", "content": prompt}
        ]
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error querying LLM: {str(e)}"

def safe_write_file(filename: str, content: str) -> dict:
    """Safely write content to a file within the workspace."""
    try:
        # Security: Ensure file is within workspace
        filepath = os.path.join(WORKSPACE_ROOT, filename)
        if not os.path.abspath(filepath).startswith(os.path.abspath(WORKSPACE_ROOT)):
            return {"status": "error", "message": "Access denied: File must be within workspace"}
        
        # Create directory if needed
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Write file
        with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(content)
        
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
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return {
            "status": "success",
            "content": content,
            "filepath": filepath
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to read file: {str(e)}"}

def discover_files(extensions: list = None, limit: int = 50) -> dict:
    """Discover files in the workspace and related directories."""
    try:
        if extensions is None:
            extensions = [".py", ".md", ".txt", ".json", ".duckdb", ".lance", ".onnx", ".py", ".yaml", ".yml"]
        
        found_files = []
        
        # Search in workspace
        for root, dirs, files in os.walk(WORKSPACE_ROOT):
            # Skip common noise directories
            dirs[:] = [d for d in dirs if d.lower() not in ['.git', '__pycache__', 'node_modules', '.venv']]
            
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    full_path = os.path.join(root, file)
                    try:
                        stat = os.stat(full_path)
                        rel_path = os.path.relpath(full_path, WORKSPACE_ROOT)
                        found_files.append({
                            "name": file,
                            "relative_path": rel_path,
                            "absolute_path": full_path,
                            "size": stat.st_size,
                            "modified": str(stat.st_mtime)
                        })
                    except:
                        pass  # Skip files we can't stat
        
        # Also check studies directory
        if os.path.exists(STUDIES_DIR):
            for root, dirs, files in os.walk(STUDIES_DIR):
                dirs[:] = [d for d in dirs if d.lower() not in ['.git', '__pycache__', 'node_modules', '.venv']]
                
                for file in files:
                    if any(file.lower().endswith(ext) for ext in extensions):
                        full_path = os.path.join(root, file)
                        try:
                            stat = os.stat(full_path)
                            rel_path = os.path.relpath(full_path, WORKSPACE_ROOT)
                            found_files.append({
                                "name": file,
                                "relative_path": rel_path,
                                "absolute_path": full_path,
                                "size": stat.st_size,
                                "modified": str(stat.st_mtime)
                            })
                        except:
                            pass
        
        # Limit results to prevent context overflow
        found_files = found_files = sorted(found_files, key=lambda x: x['modified'], reverse=True)[:limit]
        
        return {
            "status": "success",
            "files": found_files,
            "count": len(found_files),
            "searched_paths": [WORKSPACE_ROOT, STUDIES_DIR if os.path.exists(STUDIES_DIR) else ""]
        }
    except Exception as e:
        return {"status": "error", "message": f"File discovery failed: {str(e)}"}

def check_ports() -> dict:
    """Check status of target ports."""
    try:
        results = {}
        for port in TARGET_PORTS:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            results[port] = "open" if result == 0 else "closed"
        
        # Service mapping from your docs
        service_map = {
            1234: "LM Studio",
            1010: "LM Studio (Alternate)",
            6379: "Ray GCS",
            8000: "Ray Serve",
            8001: "MCP API Gateway",
            8005: "MCP RAG Control",
            8265: "Ray Dashboard"
        }
        
        service_status = []
        for port, status in results.items():
            service_name = service_map.get(port, f"Unknown-Port-{port}")
            service_status.append({
                "port": port,
                "service": service_name,
                "status": status
            })
        
        return {
            "status": "success",
            "port_status": results,
            "services": service_status,
            "open_ports": [p for p, s in results.items() if s == "open"]
        }
    except Exception as e:
        return {"status": "error", "message": f"Port check failed: {str(e)}"}

def get_system_info() -> dict:
    """Get basic system information."""
    try:
        import platform
        import psutil
        
        # Try to get RAM info
        memory = psutil.virtual_memory()
        
        return {
            "status": "success",
            "system": {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "ram_total_gb": round(memory.total / (1024**3), 2),
                "ram_available_gb": round(memory.available / (1024**3), 2),
                "ram_used_percent": memory.percent
            }
        }
    except ImportError:
        # Fallback if psutil not available
        import platform
        return {
            "status": "success",
            "system": {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor()
            },
            "note": "Install psutil for detailed memory info"
        }
    except Exception as e:
        return {"status": "error", "message": f"System info failed: {str(e)}"}

# ==============================================================================
# MAIN INTERFACE
# ==============================================================================

def main():
    """Main interactive loop."""
    print("=" * 60)
    print("🤖 MONTY AUTOCODER RAG v2")
    print("🔗 Designed to work with your RAG/prompt/memory plugins")
    print("=" * 60)
    
    # Test connection
    try:
        test_response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print("✅ Connected to LM Studio")
    except Exception as e:
        print(f"❌ Failed to connect to LM Studio: {e}")
        print("   Make sure:")
        print("   1. LM Studio is running")
        print("   2. Local server is started (Developer -> Start Local Server)")
        print("   3. A model is loaded")
        print("   4. You're using the correct port (default: 1234)")
        return
    
    print("\n💡 Available commands:")
    print("   • Ask me to write, explain, or debug code")
    print("   • 'files' - Discover files in workspace")
    print("   • 'ports' - Check service port status")
    print("   • 'system' - Get system information")
    print("   • 'help' - Show this help")
    print("   • 'quit' - Exit")
    print("\n💡 Your RAG/prompt/memory plugins will provide context automatically!")
    print("-" * 60)
    
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            elif user_input.lower() == 'help':
                print("\n💡 Available commands:")
                print("   • Ask me to write, explain, or debug code")
                print("   • 'files' - Discover files in workspace")
                print("   • 'ports' - Check service port status")
                print("   • 'system' - Get system information")
                print("   • 'help' - Show this help")
                print("   • 'quit' - Exit")
                
            elif user_input.lower() == 'files':
                print("\n🔍 Discovering files...")
                result = discover_files()
                if result["status"] == "success":
                    print(f"   Found {result['count']} files:")
                    for f in result['files'][:10]:  # Show first 10
                        print(f"   📄 {f['relative_path']} ({f['size']} bytes)")
                    if len(result['files']) > 10:
                        print(f"   ... and {len(result['files']) - 10} more")
                else:
                    print(f"   ❌ {result['message']}")
                    
            elif user_input.lower() == 'ports':
                print("\n🔌 Checking port status...")
                result = check_ports()
                if result["status"] == "success":
                    print("   Service Status:")
                    for svc in result['services']:
                        status_emoji = "🟢" if svc['status'] == 'open' else "🔴"
                        print(f"   {status_emoji} {svc['service']} (:{svc['port']}): {svc['status']}")
                else:
                    print(f"   ❌ {result['message']}")
                    
            elif user_input.lower() == 'system':
                print("\n💻 Getting system info...")
                result = get_system_info()
                if result["status"] == "success":
                    sys_info = result['system']
                    print("   System Information:")
                    for key, value in sys_info.items():
                        print(f"   • {key.replace('_', ' ').title()}: {value}")
                    if 'note' in result:
                        print(f"   ℹ️  Note: {result['note']}")
                else:
                    print(f"   ❌ {result['message']}")
                    
            else:
                # Treat as a general query/prompt
                print("\n🤔 Thinking...")
                response = query_llm(user_input)
                print(f"\n🤖 Assistant:\n{response}")
                
                # Offer to save code if it looks like code
                if any(keyword in response.lower() for keyword in ['def ', 'class ', 'import ', 'from ', '```python', '```']):
                    save_option = input("\n💾 Save this response as a file? (y/n): ").strip().lower()
                    if save_option in ['y', 'yes']:
                        filename = input("📄 Enter filename (e.g., myscript.py): ").strip()
                        if filename:
                            if not filename.endswith('.py'):
                                filename += '.py'
                            result = safe_write_file(filename, response)
                            if result["status"] == "success":
                                print(f"   ✅ {result['message']}")
                            else:
                                print(f"   ❌ {result['message']}")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            print("\n👋 End of input. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()