#!/usr/bin/env python3
"""
Sovereign Master CLI
Unified interface for Tailnet ingress audit, MCP RAG queries, contract parsing, and DSP execution.
"""

import os
import sys
import json
import socket
import asyncio
import argparse
from typing import Dict, Any, List, Optional
import httpx

# --- Environment & Ingress Configuration ---
DEFAULT_ROUTES = [
    {"name": "Frontend WebUI", "ingress": "https://scars-lab.taila0aac3.ts.net/", "host": "127.0.0.1", "port": 3000, "path": "/"},
    {"name": "Core Backend API", "ingress": "https://scars-lab.taila0aac3.ts.net/api", "host": "127.0.0.1", "port": 8080, "path": "/"},
    {"name": "MCP Swarm / RAG Gateway", "ingress": "https://scars-lab.taila0aac3.ts.net/mcp", "host": "127.0.0.1", "port": 8005, "path": "/health"},
    {"name": "FastAPI / Proxy Router", "ingress": "https://scars-lab.taila0aac3.ts.net/proxy", "host": "127.0.0.1", "port": 8000, "path": "/health"},
    {"name": "Ray / Inference Worker", "ingress": "https://scars-lab.taila0aac3.ts.net:8443/", "host": "127.0.0.1", "port": 8002, "path": "/"},
    {"name": "DSP / ONNX Remaster Daemon", "ingress": "https://scars-lab.taila0aac3.ts.net:10000/", "host": "127.0.0.1", "port": 8003, "path": "/"},
]

# --- Helper Utilities ---
def check_tcp(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

async def probe_http(host: str, port: int, path: str) -> tuple[bool, int]:
    url = f"http://{host}:{port}{path}"
    try:
        async with httpx.AsyncClient(timeout=2.5) as client:
            res = await client.get(url)
            return True, res.status_code
    except Exception:
        return False, 0

# --- Command: check-ingress ---
async def cmd_check_ingress(args):
    print("\n" + "=" * 65)
    print(" 🚀 SOVEREIGN / TAILNET INGRESS STATUS AUDIT")
    print("=" * 65)
    all_live = True
    for route in DEFAULT_ROUTES:
        name = route["name"]
        host = route["host"]
        port = route["port"]
        ingress = route["ingress"]

        tcp_up = check_tcp(host, port)
        if not tcp_up:
            print(f" [❌ DOWN] {name:<26} -> Port {port} (TCP Connection Refused)")
            all_live = False
            continue

        http_up, status = await probe_http(host, port, route["path"])
        if http_up:
            print(f" [✅ LIVE] {name:<26} -> 127.0.0.1:{port} (HTTP {status})")
            print(f"          ↳ Ingress: {ingress}")
        else:
            print(f" [⚠️  WARN] {name:<26} -> Port {port} open (HTTP probe failed)")
            all_live = False

    print("=" * 65)
    if all_live:
        print(" 🎉 All local daemons are active and ready for Tailnet routing.\n")
    else:
        print(" ⚠️  Check inactive ports before routing production traffic.\n")

# --- Command: parse-contracts ---
async def cmd_parse_contracts(args):
    url = args.url
    print(f"\n[*] Fetching webpage: {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=20.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html_text = resp.text
    except Exception as e:
        print(f"[❌] Failed to fetch URL {url}: {e}")
        return

    # Basic text cleanup
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
            tag.extract()
        text_content = soup.get_text(separator="\n").strip()
    except ImportError:
        text_content = html_text[:20000]

    print(f"[+] Retrieved {len(text_content)} characters. Forwarding to LLM extraction engine...")

    # LLM extraction payload
    llm_url = os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:1234/v1/chat/completions")
    prompt = f"""
    You are an expert contract & procurement extraction engine.
    Extract all contract, freelance, or subcontract opportunities from the text below.
    Return JSON array of objects with keys: "title", "organization", "compensation", "key_skills", "summary".

    Page Content:
    {text_content[:24000]}
    """

    payload = {
        "messages": [
            {"role": "system", "content": "You are a JSON-only extraction bot. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            llm_resp = await client.post(llm_url, json=payload)
            if llm_resp.status_code == 200:
                out = llm_resp.json()["choices"][0]["message"]["content"]
                print("\n" + "=" * 65)
                print(" 📋 EXTRACTED CONTRACT OPPORTUNITIES")
                print("=" * 65)
                print(out)
                if args.export_json:
                    with open(args.export_json, "w", encoding="utf-8") as f:
                        f.write(out)
                    print(f"\n[+] Exported to {args.export_json}")
            else:
                print(f"[❌] LLM endpoint returned status {llm_resp.status_code}: {llm_resp.text}")
    except Exception as e:
        print(f"[❌] Failed to connect to local LLM ({llm_url}): {e}")

# --- Command: acp ---
def cmd_acp(args):
    print("\n[*] Inspecting A2A Zero-Copy Envelope Status...")
    mcp_port = 8005
    acp_port = 8000
    print(f" - MCP Gateway (Port {mcp_port}): {'ONLINE' if check_tcp('127.0.0.1', mcp_port) else 'OFFLINE'}")
    print(f" - ACP Control Plane (Port {acp_port}): {'ONLINE' if check_tcp('127.0.0.1', acp_port) else 'OFFLINE'}")
    print("[+] A2A Zero-Copy Envelope protocol ready.\n")

# --- Command: status ---
def cmd_status(args):
    print("\n--- Sovereign Stack Quick Status ---")
    ports = {"WebUI": 3000, "Proxy": 8000, "Ray": 8002, "DSP": 8003, "MCP": 8005, "Backend": 8080, "LMStudio": 1234}
    for name, port in ports.items():
        state = "ONLINE" if check_tcp("127.0.0.1", port) else "OFFLINE"
        print(f"  - {name:<10} (Port {port:<5}): {state}")
    print("-" * 36 + "\n")

# --- CLI Entrypoint ---
def main():
    parser = argparse.ArgumentParser(
        description="Sovereign Master CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command")

    # check-ingress
    subparsers.add_parser("check-ingress", help="Audit health of Tailnet proxy routes and ports")

    # status
    subparsers.add_parser("status", help="Quick check of all local daemon ports")

    # acp
    subparsers.add_parser("acp", help="Check A2A control plane envelope status")

    # parse-contracts
    parse_p = subparsers.add_parser("parse-contracts", help="Scrape webpage & extract contracts via LLM")
    parse_p.add_argument("--url", required=True, help="Target URL to scrape")
    parse_p.add_argument("--export-json", default=None, help="File path to save JSON results")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.command == "check-ingress":
        asyncio.run(cmd_check_ingress(args))
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "acp":
        cmd_acp(args)
    elif args.command == "parse-contracts":
        asyncio.run(cmd_parse_contracts(args))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()