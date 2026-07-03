#!/usr/bin/env python3
"""Full end-to-end test of LOGReport on remote VM via HermesRemote."""

import base64
import requests
import json
import time
import sys

VPS_URL = "http://187.124.31.229:80"
AGENT_ID = "a0-falke"
LOGREPORT_PORT = 8700

def write_vbs(script_content, path="C:\\temp\\test_api.vbs"):
    """Write a VBS script to VM via HermesRemote."""
    b64 = base64.b64encode(script_content.encode('utf-8')).decode('ascii')
    payload = {"path": path, "data": b64, "offset": 0}
    resp = requests.post(f"{VPS_URL}/api/agent/{AGENT_ID}/fs-write",
                        json=payload, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"fs-write failed: {resp.status_code} {resp.text}")
    return True

def exec_cmd(command, timeout=30):
    """Execute a command on VM via HermesRemote."""
    resp = requests.post(f"{VPS_URL}/api/agent/{AGENT_ID}/exec",
                       json={"command": command}, timeout=timeout)
    data = resp.json()
    stdout = data.get('stdout', '')
    stderr = data.get('stderr', '')
    exit_code = data.get('exit_code', -1)
    return stdout, stderr, exit_code

def api_get(endpoint, timeout=30):
    """GET request to LOGReport API on VM."""
    vbs = f'''Set objHTTP = CreateObject("MSXML2.ServerXMLHTTP.6.0")
objHTTP.setTimeouts 10000, 10000, {timeout*1000}, {timeout*1000}
objHTTP.Open "GET", "http://localhost:{LOGREPORT_PORT}{endpoint}", False
objHTTP.Send
WScript.Echo "STATUS:" & objHTTP.Status
WScript.Echo objHTTP.ResponseText
'''
    write_vbs(vbs)
    stdout, stderr, code = exec_cmd(f"cscript //nologo C:\\temp\\test_api.vbs", timeout=timeout+10)
    return parse_vbs_response(stdout)

def api_post(endpoint, body_json, timeout=30):
    """POST request to LOGReport API on VM."""
    # Escape double quotes and special chars for VBS
    body_escaped = body_json.replace('"', '""')
    vbs = f'''Set objHTTP = CreateObject("MSXML2.ServerXMLHTTP.6.0")
objHTTP.setTimeouts 10000, 10000, {timeout*1000}, {timeout*1000}
objHTTP.Open "POST", "http://localhost:{LOGREPORT_PORT}{endpoint}", False
objHTTP.setRequestHeader "Content-Type", "application/json"
objHTTP.Send "{body_escaped}"
WScript.Echo "STATUS:" & objHTTP.Status
WScript.Echo objHTTP.ResponseText
'''
    write_vbs(vbs)
    stdout, stderr, code = exec_cmd(f"cscript //nologo C:\\temp\\test_api.vbs", timeout=timeout+10)
    return parse_vbs_response(stdout)

def api_put(endpoint, body_json="", timeout=30):
    """PUT request to LOGReport API on VM."""
    body_escaped = body_json.replace('"', '""') if body_json else ""
    vbs = f'''Set objHTTP = CreateObject("MSXML2.ServerXMLHTTP.6.0")
objHTTP.setTimeouts 10000, 10000, {timeout*1000}, {timeout*1000}
objHTTP.Open "PUT", "http://localhost:{LOGREPORT_PORT}{endpoint}", False
objHTTP.setRequestHeader "Content-Type", "application/json"
objHTTP.Send "{body_escaped}"
WScript.Echo "STATUS:" & objHTTP.Status
WScript.Echo objHTTP.ResponseText
'''
    write_vbs(vbs)
    stdout, stderr, code = exec_cmd(f"cscript //nologo C:\\temp\\test_api.vbs", timeout=timeout+10)
    return parse_vbs_response(stdout)

def api_delete(endpoint, body_json="", timeout=30):
    """DELETE request to LOGReport API on VM."""
    body_escaped = body_json.replace('"', '""') if body_json else ""
    send_line = f'objHTTP.Send "{body_escaped}"' if body_escaped else 'objHTTP.Send'
    vbs = f'''Set objHTTP = CreateObject("MSXML2.ServerXMLHTTP.6.0")
objHTTP.setTimeouts 10000, 10000, {timeout*1000}, {timeout*1000}
objHTTP.Open "DELETE", "http://localhost:{LOGREPORT_PORT}{endpoint}", False
objHTTP.setRequestHeader "Content-Type", "application/json"
{send_line}
WScript.Echo "STATUS:" & objHTTP.Status
WScript.Echo objHTTP.ResponseText
'''
    write_vbs(vbs)
    stdout, stderr, code = exec_cmd(f"cscript //nologo C:\\temp\\test_api.vbs", timeout=timeout+10)
    return parse_vbs_response(stdout)

