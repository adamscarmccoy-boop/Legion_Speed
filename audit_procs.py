import psutil

print(f"{'PID':>6} | {'RAM (MB)':>10} | {'VIRT (GB)':>10} | {'PROCESS NAME':<25} | COMMAND")
print("-" * 100)

procs = []
for p in psutil.process_iter(['pid', 'name', 'memory_info', 'cmdline']):
    try:
        mem = p.info['memory_info']
        if mem:
            rss_mb = mem.rss / (1024 * 1024)
            vms_gb = mem.vms / (1024 * 1024 * 1024)
            cmd = " ".join(p.info['cmdline']) if p.info['cmdline'] else ""
            procs.append((rss_mb, vms_gb, p.info['pid'], p.info['name'], cmd))
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

procs.sort(key=lambda x: x[0], reverse=True)

for rss_mb, vms_gb, pid, name, cmd in procs[:30]:
    print(f"{pid:>6} | {rss_mb:>10.1f} | {vms_gb:>10.1f} | {name:<25} | {cmd[:60]}")
