import json
import os
from pathlib import Path

# Configuration paths
MCP_CONFIG_PATH = r"C:\Users\adams\.lmstudio\mcp.json"
HARDWARE_CONFIG_PATH = r"C:\Users\adams\.lmstudio\.internal\hardware-config.json"

def check_hardware_config():
    """Verify GPU offloads are correctly set."""
    try:
        with open(HARDWARE_CONFIG_PATH, 'r') as f:
            config = json.load(f)
        # Check that both layers have load.gpuStrictVramCap=true
        for layer in config['json']:
            if not (layer[1]['fields'][0]['value'] == True):
                print("ERROR: GPU strict VRAM cap not enabled")
                return False
    except Exception as e:
        print(f"Hardware config error: {e}")
        return False
    return True

def check_mcp_config():
    """Check if MCP config exists and is valid."""
    if not os.path.exists(MCP_CONFIG_PATH):
        print("WARNING: No mcp.json found")
        return False
    
    try:
        with open(MCP_CONFIG_PATH, 'r') as f:
            data = json.load(f)
        # Basic validation - should have tools list
        if 'tools' not in data or not isinstance(data['tools'], list):
            print("ERROR: MCP config malformed")
            return False
        return True
    except Exception as e:
        print(f"MCP config error: {e}")
        return False

def repair_mcp_json():
    """Repair corrupted mcp.json by creating minimal valid structure."""
    # Create default structure if file doesn't exist or is invalid
    default = {
        "tools": [],
        "settings": {}
    }
    
    try:
        with open(MCP_CONFIG_PATH, 'w') as f:
            json.dump(default, f)
        print("MCP JSON repaired")
        return True
    except Exception as e:
        print(f"Failed to repair MCP: {e}")
        return False

def main():
    """Main health check function."""
    print("=== LM Studio MCP Health Check ===")
    
    # 1. Hardware config check
    if not check_hardware_config():
        print("Hardware configuration is incorrect")
        exit(1)
    
    # 2. MCP config check
    if not check_mcp_config():
        print("MCP configuration needs repair")
        if repair_mcp_json():
            print("Repaired MCP JSON successfully")
        else:
            print("Failed to repair MCP JSON")
            exit(1)
    
    print("All checks passed")

if __name__ == "__main__":
    main()