def parse_vbs_response(stdout):
    """Parse VBS output: extract status code and response body."""
    lines = stdout.strip().split('\n')
    status_code = 0
    body_lines = []
    found_status = False
    for line in lines:
        if line.startswith("STATUS:"):
            try:
                status_code = int(line.split(":")[1].strip())
            except:
                pass
            found_status = True
        elif found_status:
            body_lines.append(line)
    body = '\n'.join(body_lines)
    try:
        body_json = json.loads(body)
    except:
        body_json = body
    return status_code, body_json

def check_health():
    """Check if LOGReport is running."""
    print("\n=== Checking LOGReport health ===")
    status, body = api_get("/api/v1/health")
    print(f"  Status: {status}")
    if isinstance(body, dict):
        print(f"  Version: {body.get('version', 'unknown')}")
        print(f"  Node count: {body.get('node_count', 'unknown')}")
        print(f"  Uptime: {body.get('uptime', 'unknown')}")
    return status == 200

def phase1_project_mgmt():
    """Phase 1: Project management - delete existing, create new."""
    print("\n" + "="*60)
    print("PHASE 1: PROJECT MANAGEMENT")
    print("="*60)

    # List existing projects
    print("\n--- 1.1 List existing projects ---")
    status, body = api_get("/api/v1/projects")
    print(f"  Status: {status}")
    if isinstance(body, dict):
        projects = body.get("projects", [])
        print(f"  Existing projects: {len(projects)}")
        for p in projects:
            print(f"    ID={p.get('id')} num={p.get('project_number')} ship={p.get('ship_name')} log_root={p.get('log_root')}")

    # Delete existing project ID 1 if exists
    print("\n--- 1.2 Delete existing project (ID 1) ---")
    status, body = api_delete("/api/v1/projects/1")
    print(f"  Status: {status}")
    print(f"  Response: {body}")

    # Also delete _LOG structure for old project
    print("\n--- 1.3 Delete old _LOG structure ---")
    status, body = api_delete("/api/v1/nodesconfig/delete-structure",
                             json.dumps({"log_root": "C:\\Ships\\TEST_SHIP2"}))
    print(f"  Status: {status}")
    if isinstance(body, dict):
        print(f"  Deleted: {body.get('deleted', '?')}")

    # Also try TEST_SHIP3 if exists from prior runs
    status, body = api_delete("/api/v1/nodesconfig/delete-structure",
                             json.dumps({"log_root": "C:\\Ships\\TEST_SHIP3"}))
    if isinstance(body, dict) and body.get("deleted"):
        print(f"  Deleted old TEST_SHIP3 structure too")

    # Create new project
    print("\n--- 1.4 Create new project ---")
    new_project = {
        "project_number": "T6002",
        "ship_name": "TEST_SHIP3",
        "log_root": "C:\\Ships\\TEST_SHIP3"
    }
    status, body = api_post("/api/v1/projects", json.dumps(new_project))
    print(f"  Status: {status}")
    if isinstance(body, dict) and "project" in body:
        proj = body["project"]
        print(f"  Created project: ID={proj.get('id')} num={proj.get('project_number')} ship={proj.get('ship_name')}")
        return proj.get("id")
    else:
        print(f"  ERROR: Failed to create project: {body}")
        return None

