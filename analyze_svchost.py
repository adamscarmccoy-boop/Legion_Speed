import subprocess
import datetime
import xml.etree.ElementTree as ET
import sys
import json
import csv

def get_active_service_hosts():
    """Uses tasklist.exe to deterministically capture all svchost processes and hosted services."""
    cmd = ["tasklist", "/svc", "/fi", "IMAGENAME eq svchost.exe", "/fo", "csv"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="oem", errors="replace")
    except Exception as e:
        print(f"[!] Error running tasklist: {e}", file=sys.stderr)
        return []
    
    hosts = []
    lines = res.stdout.strip().splitlines()
    if len(lines) < 2:
        return hosts

    reader = csv.reader(lines)
    header = next(reader, None)

    for row in reader:
        if len(row) >= 3:
            image_name, pid_str, services_str = row[0], row[1], row[2]
            try:
                pid = int(pid_str)
            except ValueError:
                continue

            services = [s.strip() for s in services_str.split(",") if s.strip()]
            hosts.append({
                "pid": pid,
                "services_count": len(services),
                "services": sorted(services)
            })

    return hosts

def get_process_memory_map():
    """Fetches Working Set memory for svchost PIDs using wmic."""
    cmd = ["wmic", "process", "where", "name='svchost.exe'", "get", "ProcessId,WorkingSetSize", "/format:csv"]
    pid_mem = {}
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="oem", errors="replace")
        lines = [l.strip() for l in res.stdout.splitlines() if l.strip()]
        reader = csv.reader(lines)
        for row in reader:
            if len(row) >= 3 and row[1].isdigit() and row[2].isdigit():
                pid = int(row[1])
                ws_bytes = int(row[2])
                pid_mem[pid] = round(ws_bytes / (1024 * 1024), 2)
    except Exception:
        pass
    return pid_mem

def get_last_hour_service_events():
    """Uses native Windows wevtutil to extract Service Control Manager events from System Event Log over the last 1 hour."""
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    one_hour_ago = now_utc - datetime.timedelta(hours=1)
    iso_time = one_hour_ago.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    xpath_query = f"*[System[Provider[@Name='Service Control Manager'] and TimeCreated[@SystemTime>='{iso_time}']]]"
    cmd = ["wevtutil", "qe", "System", f"/q:{xpath_query}", "/f:xml", "/c:200"]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"[!] Error running wevtutil: {e}", file=sys.stderr)
        return []

    if not res.stdout.strip():
        return []

    events = []
    xml_data = f"<Events>{res.stdout}</Events>"
    try:
        root = ET.fromstring(xml_data)
        for evt in root.findall(".//{http://schemas.microsoft.com/win/2004/08/events/event}Event"):
            sys_node = evt.find("{http://schemas.microsoft.com/win/2004/08/events/event}System")
            
            evt_id = sys_node.find("{http://schemas.microsoft.com/win/2004/08/events/event}EventID").text if sys_node.find("{http://schemas.microsoft.com/win/2004/08/events/event}EventID") is not None else "N/A"
            time_created = sys_node.find("{http://schemas.microsoft.com/win/2004/08/events/event}TimeCreated")
            sys_time = time_created.attrib.get("SystemTime", "N/A") if time_created is not None else "N/A"
            
            if sys_time != "N/A":
                try:
                    dt = datetime.datetime.fromisoformat(sys_time.replace("Z", "+00:00"))
                    sys_time = dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass

            event_data = evt.find("{http://schemas.microsoft.com/win/2004/08/events/event}EventData")
            data_items = []
            if event_data is not None:
                for d in event_data.findall("{http://schemas.microsoft.com/win/2004/08/events/event}Data"):
                    if d.text:
                        data_items.append(d.text.strip())

            details = " | ".join(data_items) if data_items else "Service state update"

            events.append({
                "timestamp": sys_time,
                "event_id": evt_id,
                "details": details
            })
    except Exception as e:
        events.append({"timestamp": "N/A", "event_id": "ERR", "details": f"XML parse error: {e}"})

    return events

def main():
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hosts = get_active_service_hosts()
    mem_map = get_process_memory_map()

    total_mem = 0.0
    for h in hosts:
        h["ram_mb"] = mem_map.get(h["pid"], 0.0)
        total_mem += h["ram_mb"]

    hosts.sort(key=lambda x: x["ram_mb"], reverse=True)
    events = get_last_hour_service_events()

    # Console Report Output
    print("=" * 90)
    print(f" WINDOWS SERVICE HOSTS (svchost.exe) DIAGNOSTIC REPORT")
    print(f" Generated: {now_str}")
    print("=" * 90)
    print()

    print("--- 1. ACTIVE SERVICE HOST PROCESSES ---")
    print(f" Total Active svchost PIDs : {len(hosts)}")
    print(f" Total Hosted Services    : {sum(h['services_count'] for h in hosts)}")
    print(f" Total svchost Memory     : {total_mem:.2f} MB")
    print()

    print(f"{'PID':<8} {'RAM (MB)':<12} {'SVCS':<6} {'HOSTED WINDOWS SERVICES'}")
    print("-" * 90)
    for h in hosts:
        svc_str = ", ".join(h["services"])
        if len(svc_str) > 60:
            svc_str = svc_str[:57] + "..."
        mem_display = f"{h['ram_mb']:.2f}" if h['ram_mb'] > 0 else "N/A"
        print(f"{h['pid']:<8} {mem_display:<12} {h['services_count']:<6} {svc_str}")

    print()
    print("=" * 90)

    print(f"--- 2. SERVICE CONTROL MANAGER EVENTS (LAST 60 MINUTES: {len(events)} events) ---")
    print("-" * 90)

    if not events:
        print(" No Service Control Manager state change/error events recorded in the last 60 minutes.")
    else:
        print(f"{'TIMESTAMP':<22} {'ID':<8} {'EVENT DETAILS'}")
        print("-" * 90)
        for e in events:
            det = e['details']
            if len(det) > 55:
                det = det[:52] + "..."
            print(f"{e['timestamp']:<22} {e['event_id']:<8} {det}")

    print("=" * 90)

    # Export to JSON
    report_data = {
        "generated_at": now_str,
        "summary": {
            "total_pids": len(hosts),
            "total_services": sum(h['services_count'] for h in hosts),
            "total_ram_mb": round(total_mem, 2)
        },
        "active_service_hosts": hosts,
        "last_hour_events": events
    }
    with open("svchost_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print("\n[+] Structured report saved to 'svchost_report.json'")

if __name__ == "__main__":
    main()
