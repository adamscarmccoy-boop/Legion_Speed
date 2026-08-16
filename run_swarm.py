import subprocess
import time

print("Starting Antigravity Swarm...")

# Start the API bridge in the background
api_bridge_path = r"C:\WEB CASE STUDY\antigravity_vscode_ext\api_bridge.py"
python_exe = r"C:\WEB CASE STUDY\.venv\Scripts\python.exe"
print(f"Launching API Bridge: {api_bridge_path} using {python_exe}")
subprocess.Popen([python_exe, api_bridge_path], creationflags=subprocess.CREATE_NEW_CONSOLE)

# Wait a second for the server to boot
time.sleep(2)

# Launch VS Code Extension Development Host
ext_path = r"C:\WEB CASE STUDY\antigravity_vscode_ext"
print(f"Opening VS Code Extension Host: {ext_path}")
subprocess.run(["code", f"--extensionDevelopmentPath={ext_path}"])      

print("Done! Check your new VS Code window.")