def phase2_load_nodes(project_id):
    """Phase 2: Load nodes from BU directory and nodes.json."""
    print("\n" + "="*60)
    print("PHASE 2: LOAD NODES")
    print("="*60)

    # Scan .sys files from BU directory
    print("\n--- 2.1 Scan .sys files from C:\\dna\\CA\\bu ---")
    status, body = api_get("/api/v1/sysfiles/scan?dir=C:\\dna\\CA\\bu", timeout=60)
    print(f"  Status: {status}")
    if isinstance(body, dict):
        configs = body.get("configs", [])
        print(f"  Nodes found: {len(configs)}")
        print(f"  Total before filter: {body.get('total_before_filter', '?')}")
        sys_files = body.get("sys_files", [])
        print(f"  .sys files found: {len(sys_files)}")
        # Count token types
        fbc_count = sum(1 for c in configs for t in c.get("tokens", []) if t.get("token_type") == "FBC")
        rpc_count = sum(1 for c in configs for t in c.get("tokens", []) if t.get("token_type") == "RPC")
        log_count = sum(1 for c in configs for t in c.get("tokens", []) if t.get("token_type") == "LOG")
        print(f"  Token counts: FBC={fbc_count} RPC={rpc_count} LOG={log_count}")
        # Print first few nodes
        for c in configs[:5]:
            tokens = c.get("tokens", [])
            print(f"    {c.get('name')} (IP={c.get('ip_address')}) tokens={len(tokens)}")
        if len(configs) > 5:
            print(f"    ... and {len(configs)-5} more")

        if len(configs) == 0:
            print("  ERROR: No nodes found in BU directory!")
            return False

        # Save nodes to project-scoped nodes.json
        print(f"\n--- 2.2 Save scanned nodes to project {project_id} ---")
        status, body = api_post(f"/api/v1/nodesconfig?project_id={project_id}",
                              json.dumps(configs))
        print(f"  Status: {status}")
        if isinstance(body, dict):
            print(f"  Saved: {body.get('saved')} count={body.get('count')} path={body.get('path')}")

        # Verify nodes saved
        print(f"\n--- 2.3 Verify nodes saved ---")
        status, body = api_get(f"/api/v1/nodesconfig?project_id={project_id}")
        print(f"  Status: {status}")
        if isinstance(body, dict):
            saved_configs = body.get("configs", [])
            print(f"  Loaded: {len(saved_configs)} nodes from {body.get('path')}")
            fbc_count = sum(1 for c in saved_configs for t in c.get("tokens", []) if t.get("token_type") == "FBC")
            rpc_count = sum(1 for c in saved_configs for t in c.get("tokens", []) if t.get("token_type") == "RPC")
            log_count = sum(1 for c in saved_configs for t in c.get("tokens", []) if t.get("token_type") == "LOG")
            print(f"  Token counts: FBC={fbc_count} RPC={rpc_count} LOG={log_count}")

        # Load from nodes.json file directly
        print(f"\n--- 2.4 Load nodes from nodes.json via PUT /load ---")
        nodes_json_path = f"C:\\Ships\\TEST_SHIP3\\_LOG\\nodes.json"
        status, body = api_put(f"/api/v1/nodesconfig/load?path={nodes_json_path}")
        print(f"  Status: {status}")
        if isinstance(body, dict):
            print(f"  Loaded: {body.get('count')} configs from {body.get('path')}")
        elif isinstance(body, str) and "not_found" in body.lower():
            print(f"  (Expected if nodes.json not at that path yet)")

        # Try scan-nodes via DIA debugger
        print(f"\n--- 2.5 Scan nodes via DIA debugger ---")
        status, body = api_post("/api/v1/sysfiles/scan-nodes", "{}", timeout=90)
        print(f"  Status: {status}")
        if isinstance(body, dict):
            print(f"  Method: {body.get('method', '?')}")
            print(f"  Nodes found: {body.get('count', 0)}")
        elif isinstance(body, str):
            print(f"  Response: {body[:200]}")

        return len(configs) > 0
    return False

