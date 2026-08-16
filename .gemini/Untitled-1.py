
import os
import sys
import platform
import subprocess
import socket
import json
import urllib.request
import urllib.error

# Terminals color output setup
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Enable Windows ANSI escape codes for colors
if platform.system() == 'Windows':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        # Fallback to plain text if console colors fail
        Colors.HEADER = Colors.OKBLUE = Colors.OKCYAN = Colors.OKGREEN = ""
        Colors.WARNING = Colors.FAIL = Colors.ENDC = Colors.BOLD = ""


def check_port(host, port, timeout=1.0):
    """Safely checks if a port is open."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def get_env_info():
    """Identifies the execution environment (Windows, WSL2, Native Linux)."""
    is_wsl = False
    win_host_ip = None
    system = platform.system()
    
    if system == 'Linux':
        if 'microsoft' in platform.release().lower() or os.path.exists('/run/WSL'):
            is_wsl = True
            
    if is_wsl:
        # Resolve Windows Host IP from WSL's resolv.conf
        try:
            with open('/etc/resolv.conf', 'r') as f:
                for line in f:
                    if line.strip().startswith('nameserver'):
                        win_host_ip = line.split()[1].strip()
                        break
        except Exception:
            pass
        # Fallback to route
        if not win_host_ip:
            try:
                res = subprocess.check_output("ip route | grep default", shell=True).decode()
                parts = res.split()
                if len(parts) >= 3:
                    win_host_ip = parts[2]
            except Exception:
                pass
                
    return {
        'os': 'WSL2' if is_wsl else system,
        'is_wsl': is_wsl,
        'win_host_ip': win_host_ip
    }


def check_node():
    """Validates Node.js installation and minimum required version."""
    try:
        version_str = subprocess.check_output(["node", "--version"], stderr=subprocess.DEVNULL).decode().strip()
        v = version_str.lstrip('v')
        major = int(v.split('.')[0])
        minor = int(v.split('.')[1])
        
        if major < 22 or (major == 22 and minor < 16):
            return {"status": "WARNING", "version": version_str, "rec": "OpenClaw requires Node 22.16+ or Node 24 (LTS). Upgrade Node.js."}
        return {"status": "OK", "version": version_str, "rec": ""}
    except FileNotFoundError:
        return {"status": "FAIL", "version": None, "rec": "Node.js is not installed. Please install Node 24 (LTS)."}


def check_openclaw_cli():
    """Checks if OpenClaw is installed globally."""
    try:
        version_str = subprocess.check_output(["openclaw", "--version"], stderr=subprocess.DEVNULL).decode().strip()
        return {"status": "OK", "version": version_str}
    except FileNotFoundError:
        return {"status": "FAIL", "version": None}


def check_wsl_systemd(is_wsl):
    """If in WSL2, checks if systemd is enabled (required for daemon setups)."""
    if not is_wsl:
        return None
    try:
        status = subprocess.check_output(["systemctl", "is-system-running"], stderr=subprocess.DEVNULL).decode().strip()
        is_active = status in ["running", "degraded", "starting"]
        
        gateway_service = "unknown"
        try:
            gateway_service = subprocess.check_output(["systemctl", "--user", "is-active", "openclaw-gateway"], stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            pass
            
        return {
            "active": is_active,
            "status": status,
            "gateway_service": gateway_service
        }
    except Exception:
        return {"active": False, "status": "Inactive/Error", "gateway_service": "unknown"}


def check_gateway_api():
    """Queries OpenClaw Gateway on port 18789."""
    ports = {
        "127.0.0.1": check_port("127.0.0.1", 18789),
        "::1": check_port("::1", 18789)
    }
    
    alive = False
    details = ""
    try:
        req = urllib.request.Request("http://127.0.0.1:18789/", headers={'User-Agent': 'OpenClawDiag/1.0'})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if resp.status == 200:
                alive = True
    except urllib.error.HTTPError as e:
        if e.code in [401, 403, 400]: # Gateway is active but rejecting requests / wants auth
            alive = True
        else:
            details = f"HTTP Error {e.code}"
    except Exception as e:
        details = str(e)
        
    return {"ports": ports, "alive": alive, "details": details}


def check_chrome_cdp(env_info):
    """Probes port 9222 for Chrome DevTools Protocol and verifies endpoint payload."""
    hosts = ["127.0.0.1", "localhost", "::1"]
    if env_info['is_wsl'] and env_info['win_host_ip']:
        hosts.append(env_info['win_host_ip'])
        
    ports = {h: check_port(h, 9222) for h in hosts}
    cdp_active = False
    browser_metadata = None
    
    for host, open_state in ports.items():
        if open_state:
            try:
                url = f"http://{host}:9222/json/version"
                req = urllib.request.Request(url, headers={'User-Agent': 'OpenClawDiag/1.0'})
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode())
                        cdp_active = True
                        browser_metadata = {
                            "host_tested": host,
                            "browser": data.get("Browser"),
                            "protocol": data.get("Protocol-Version")
                        }
                        break
            except Exception:
                pass
                
    return {"ports": ports, "active": cdp_active, "meta": browser_metadata}


def get_openclaw_config(env_info):
    """Validates ~/.openclaw/openclaw.json existence."""
    if env_info['is_wsl'] or platform.system() != 'Windows':
        path = os.path.expanduser('~/.openclaw/openclaw.json')
    else:
        path = os.path.join(os.environ.get('USERPROFILE', ''), '.openclaw', 'openclaw.json')
        
    if not os.path.exists(path):
        return {"exists": False, "path": path, "data": None}
    try:
        with open(path, 'r') as f:
            return {"exists": True, "path": path, "data": json.load(f)}
    except Exception:
        return {"exists": True, "path": path, "data": None, "corrupt": True}


def check_windows_specifics():
    """Runs Windows host diagnostics (processes and netsh rules)."""
    if platform.system() != 'Windows':
        return None
        
    chrome_running = False
    try:
        tasks = subprocess.check_output(["tasklist", "/fi", "IMAGENAME eq chrome.exe"], stderr=subprocess.DEVNULL).decode(errors='ignore')
        chrome_running = "chrome.exe" in tasks.lower()
    except Exception:
        pass
        
    portproxy_rules = ""
    try:
        portproxy_rules = subprocess.check_output(["netsh", "interface", "portproxy", "show", "all"], stderr=subprocess.DEVNULL).decode(errors='ignore')
    except Exception:
        pass
        
    return {
        "chrome_running": chrome_running,
        "portproxy": portproxy_rules
    }


def main():
    print(f"{Colors.HEADER}{Colors.BOLD}=== OpenClaw System & Connection Diagnostic Tool ==={Colors.ENDC}\n")
    
    env = get_env_info()
    print(f"[*] Environment Detected: {Colors.BOLD}{env['os']}{Colors.ENDC}")
    if env['is_wsl']:
        print(f"[*] WSL2 Windows Host Gateway IP: {Colors.OKCYAN}{env['win_host_ip']}{Colors.ENDC}")
    
    # 1. Dependency Checks
    print("\n--- Dependencies ---")
    node = check_node()
    if node['status'] == 'OK':
        print(f"[✓] Node.js: {Colors.OKGREEN}{node['version']}{Colors.ENDC}")
    elif node['status'] == 'WARNING':
        print(f"[!] Node.js: {Colors.WARNING}{node['version']} (Warning: {node['rec']}){Colors.ENDC}")
    else:
        print(f"[✗] Node.js: {Colors.FAIL}NOT INSTALLED! ({node['rec']}){Colors.ENDC}")
        
    cli = check_openclaw_cli()
    if cli['status'] == 'OK':
        print(f"[✓] OpenClaw CLI: {Colors.OKGREEN}{cli['version']}{Colors.ENDC}")
    else:
        print(f"[✗] OpenClaw CLI: {Colors.FAIL}NOT INSTALLED!{Colors.ENDC}")
        
    wsl_sys = check_wsl_systemd(env['is_wsl'])
    if wsl_sys:
        if wsl_sys['active']:
            print(f"[✓] WSL2 systemd: {Colors.OKGREEN}Active{Colors.ENDC} (Gateway Service: {Colors.BOLD}{wsl_sys['gateway_service']}{Colors.ENDC})")
        else:
            print(f"[✗] WSL2 systemd: {Colors.FAIL}Inactive! Systemd is required for openclaw-gateway runtimes.{Colors.ENDC}")

    # 2. Config File Validation
    print("\n--- Configurations ---")
    cfg = get_openclaw_config(env)
    if cfg['exists']:
        if cfg['data']:
            print(f"[✓] Config found at: {Colors.OKGREEN}{cfg['path']}{Colors.ENDC}")
        else:
            print(f"[✗] Config at {Colors.FAIL}{cfg['path']} is corrupt or invalid JSON!{Colors.ENDC}")
    else:
        print(f"[!] Config missing at: {Colors.WARNING}{cfg['path']} (Normal if first-time onboarding){Colors.ENDC}")

    # 3. Connection & Port Scans
    print("\n--- Connectivity & Port Check ---")
    gw = check_gateway_api()
    gw_listening = any(gw['ports'].values())
    if gw_listening:
        status_color = Colors.OKGREEN if gw['alive'] else Colors.WARNING
        print(f"[✓] OpenClaw Gateway (Port 18789): {status_color}Listening{Colors.ENDC}")
        for host, status in gw['ports'].items():
            print(f"    - {host}: {'OPEN' if status else 'CLOSED'}")
    else:
        print(f"[✗] OpenClaw Gateway (Port 18789): {Colors.FAIL}NOT LISTENING (ECONNREFUSED){Colors.ENDC}")
        
    cdp = check_chrome_cdp(env)
    if cdp['active']:
        print(f"[✓] Chrome DevTools Protocol (Port 9222): {Colors.OKGREEN}Active & Reachable{Colors.ENDC}")
        print(f"    - Connected to: {Colors.BOLD}{cdp['meta']['browser']}{Colors.ENDC} on {cdp['meta']['host_tested']}")
    else:
        print(f"[✗] Chrome DevTools Protocol (Port 9222): {Colors.FAIL}NOT REACHABLE{Colors.ENDC}")
        for host, status in cdp['ports'].items():
            print(f"    - {host}: {'OPEN' if status else 'CLOSED'}")

    win_specs = check_windows_specifics()
    if win_specs:
        print("\n--- Windows Host Process & Forwarding Status ---")
        print(f"[*] Chrome.exe running on Windows: {'YES' if win_specs['chrome_running'] else 'NO'}")
        if win_specs['portproxy'].strip():
            print("[*] Active Port Forwarding Rules (netsh):")
            print(win_specs['portproxy'])
        else:
            print("[*] Active Port Forwarding Rules (netsh): None found.")

    # 4. Diagnostics Evaluation / Action Items
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== ACTION ITEMS (WHAT NEEDS FIXED) ==={Colors.ENDC}")
    trouble_found = False
    
    # Check Node
    if node['status'] == 'FAIL':
        trouble_found = True
        print(f"\n{Colors.BOLD}1. Node.js is Missing{Colors.ENDC}")
        print("   -> Action: Download and install Node.js 24 LTS from https://nodejs.org/")
    elif node['status'] == 'WARNING':
        trouble_found = True
        print(f"\n{Colors.BOLD}1. Outdated Node.js Version{Colors.ENDC}")
        print(f"   -> Action: Your system runs {node['version']}. OpenClaw performs best on Node 24.")
        
    # Check CLI
    if cli['status'] == 'FAIL':
        trouble_found = True
        print(f"\n{Colors.BOLD}2. OpenClaw CLI is Missing{Colors.ENDC}")
        print("   -> Action: Install the global CLI executable using your terminal:")
        print(f"      {Colors.OKCYAN}npm install -g openclaw@latest{Colors.ENDC}")
        
    # Check WSL Systemd
    if wsl_sys and not wsl_sys['active']:
        trouble_found = True
        print(f"\n{Colors.BOLD}3. Systemd is disabled inside WSL2{Colors.ENDC}")
        print("   -> Action: Edit '/etc/wsl.conf' inside your WSL Ubuntu shell to enable systemd:")
        print(f"      {Colors.OKCYAN}sudo nano /etc/wsl.conf{Colors.ENDC}")
        print("      Add the following blocks and save:")
        print("      [boot]\n      systemd=true")
        print("      Then, restart WSL inside your Windows PowerShell terminal:")
        print(f"      {Colors.OKCYAN}wsl --shutdown{Colors.ENDC}")

    # Check Gateway Connection
    if not gw_listening:
        trouble_found = True
        print(f"\n{Colors.BOLD}4. OpenClaw Gateway Daemon is Offline (ECONNREFUSED on 18789){Colors.ENDC}")
        if env['is_wsl']:
            print("   -> Action: Fire up the background gateway process inside WSL:")
            print(f"      {Colors.OKCYAN}openclaw gateway start{Colors.ENDC}")
            print("      (Or if registered as service):")
            print(f"      {Colors.OKCYAN}systemctl --user start openclaw-gateway{Colors.ENDC}")
        else:
            print("   -> Action: Start the local gateway in Windows Command Prompt / PowerShell:")
            print(f"      {Colors.OKCYAN}openclaw gateway start{Colors.ENDC}")

    # Check Chrome CDP Connection
    if not cdp['active']:
        trouble_found = True
        print(f"\n{Colors.BOLD}5. Chrome DevTools Protocol is Offline (Unreachable on Port 9222){Colors.ENDC}")
        print("   -> Action: Start Google Chrome on your host machine with debugging ports enabled.")
        if env['is_wsl'] or platform.system() == 'Windows':
            print("      In your Windows Run prompt (Win + R) or PowerShell, run:")
            print(f"      {Colors.OKCYAN}start chrome --remote-debugging-port=9222{Colors.ENDC}")
        else:
            print("      Run the following in your terminal:")
            print(f"      {Colors.OKCYAN}google-chrome --remote-debugging-port=9222{Colors.ENDC}")

        # If in WSL, explain port forwarding / firewall boundary
        if env['is_wsl'] and env['win_host_ip']:
            print(f"\n{Colors.BOLD}6. Boundary Mismatch: WSL cannot connect to Windows Chrome over Loopback{Colors.ENDC}")
            print(f"   -> WSL is attempting to reach Windows on {env['win_host_ip']}:9222. Since Windows Chrome")
            print("      default-binds to local loopbacks (127.0.0.1 / ::1), we must forward the bridge!")
            print("   -> Action 1 (If Chrome is bound to 127.0.0.1 on Windows):")
            print("      Execute inside Windows PowerShell (as Administrator) to proxy requests:")
            print(f"      {Colors.OKCYAN}netsh interface portproxy add v4tov4 listenaddress={env['win_host_ip']} listenport=9222 connectaddress=127.0.0.1 connectport=9222{Colors.ENDC}")
            print("   -> Action 2 (If Chrome is bound to ::1 / IPv6 on Windows):")
            print(f"      Execute inside Windows PowerShell (as Administrator):")
            print(f"      {Colors.OKCYAN}netsh interface portproxy add v4tov6 listenaddress={env['win_host_ip']} listenport=9222 connectaddress=::1 connectport=9222{Colors.ENDC}")
            print("   -> Action 3: Make sure you expose Windows local network ports to WSL in Windows Defender Firewall.")
            print(f"      {Colors.OKCYAN}New-NetFirewallRule -DisplayName \"OpenClaw Gateway\" -Direction Inbound -Protocol TCP -LocalPort 18789 -Action Allow{Colors.ENDC}")

    if not trouble_found:
        print(f"\n{Colors.OKGREEN}✔ Everything looks healthy! No immediate network boundary or configuration issues detected.{Colors.ENDC}")
        print("  If you still cannot communicate with the agent, double check token auth rules in your channel settings.")
    else:
        print(f"\n{Colors.WARNING}* Please execute the highlighted troubleshooting steps above and run the script again. *{Colors.ENDC}")

if __name__ == "__main__":
    main()