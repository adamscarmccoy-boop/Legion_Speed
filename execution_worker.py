import subprocess
import re
import os
from typing import Optional

SANDBOX_DIR = os.environ.get("SANDBOX_DIR", "./sandbox")
if not os.path.exists(SANDBOX_DIR):
    os.makedirs(SANDBOX_DIR, exist_ok=True)

class ExecutionEngine:
    """Handles the secure execution of shell commands within a sandbox."""

    def parse_and_execute(self, full_response: str) -> Optional[str]:
        """Scans response for <<<EXECUTE: command>>> tags and runs them safely."""
        
        pattern = r"<<<EXECUTE:\s*(.*?)>>>"
        matches = re.findall(pattern, full_response)

        if not matches:
            return None

        print(f"\n\033[95m=== EXECUTION PROTOCOL DETECTED ===\033[0m")
        
        command_output = ""
        
        for cmd in matches:
            cmd = cmd.strip()
            
            # === THE IRON GATE (Security Layer) ===
            dangerous = ["del", "rm", "format", "mkfs", "rmdir", "shutdown"]
            if any(cmd.lower().startswith(d) for d in dangerous):
                print(f"\033[91m[SECURITY BLOCKED] Destructive command detected: {cmd}\033[0m")
                command_output += f"\nCommand blocked by Iron Gate: {cmd}"
                continue

            print(f"\033[93mProposed Command: {cmd}\033[0m")
            # Note: In a real system, this input would be handled via an API call or structured response. 
            # For local testing, we use input().
            confirm = input(f"\033[93mExecute this in sandbox? [y/N]: \033[0m").strip().lower()
            
            if confirm == 'y':
                try:
                    print(f"\033[92m[EXECUTING] {cmd}\033[0m")
                    
                    # Force execution inside the sandbox
                    result = subprocess.run(
                        cmd, shell=True, capture_output=True, text=True, cwd=SANDBOX_DIR
                    )
                    
                    output = result.stdout + result.stderr
                    if not output.strip():
                        output = "[Command executed successfully with no output]"
                        
                    print(f"\033[90m--- Terminal Output ---\033[0m\n{output}\n----------------------")
                    
                    # Format raw error log for LLM (Maximizing Error Parsing Fidelity)
                    command_output += f"\nI executed `{cmd}`.\nTerminal Output:\n{output}\n"
                    
                    if result.returncode != 0:
                        command_output += "The command failed with exit code {result.returncode}. Analyze this log and determine the necessary fix for the preceding request."
                    else:
                        command_output += "The command succeeded without errors."

                except Exception as e:
                    print(f"\033[91m[FAILED] Execution Error: {e}\033[0m")
                    command_output += f"\nExecution failed catastrophically: {e}"
            else:
                print(f"\033[93m[SKIPPED]\033[0m")
                command_output += f"\nUser denied permission to run: {cmd}\n"
            
        return command_output if command_output else None