def phase3_structure(project_id):
    """Phase 3: Create/delete structure operations."""
    print("\n" + "="*60)
    print("PHASE 3: STRUCTURE OPERATIONS")
    print("="*60)

    log_root = "C:\\Ships\\TEST_SHIP3"

    # Create structure
    print("\n--- 3.1 Create _LOG structure ---")
    status, body = api_post("/api/v1/nodesconfig/create-structure",
                          json.dumps({"log_root": log_root}))
    print(f"  Status: {status}")
    if isinstance(body, dict):
        print(f"  Created dirs: {body.get('created_dirs')}")
        print(f"  Created files: {body.get('created_files')}")
        print(f"  Station count: {body.get('station_count')}")
    else:
        print(f"  Response: {body}")
        return False

    # Verify dirs/files on disk
    print("\n--- 3.2 Verify structure on disk ---")
    stdout, stderr, code = exec_cmd("dir C:\\Ships\\TEST_SHIP3\\_LOG /s /b | findstr /c:\".\" | find /c /v \"\"", timeout=15)
    print(f"  Files on disk: {stdout.strip()}")

    stdout, stderr, code = exec_cmd("dir C:\\Ships\\TEST_SHIP3\\_LOG /ad /s /b | find /c \"\"", timeout=15)
    print(f"  Directories on disk: {stdout.strip()}")

    # Check file tree
    print(f"\n--- 3.3 Check file tree ---")
    status, body = api_get(f"/api/v1/nodesconfig/tree?project_id={project_id}&log_root={log_root}")
    print(f"  Status: {status}")
    if isinstance(body, dict):
        tree = body.get("tree", {})
        stations = tree.get("children", [])
        print(f"  Tree stations: {len(stations)}")
        for s in stations[:3]:
            groups = s.get("children", [])
            print(f"    {s.get('name')} (IP={s.get('ip')}): {len(groups)} groups")
            for g in groups[:4]:
                files = g.get("children", [])
                print(f"      {g.get('name')}: {len(files)} files")
                for f in files[:2]:
                    print(f"        {f.get('name')} lines={f.get('line_count', '?')} status={f.get('status', '?')}")
                if len(files) > 2:
                    print(f"        ... +{len(files)-2} more")
        if len(stations) > 3:
            print(f"    ... and {len(stations)-3} more stations")

    # Delete structure
    print("\n--- 3.4 Delete _LOG structure ---")
    status, body = api_delete("/api/v1/nodesconfig/delete-structure",
                             json.dumps({"log_root": log_root}))
    print(f"  Status: {status}")
    if isinstance(body, dict):
        print(f"  Deleted: {body.get('deleted')}")

    # Verify _LOG deleted
    print("\n--- 3.5 Verify _LOG deleted ---")
    stdout, stderr, code = exec_cmd("if exist C:\\Ships\\TEST_SHIP3\\_LOG (echo EXISTS) else (echo NOT_EXISTS)", timeout=10)
    result = stdout.strip()
    print(f"  _LOG dir: {result}")
    if "EXISTS" in result:
        print("  ERROR: _LOG was not deleted!")
        return False

    # Recreate structure
    print("\n--- 3.6 Recreate _LOG structure ---")
    status, body = api_post("/api/v1/nodesconfig/create-structure",
                          json.dumps({"log_root": log_root}))
    print(f"  Status: {status}")
    if isinstance(body, dict):
        print(f"  Created dirs: {body.get('created_dirs')} files: {body.get('created_files')}")

    return True

def phase4_add_node(project_id):
    """Phase 4: Add a new node via API."""
    print("\n" + "="*60)
    print("PHASE 4: ADD NODE VIA API")
    print("="*60)

    # Get current configs
    print("\n--- 4.1 Get current nodes config ---")
    status, body = api_get(f"/api/v1/nodesconfig?project_id={project_id}")
    if not isinstance(body, dict):
        print(f"  ERROR: {body}")
        return False
    configs = body.get("configs", [])
    print(f"  Current nodes: {len(configs)}")

    # Add a test node
    test_node = {
        "name": "TEST_NODE_99",
        "ip_address": "192.168.99.99",
        "tokens": [
            {"token_id": "999", "token_type": "FBC", "protocol": "telnet"},
            {"token_id": "999", "token_type": "RPC", "protocol": "telnet"},
            {"token_id": "999", "token_type": "LOG", "protocol": "telnet"}
        ]
    }
    configs.append(test_node)

    print(f"\n--- 4.2 Save configs with new test node ---")
    status, body = api_post(f"/api/v1/nodesconfig?project_id={project_id}",
                          json.dumps(configs))
    print(f"  Status: {status}")
    if isinstance(body, dict):
        print(f"  Saved: {body.get('saved')} count={body.get('count')}")

    # Verify
    print(f"\n--- 4.3 Verify new node appears ---")
    status, body = api_get(f"/api/v1/nodesconfig?project_id={project_id}")
    if isinstance(body, dict):
        saved = body.get("configs", [])
        print(f"  Nodes: {len(saved)}")
        found = any(c.get("name") == "TEST_NODE_99" for c in saved)
        print(f"  TEST_NODE_99 found: {found}")

    # Now remove the test node to clean up
    configs_clean = [c for c in configs if c.get("name") != "TEST_NODE_99"]
    status, body = api_post(f"/api/v1/nodesconfig?project_id={project_id}",
                          json.dumps(configs_clean))
    print(f"\n--- 4.4 Cleanup: removed test node (saved {len(configs_clean)} configs) ---")

    return True

