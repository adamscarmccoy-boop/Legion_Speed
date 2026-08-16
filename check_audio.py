import subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")

# Check default audio device and format
cmds = [
    'Get-CimInstance Win32_SoundDevice | Format-List Name, Status, Manufacturer',
    'Get-PnpDevice -Class AudioEndpoint -Status OK | Format-List FriendlyName, InstanceId',
]

for cmd in cmds:
    r = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True)
    print(r.stdout)

# Check if any process has exclusive audio
r = subprocess.run(['powershell', '-Command', 
    'Get-Process | Format-Table ProcessName, Id, HandleCount -AutoSize'], 
    capture_output=True, text=True)

# Filter for high-handle processes that might hold audio
for line in r.stdout.splitlines():
    lo = line.lower()
    if any(k in lo for k in ['audio', 'listen', 'realtek', 'nvidia', 'nahimic', 
                              'waves', 'sonarr', 'sonic', 'maxx', 'dts', 'dolby',
                              'a-volute', 'voicemeeter', 'asio', 'wasapi']):
        print(f"  🔴 {line.strip()}")
