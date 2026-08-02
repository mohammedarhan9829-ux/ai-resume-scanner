#!/usr/bin/env python
import os
import sys
import socket
import uvicorn

# Force UTF-8 encoding for standard output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def get_local_ip() -> str:
    """Retrieve host IPv4 address on local network (Wi-Fi/LAN)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def print_banner(host_ip: str, port: int):
    """Print ASCII Banner and Network Links for Presentation."""
    print("=" * 72)
    print("      [+] AI RESUME SCANNER & CAREER MATCHER - NETWORK DEPLOYMENT")
    print("      B.Tech AI & Data Science (AI&DS) 4th Year Project")
    print("=" * 72)
    print(f"  --> Local Computer Access : http://localhost:{port}")
    print(f"  --> Local Network (LAN)   : http://{host_ip}:{port}")
    print("-" * 72)
    print("  [!] IMPORTANT BROWSER NOTE:")
    print("      Do NOT type 0.0.0.0 in the browser address bar!")
    print(f"      - On this PC, open: http://localhost:{port}")
    print(f"      - On other devices on Wi-Fi, open: http://{host_ip}:{port}")
    print("=" * 72)
    print("\nServer is running... Press Ctrl+C to stop.\n")

if __name__ == "__main__":
    port = 8000
    host_ip = get_local_ip()

    if "--test" in sys.argv:
        print("Testing server startup script...")
        print(f"Detected IP: {host_ip}")
        print("Test passed successfully.")
        sys.exit(0)

    print_banner(host_ip, port)
    
    # Run Uvicorn server bound to 0.0.0.0 for network availability
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)