def phase5_commander(project_id):
    """Phase 5: Commander right-click commands."""
    print("\n" + "="*60)
    print("PHASE 5: COMMANDER RIGHT-CLICK COMMANDS")
    print("="*60)

    # Set log root first
    print("\n--- 5.0 Set log root ---")
    status, body = api_post("/api/v1/logs/setroot",
                          json.dumps({"path": "C:\\Ships\\TEST_SHIP3"}))
    print(f"  Status: {status}")
    if isinstance(body, dict):
        print(f"  Log root set to: {body.get('log_root')}")

    # Get tree to find FBC tokens
    print("\n--- 5.1 Get tree for token info ---")
    status, body = api_get(f"/api/v1/nodesconfig/tree?project_id={project_id}&log_root=C:\\Ships\\TEST_SHIP3")
    if not isinstance(body, dict):
        print(f"  ERROR: {body}")
        return False
    tree = body.get("tree", {})
    stations = tree.get("children", [])

    # Find first station with FBC tokens
    test_station = None
    test_fbc_token = None
    test_rpc_token = None
    test_ip = None
    for s in stations:
        groups = s.get("children", [])
        test_ip = s.get("ip", "")
        for g in groups:
            if g.get("name") == "FBC" and len(g.get("children", [])) > 0:
                test_station = s.get("name")
                first_fbc = g["children"][0]
                test_fbc_token = first_fbc.get("token_id", "")
                break
            if g.get("name") == "RPC" and len(g.get("children", [])) > 0:
                first_rpc = g["children"][0]
                test_rpc_token = first_rpc.get("token_id", "")
        if test_station and test_fbc_token:
            break

    if not test_station:
        print("  ERROR: No station with FBC tokens found!")
        return False

    print(f"  Test station: {test_station}")
    print(f"  Test FBC token: {test_fbc_token}")
    print(f"  Test RPC token: {test_rpc_token}")
    print(f"  Test IP: {test_ip}")

    # Test FBC print command
    print(f"\n--- 5.2 Test FBC print (fis) command ---")
    fbc_cmd = f"print from fbc io structure {test_fbc_token}0000"
    req_body = {
        "command": fbc_cmd,
        "node_name": test_station,
        "token_type": "FBC",
        "token_id": test_fbc_token,
        "ip_address": test_ip,
        "host": "127.0.0.1",
        "port": 1234
    }
    status, body = api_post("/api/v1/telnet/execute", json.dumps(req_body), timeout=30)
    print(f"  Status: {status}")
    if isinstance(body, dict):
        print(f"  Sent: {body.get('sent')}")
        print(f"  File written: {body.get('file_written')}")
        print(f"  File path: {body.get('file_path', '')}")
        output = body.get("output", "")
        print(f"  Output length: {len(output) if isinstance(output, str) else '?'}")
        if isinstance(output, str) and len(output) > 0:
            print(f"  Output preview: {output[:200]}")
    elif isinstance(body, str):
        print(f"  Error: {body[:300]}")

    # Check if FBC file was written
    if isinstance(body, dict) and body.get("file_written"):
        file_path = body.get("file_path", "")
        print(f"\n--- 5.3 Verify FBC file written ---")
        # Check file size
        if file_path:
            check_cmd = f'for %f in ("{file_path}") do @echo %~zf'
            stdout, stderr, code = exec_cmd(f"cmd /c {check_cmd}", timeout=10)
            print(f"  File size: {stdout.strip()} bytes")
            # Check file content
            stdout, stderr, code = exec_cmd(f'type "{file_path}"', timeout=10)
            content_lines = stdout.strip().split('\n') if stdout.strip() else []
            print(f"  Content lines: {len(content_lines)}")
            if content_lines:
                print(f"  First line: {content_lines[0][:100]}")

    # Test RPC print command
    if test_rpc_token:
        print(f"\n--- 5.4 Test RPC print command ---")
        rpc_cmd = f"print from fbc rupi counters {test_rpc_token}0000"
        req_body = {
            "command": rpc_cmd,
            "node_name": test_station,
            "token_type": "RPC",
            "token_id": test_rpc_token,
            "ip_address": test_ip,
            "host": "127.0.0.1",
            "port": 1234
        }
        status, body = api_post("/api/v1/telnet/execute", json.dumps(req_body), timeout=30)
        print(f"  Status: {status}")
        if isinstance(body, dict):
            print(f"  File written: {body.get('file_written')}")
            print(f"  File path: {body.get('file_path', '')}")
        elif isinstance(body, str):
            print(f"  Response: {body[:200]}")

    # Test RPC clear command
    if test_rpc_token:
        print(f"\n--- 5.5 Test RPC clear command ---")
        clear_cmd = f"clear fbc rupi counters {test_rpc_token}0000"
        req_body = {
            "command": clear_cmd,
            "node_name": test_station,
            "token_type": "RPC",
            "token_id": test_rpc_token,
            "ip_address": test_ip,
            "host": "127.0.0.1",
            "port": 1234
        }
        status, body = api_post("/api/v1/telnet/execute", json.dumps(req_body), timeout=30)
        print(f"  Status: {status}")
        if isinstance(body, dict):
            print(f"  Sent: {body.get('sent')}")

    # Test bstool errlog
    print(f"\n--- 5.6 Test BsTool errlog ---")
    req_body = {
        "server_name": test_station,
        "timeout": 10
    }
    status, body = api_post("/api/v1/bstool/errlog", json.dumps(req_body), timeout=30)
    print(f"  Status: {status}")
    if isinstance(body, dict):
        if body.get("error"):
            print(f"  Error: {body.get('message', '')[:200]}")
        else:
            print(f"  Messages: {body.get('count', 0)}")
            print(f"  File written: {body.get('file_written', False)}")
    elif isinstance(body, str):
        print(f"  Response: {body[:200]}")

    # Check tree status changes
    print(f"\n--- 5.7 Check tree status after commands ---")
    status, body = api_get(f"/api/v1/nodesconfig/tree?project_id={project_id}&log_root=C:\\Ships\\TEST_SHIP3")
    if isinstance(body, dict):
        tree = body.get("tree", {})
        for s in tree.get("children", []):
            if s.get("name") == test_station:
                for g in s.get("children", []):
                    for f in g.get("children", []):
                        lc = f.get("line_count", 0)
                        st = f.get("status", "?")
                        if lc > 0:
                            print(f"  {g.get('name')}/{f.get('name')}: lines={lc} status={st}")

    return True

