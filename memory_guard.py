import time
import sys
import os
import psutil
from datetime import datetime

# Target memory thresholds
WARNING_COMMIT_GB = 40.0
CRITICAL_COMMIT_GB = 52.0

def get_top_memory_procs(n=5):
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            mem = p.info['memory_info']
            if mem:
                procs.append((p.info['name'], p.info['pid'], mem.rss / (1024 ** 2)))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: x[2], reverse=True)
    return procs[:n]

def main():
    if os.name == 'nt':
        os.system("title Sovereign Memory Guard")
    print("==================================================================")
    print("       SOVEREIGN MEMORY GUARD & RESOURCE MONITOR ACTIVE           ")
    print("==================================================================")
    print(f"Monitoring system commit RAM & VRAM limits every 5s...")
    print(f"Warning Threshold : {WARNING_COMMIT_GB} GB")
    print(f"Critical Threshold: {CRITICAL_COMMIT_GB} GB\n")

    last_report_time = 0

    while True:
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            used_ram_gb = mem.used / (1024 ** 3)
            total_ram_gb = mem.total / (1024 ** 3)
            used_swap_gb = swap.used / (1024 ** 3)
            total_commit_gb = (mem.used + swap.used) / (1024 ** 3)

            now = time.time()

            # Output heartbeat status every 15 seconds or when usage changes significantly
            if now - last_report_time > 15 or total_commit_gb > WARNING_COMMIT_GB:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] RAM: {used_ram_gb:.1f}/{total_ram_gb:.1f} GB ({mem.percent}%) | Pagefile: {used_swap_gb:.1f} GB | Total Commit: {total_commit_gb:.1f} GB")
                
                if total_commit_gb > WARNING_COMMIT_GB:
                    print(f"  [!] HIGH MEMORY CONSUMPTION DETECTED! Top 5 RAM consumers:")
                    top_procs = get_top_memory_procs(5)
                    for name, pid, rss in top_procs:
                        print(f"      - {name:<25} (PID {pid:>6}): {rss:>7.1f} MB")

                if total_commit_gb > CRITICAL_COMMIT_GB:
                    print(f"  [CRITICAL WARNING] Commit approaching dangerous BSOD limit! Recommend closing unused background servers.")
                
                last_report_time = now

        except Exception as e:
            print(f"Monitor error: {e}")

        time.sleep(5)

if __name__ == "__main__":
    main()
