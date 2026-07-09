#!/usr/bin/env python3
import base64, requests, time, sys, hashlib

VPS_URL = "http://187.124.31.229:80"
AGENT_ID = "a0-falke"
TARGET_PATH = "C:\\temp\\LOGReport_v439.exe"
LOCAL_FILE = "/opt/data/LOGReport/LOGReport_v439.exe"
CHUNK_SIZE = 10240

with open(LOCAL_FILE, 'rb') as f:
    data = f.read()
    local_hash = hashlib.sha256(data).hexdigest()

total_size = len(data)
total_chunks = (total_size + CHUNK_SIZE - 1) // CHUNK_SIZE

print(f"File: {total_size} bytes, {total_chunks} chunks", flush=True)
print(f"Local SHA256: {local_hash}", flush=True)

offset = 0
chunk_num = 0
failures = 0

while offset < total_size:
    chunk = data[offset:offset + CHUNK_SIZE]
    chunk_b64 = base64.b64encode(chunk).decode('ascii')
    payload = {"path": TARGET_PATH, "data": chunk_b64, "offset": offset}
    
    success = False
    for attempt in range(3):
        try:
            resp = requests.post(f"{VPS_URL}/api/agent/{AGENT_ID}/fs-write",
                               json=payload, timeout=60)
            if resp.status_code == 200:
                success = True
                break
            time.sleep(1)
        except:
            time.sleep(2)
    
    if not success:
        failures += 1
        if failures > 20:
            print(f"TOO MANY FAILURES at chunk {chunk_num}", flush=True)
            sys.exit(1)
    
    chunk_num += 1
    offset += CHUNK_SIZE
    if chunk_num % 100 == 0:
        print(f"  {chunk_num}/{total_chunks} ({offset}/{total_size})", flush=True)

print(f"Upload: {chunk_num} chunks, {failures} failures", flush=True)

time.sleep(3)
resp = requests.post(f"{VPS_URL}/api/agent/{AGENT_ID}/fs-hash",
                    json={"path": TARGET_PATH}, timeout=30)
vm_hash = resp.json().get('sha256', 'ERROR')
print(f"VM SHA256:   {vm_hash}", flush=True)
print(f"Local SHA256: {local_hash}", flush=True)
if vm_hash == local_hash:
    print("HASH MATCH ✓", flush=True)
else:
    print("HASH MISMATCH ✗", flush=True)