def phase6_command_queue(project_id):
    """Phase 6: Sequential command queue."""
    print("\n" + "="*60)
    print("PHASE 6: SEQUENTIAL COMMAND QUEUE")
    print("="*60)

    # Get a node name from the config
    print("\n--- 6.1 Get node names ---")
    status, body = api_get(f"/api/v1/nodesconfig?project_id={project_id}")
    if not isinstance(body, dict):
        print(f"  ERROR: {body}")
        return False
    configs = body.get("configs", [])
    if len(configs) == 0:
        print("  ERROR: No nodes configured!")
        return False

    # Find a node with FBC tokens
    test_node_name = None
    for c in configs:
        has_fbc = any(t.get("token_type") == "FBC" for t in c.get("tokens", []))
        if has_fbc:
            test_node_name = c.get("name")
            print(f"  Test node: {test_node_name}")
            break

    if not test_node_name:
        print("  ERROR: No node with FBC tokens found!")
        return False

    # Add batch commands for single node
    print(f"\n--- 6.2 Add batch commands for node: {test_node_name} ---")
    req_body = {"node_name": test_node_name}
    status, body = api_post(f"/api/v1/commandqueue/batch-node?project_id={project_id}",
                           json.dumps(req_body))
    print(f"  Status: {status}")
    if isinstance(body, dict):
        print(f"  Batch added: {body.get('batch_added')}")
        print(f"  Total commands: {body.get('total')}")
    elif isinstance(body, str):
        print(f"  Error: {body[:200]}")
        return False

    # Start queue
    print(f"\n--- 6.3 Start queue ---")
    status, body = api_post("/api/v1/commandqueue/start", "{}")
    print(f"  Status: {status}")
    print(f"  Response: {body}")

    # Poll status until completed
    print(f"\n--- 6.4 Poll queue status ---")
    for i in range(30):
        time.sleep(2)
        status, body = api_get("/api/v1/commandqueue/status")
        if isinstance(body, dict):
            current = body.get("current", 0)
            total = body.get("total", 0)
            state = body.get("state", "?")
            cmds = body.get("commands", [])
            completed = sum(1 for c in cmds if c.get("status") == "completed")
            failed = sum(1 for c in cmds if c.get("status") == "failed")
            print(f"  [{i}] state={state} current={current}/{total} completed={completed} failed={failed}")
            if state in ("done", "idle") or (state == "idle" and current >= total):
                break
        else:
            print(f"  [{i}] Response: {body}")

    # Check final status
    status, body = api_get("/api/v1/commandqueue/status")
    if isinstance(body, dict):
        cmds = body.get("commands", [])
        print(f"\n  Final: {len(cmds)} commands")
        for c in cmds[:5]:
            print(f"    {c.get('node_name')}/{c.get('type')}/{c.get('token_id')}: {c.get('status')}")
        if len(cmds) > 5:
            print(f"    ... and {len(cmds)-5} more")

    # Test pause/resume/cancel
    print(f"\n--- 6.5 Test pause/resume/cancel ---")
    # Add another batch
    status, body = api_post(f"/api/v1/commandqueue/batch-node?project_id={project_id}",
                           json.dumps({"node_name": test_node_name}))
    if isinstance(body, dict):
        total = body.get("total", 0)
        print(f"  Added batch: {total} commands")

    # Start
    status, body = api_post("/api/v1/commandqueue/start", "{}")
    print(f"  Start: {status}")

    # Wait a moment then pause
    time.sleep(1)
    status, body = api_post("/api/v1/commandqueue/pause", "{}")
    print(f"  Pause: {status} {body if isinstance(body, dict) else ''}")

    # Check status
    time.sleep(1)
    status, body = api_get("/api/v1/commandqueue/status")
    if isinstance(body, dict):
        state = body.get("state", "?")
        print(f"  State after pause: {state}")

    # Resume
    status, body = api_post("/api/v1/commandqueue/resume", "{}")
    print(f"  Resume: {status}")

    # Wait for completion
    for i in range(20):
        time.sleep(2)
        status, body = api_get("/api/v1/commandqueue/status")
        if isinstance(body, dict):
            state = body.get("state", "?")
            current = body.get("current", 0)
            total = body.get("total", 0)
            print(f"  [{i}] state={state} {current}/{total}")
            if state in ("done", "idle"):
                break

    # Test cancel
    print(f"\n--- 6.6 Test cancel ---")
    status, body = api_post(f"/api/v1/commandqueue/batch-node?project_id={project_id}",
                           json.dumps({"node_name": test_node_name}))
    status, body = api_post("/api/v1/commandqueue/start", "{}")
    time.sleep(1)
    status, body = api_post("/api/v1/commandqueue/cancel", "{}")
    print(f"  Cancel: {status}")
    time.sleep(1)
    status, body = api_get("/api/v1/commandqueue/status")
    if isinstance(body, dict):
        print(f"  State after cancel: {body.get('state', '?')}")

    return True

