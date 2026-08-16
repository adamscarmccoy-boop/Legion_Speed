"""
alphaXiv MCP Connector & Diagnostic Verification Script
"""
import json
import sys
import urllib.request
import urllib.parse

MCP_ENDPOINT = "https://api.alphaxiv.org/mcp/v1"
WELL_KNOWN_URL = "https://api.alphaxiv.org/.well-known/oauth-protected-resource/mcp/v1"

def check_mcp_auth_requirement():
    print("=== Step 1: Querying alphaXiv MCP Endpoint ===")
    req = urllib.request.Request(
        MCP_ENDPOINT,
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            print("Status Code:", resp.status)
            print("Response:", resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Server returned HTTP {e.code} ({e.reason})")
        err_body = e.read().decode('utf-8')
        print(f"Body: {err_body}")
        
        www_auth = e.headers.get("www-authenticate", "")
        print(f"WWW-Authenticate Header: {www_auth}")

def check_oauth_metadata():
    print("\n=== Step 2: Discovering OAuth Resource Metadata ===")
    try:
        with urllib.request.urlopen(WELL_KNOWN_URL) as resp:
            metadata = json.loads(resp.read().decode())
            print(json.dumps(metadata, indent=2))
            return metadata
    except Exception as e:
        print(f"Failed to fetch metadata: {e}")
        return None

if __name__ == "__main__":
    check_mcp_auth_requirement()
    check_oauth_metadata()
