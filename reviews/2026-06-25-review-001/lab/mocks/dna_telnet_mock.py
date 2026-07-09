#!/usr/bin/env python3
"""
Mock Valmet DNA telnet server for LOGReport testing.
Implements a minimal FBC/RPC protocol that responds to the commands
LOGReport's telnet tab sends: connect, get fbc, get rpc, get lis, scan node.

Usage: python dna_telnet_mock.py --port 23
"""
import argparse
import socket
import threading
import time
import os

# Sample FBC data — mimics Valmet DNA FBC file structure
SAMPLE_FBC = """#FBC AP01m 2026-06-25
NODE=AP01m
TYPE=FBC
TOKEN=AI1.OUT
AI1.OUT = 1
AI1.IN = 0
AI1.RANGE = 0-100
TOKEN=AI2.OUT
AI2.OUT = 1
AI2.IN = 0
AI2.RANGE = 0-100
TOKEN=DI1.STATUS
DI1.STATUS = 1
DI1.IN = 0
END
"""

SAMPLE_RPC = """#RPC AP01m 2026-06-25
NODE=AP01m
TYPE=RPC
RPC.AI1.OUT = 1
RPC.AI1.IN = 0
RPC.AI1.GAIN = 1.0
RPC.AI1.BIAS = 0.0
END
"""

SAMPLE_LIS = """#LIS AP01m 2026-06-25
NODE=AP01m
TYPE=LIS
LIST.AI1
LIST.AI2
LIST.DI1
LIST.DI2
END
"""

SAMPLE_SCAN = """SCAN AP01m
  FBC: OK (12 tokens)
  RPC: OK (12 tokens)
  LIS: OK (4 items)
  STATUS: CONNECTED
"""

COMMANDS = {
    "get fbc": SAMPLE_FBC,
    "get rpc": SAMPLE_RPC,
    "get lis": SAMPLE_LIS,
    "scan node": SAMPLE_SCAN,
    "help": "Available commands: get fbc, get rpc, get lis, scan node, help, quit",
    "status": "Node AP01m: CONNECTED, 12 tokens active",
    "quit": "Goodbye",
}


def handle_client(conn, addr):
    """Handle a single telnet client connection."""
    try:
        conn.sendall(b"Welcome to DNA Node AP01m\r\n")
        conn.sendall(b"Commands: get fbc, get rpc, get lis, scan node, help, quit\r\n")
        conn.sendall(b"> ")
        
        buffer = b""
        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            buffer += data
            
            # Process complete lines (terminated by \r\n or \n)
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                line = line.strip().decode("utf-8", errors="ignore").lower()
                
                if not line:
                    conn.sendall(b"> ")
                    continue
                
                # Find matching command
                response = None
                for cmd_key, cmd_response in COMMANDS.items():
                    if cmd_key in line:
                        response = cmd_response
                        break
                
                if response is None:
                    response = f"Unknown command: {line}. Type 'help' for available commands."
                
                conn.sendall(response.encode("utf-8") + b"\r\n")
                
                if line == "quit":
                    conn.close()
                    return
                
                conn.sendall(b"> ")
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Mock DNA telnet server")
    parser.add_argument("--port", type=int, default=23, help="Port to listen on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((args.host, args.port))
    server.listen(5)
    
    print(f"Mock DNA telnet server listening on {args.host}:{args.port}")
    print(f"Available commands: {', '.join(COMMANDS.keys())}")
    
    while True:
        conn, addr = server.accept()
        print(f"Connection from {addr}")
        thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        thread.start()


if __name__ == "__main__":
    main()