def phase7_all_nodes(project_id):
    """Phase 7: All-node execution."""
    print("\n" + "="*60)
    print("PHASE 7: ALL-NODE EXECUTION")
    print("="*60)

    # This is tricky since we need all nodes. Let's just try with batch (no node_name filter)
    # Actually batch-node requires node_name. Let's use batch instead.
    print("\n--- 7.1 Add batch for all nodes ---")
    status, body = api_post(f"/api/v1/commandqueue/batch?project_id={project_id}", "{}")
    print(f"  Status: {status}")
    if isinstance(body, dict):
        print(f"  Total: {body.get('total')}")
    elif isinstance(body, str):
        print(f"  Response: {body[:200]}")

    # Start
    print(f"\n--- 7.2 Start queue ---")
    status, body = api_post("/api/v1/commandqueue/start", "{}")
    print(f"  Status: {status}")

    # Poll
    print(f"\n--- 7.3 Poll until done ---")
    for i in range(60):
        time.sleep(3)
        status, body = api_get("/api/v1/commandqueue/status")
        if isinstance(body, dict):
            state = body.get("state", "?")
            current = body.get("current", 0)
            total = body.get("total", 0)
            cmds = body.get("commands", [])
            completed = sum(1 for c in cmds if c.get("status") == "completed")
            failed = sum(1 for c in cmds if c.get("status") == "failed")
            print(f"  [{i}] state={state} {current}/{total} ok={completed} fail={failed}")
            if state in ("done", "idle"):
                break
        else:
            print(f"  [{i}] {body}")

    # Verify files written for multiple stations
    print(f"\n--- 7.4 Verify files written for multiple stations ---")
    stdout, stderr, code = exec_cmd("dir C:\\Ships\\TEST_SHIP3\\_LOG /s /b | findstr /c:\".fbc\" | find /c /v \"\"", timeout=15)
    print(f"  FBC files: {stdout.strip()}")
    stdout, stderr, code = exec_cmd("dir C:\\Ships\\TEST_SHIP3\\_LOG /s /b | findstr /c:\".rpc\" | find /c /v \"\"", timeout=15)
    print(f"  RPC files: {stdout.strip()}")
    # Check for non-empty files
    stdout, stderr, code = exec_cmd('forfiles /P C:\\Ships\\TEST_SHIP3\\_LOG /S /M *.fbc /C "cmd /c if @fsize GEQ 1 echo @path @fsize"', timeout=15)
    non_empty_fbc = [l for l in stdout.strip().split('\n') if l.strip()]
    print(f"  Non-empty FBC files: {len(non_empty_fbc)}")

    return True

def phase8_reports(project_id):
    """Phase 8: Report generation."""
    print("\n" + "="*60)
    print("PHASE 8: REPORT GENERATION")
    print("="*60)

    log_root = "C:\\Ships\\TEST_SHIP3"

    # Generate DOCX report
    print("\n--- 8.1 Generate DOCX report ---")
    req_body = {
        "node_addresses": ["*"],
        "format": "docx",
        "log_root": log_root,
        "project_id": project_id
    }
    status, body = api_post("/api/v1/reports/generate", json.dumps(req_body), timeout=60)
    print(f"  Status: {status}")
    if isinstance(body, dict):
        print(f"  Report ID: {body.get('report_id', '?')}")
        print(f"  Status: {body.get('status', '?')}")
        print(f"  Format: {body.get('format', '?')}")
        print(f"  File path: {body.get('file_path', '?')}")
        file_size = body.get('file_size')
        print(f"  File size: {file_size}")
        if body.get("error"):
            print(f"  Error: {body.get('message', '')[:200]}")
    elif isinstance(body, str):
        print(f"  Response: {body[:300]}")

    # Generate PDF report
    print(f"\n--- 8.2 Generate PDF report ---")
    req_body = {
        "node_addresses": ["*"],
        "format": "pdf",
        "log_root": log_root,
        "project_id": project_id
    }
    status, body = api_post("/api/v1/reports/generate", json.dumps(req_body), timeout=60)
    print(f"  Status: {status}")
    if isinstance(body, dict):
        print(f"  Report ID: {body.get('report_id', '?')}")
        print(f"  Status: {body.get('status', '?')}")
        print(f"  File size: {body.get('file_size', '?')}")
        if body.get("error"):
            print(f"  Error: {body.get('message', '')[:200]}")

    # Generate JSON report
    print(f"\n--- 8.3 Generate JSON report ---")
    req_body = {
        "node_addresses": ["*"],
        "format": "json",
        "log_root": log_root,
        "project_id": project_id
    }
    status, body = api_post("/api/v1/reports/generate", json.dumps(req_body), timeout=60)
    print(f"  Status: {status}")
    if isinstance(body, dict):
        print(f"  Report ID: {body.get('report_id', '?')}")
        print(f"  Status: {body.get('status', '?')}")
        print(f"  File size: {body.get('file_size', '?')}")
        if body.get("error"):
            print(f"  Error: {body.get('message', '')[:200]}")

    # List reports
    print(f"\n--- 8.4 List reports ---")
    status, body = api_get("/api/v1/reports")
    print(f"  Status: {status}")
    if isinstance(body, dict):
        reports = body.get("reports", [])
        print(f"  Reports: {len(reports)}")
        for r in reports:
            print(f"    ID={r.get('report_id', '?')[:16]}... fmt={r.get('format')} status={r.get('status')} size={r.get('file_size', '?')}")

    # Verify report files exist
    print(f"\n--- 8.5 Verify report files ---")
    report_dir = "C:\\Users\\dna\\AppData\\Local\\Temp\\1\\logreport-reports"
    stdout, stderr, code = exec_cmd(f'dir "{report_dir}" /b', timeout=10)
    files = stdout.strip().split('\n') if stdout.strip() else []
    print(f"  Report dir: {report_dir}")
    print(f"  Files: {len(files)}")
    for f in files:
        # Get file size
        stdout2, _, _ = exec_cmd(f'cmd /c for %f in ("{report_dir}\\{f}") do @echo %~zf', timeout=10)
        size = stdout2.strip()
        print(f"    {f} ({size} bytes)")

    return True

def main():
    print("LOGReport Full End-to-End Test")
    print("="*60)

    # Check health first
    if not check_health():
        print("ERROR: LOGReport is not running or health check failed!")
        sys.exit(1)

    # Run all phases
    results = {}

    project_id = phase1_project_mgmt()
    results["phase1"] = project_id is not None
    if not results["phase1"]:
        print("Phase 1 failed, stopping.")
        sys.exit(1)

    results["phase2"] = phase2_load_nodes(project_id)
    if not results["phase2"]:
        print("Phase 2 failed, stopping.")
        sys.exit(1)

    results["phase3"] = phase3_structure(project_id)
    results["phase4"] = phase4_add_node(project_id)
    results["phase5"] = phase5_commander(project_id)
    results["phase6"] = phase6_command_queue(project_id)
    results["phase7"] = phase7_all_nodes(project_id)
    results["phase8"] = phase8_reports(project_id)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for phase, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {phase}: {status}")

    all_pass = all(results.values())
    print(f"\n  Overall: {'ALL PASS' if all_pass else 'SOME FAILURES'}")
    sys.exit(0 if all_pass else 1)

if __name__ == "__main__":
    main()