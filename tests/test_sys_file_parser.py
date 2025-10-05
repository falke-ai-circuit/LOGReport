import re
import pytest

# Sys file content provided in the problem description
sys_file_content = """
// HW     LID           PARAMETER          COMMENT

:e:hw:161 AP01		pxe:sys-csg2	// AP01 PCS
:e:hw:162 AP01_m2	-               // FBC2
:e:hw:163 AP01_m3       -               // FBC3

:e:hw:181 AP02_main	pxe:sys-csg2	// AP02 Main PCS
:e:hw:182 AP02_m2	-               // FBC2
:e:hw:183 AP02_m3       -               // FBC3

:e:hw:381 AP02_reserve	pxe:sys-csg2	// AP02 Reserve PCS
:e:hw:382 AP02_r2	-               // FBC2
:e:hw:383 AP02_r3       -               // FBC3

:e:hw:1a1 AP03_main	pxe:sys-csg2	// AP03 Main PCS
:e:hw:1a2 AP03_m2	-               // FBC2
:e:hw:1a3 AP03_m3       -               // FBC3

:e:hw:3a1 AP03_reserve	pxe:sys-csg2	// AP03 Reserve PCS
:e:hw:3a2 AP03_r2	-               // FBC2
:e:hw:3a3 AP03_r3       -               // FBC3

:e:hw:1c1 AP04		pxe:sys-csg2	// AP04 PCS
:e:hw:1c2 AP04_m2	-               // FBC2
:e:hw:1c3 AP04_m3       -               // FBC3

:e:hw:1e1 AP05		pxe:sys-csg2	// AP05 PCS
:e:hw:1e2 AP05_m2	-               // FBC2
:e:hw:1e3 AP05_m3       -               // FBC3

:e:hw:201 AP06		pxe:sys-csg2	// AP06 PCS
:e:hw:202 AP06_m2	-               // FBC2
:e:hw:203 AP06_m3       -               // FBC3

:e:hw:221 AP07_main	pxe:sys-csg2	// AP07 Main PCS
:e:hw:222 AP07_m2	-               // FBC2

:e:hw:421 AP07_reserve	pxe:sys-csg2	// AP07 Reserve PCS
:e:hw:422 AP07_r2	-               // FBC2 - in this particular case it should be node AP01, tokens 162,163 ( so basically we will use _m parsing for tokens if _m4 exists and its tokens is for example 164 we use that ) ip adresss we will not use from this file, AP02_main will be token AP02m with tokens 182,183, AP02_reserve will be AP02r tokens 382, 383 etc
"""

def parse_sys_file(content):
    nodes_data = {}

    # Regex patterns
    ap_main_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{3})\s+(AP\d{2})\s+pxe:sys-csg2.*")
    ap_main_m_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{3})\s+(AP\d{2})_main\s+pxe:sys-csg2.*")
    ap_reserve_r_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{3})\s+(AP\d{2})_reserve\s+pxe:sys-csg2.*")
    token_entry_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{3})\s+(AP\d{2})(_m|_r)\s+.*")

    lines = content.splitlines()
    
    # First pass: Identify main nodes and initialize their data
    for line in lines:
        match_ap = ap_main_node_regex.match(line)
        match_ap_main = ap_main_m_node_regex.match(line)
        match_ap_reserve = ap_reserve_r_node_regex.match(line)

        if match_ap:
            lid, node_name_prefix = match_ap.groups()
            full_node_name = node_name_prefix
            nodes_data[full_node_name] = {
                "name": full_node_name,
                "ip": "",
                "tokens": [],
                "types": ["FBC", "RPC", "LOG"]
            }
        elif match_ap_main:
            lid, node_name_prefix = match_ap_main.groups()
            full_node_name = f"{node_name_prefix}m"
            nodes_data[full_node_name] = {
                "name": full_node_name,
                "ip": "",
                "tokens": [],
                "types": ["FBC", "RPC", "LOG"]
            }
        elif match_ap_reserve:
            lid, node_name_prefix = match_ap_reserve.groups()
            full_node_name = f"{node_name_prefix}r"
            nodes_data[full_node_name] = {
                "name": full_node_name,
                "ip": "",
                "tokens": [],
                "types": ["FBC", "RPC", "LOG"]
            }

    # Second pass: Extract tokens and assign to the correct node
    for line in lines:
        token_match = token_entry_regex.match(line)
        if token_match:
            token_lid, ap_prefix, suffix = token_match.groups()
            
            parent_node_name = None
            if suffix.startswith("_m"):
                # Could be APXX or APXXm
                if ap_prefix in nodes_data: # Check for AP01, AP04, etc.
                    parent_node_name = ap_prefix
                elif f"{ap_prefix}m" in nodes_data: # Check for AP02m, AP03m, etc.
                    parent_node_name = f"{ap_prefix}m"
            elif suffix.startswith("_r"):
                # Must be APXXr
                if f"{ap_prefix}r" in nodes_data: # Check for AP02r, AP03r, etc.
                    parent_node_name = f"{ap_prefix}r"
            
            if parent_node_name and token_lid not in nodes_data[parent_node_name]["tokens"]:
                nodes_data[parent_node_name]["tokens"].append(token_lid)
    
    # Sort tokens for consistent output
    for node_name in nodes_data:
        nodes_data[node_name]["tokens"].sort()

    return list(nodes_data.values())

@pytest.fixture
def sample_sys_file_content():
    return sys_file_content

def test_sys_file_parsing_ap01(sample_sys_file_content):
    parsed_data = parse_sys_file(sample_sys_file_content)
    ap01_node = next((node for node in parsed_data if node["name"] == "AP01"), None)
    assert ap01_node is not None
    assert ap01_node["name"] == "AP01"
    assert ap01_node["ip"] == ""
    assert ap01_node["tokens"] == ["162", "163"]
    assert ap01_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap02_main(sample_sys_file_content):
    parsed_data = parse_sys_file(sample_sys_file_content)
    ap02m_node = next((node for node in parsed_data if node["name"] == "AP02m"), None)
    assert ap02m_node is not None
    assert ap02m_node["name"] == "AP02m"
    assert ap02m_node["ip"] == ""
    assert ap02m_node["tokens"] == ["182", "183"]
    assert ap02m_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap02_reserve(sample_sys_file_content):
    parsed_data = parse_sys_file(sample_sys_file_content)
    ap02r_node = next((node for node in parsed_data if node["name"] == "AP02r"), None)
    assert ap02r_node is not None
    assert ap02r_node["name"] == "AP02r"
    assert ap02r_node["ip"] == ""
    assert ap02r_node["tokens"] == ["382", "383"]
    assert ap02r_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap03_main(sample_sys_file_content):
    parsed_data = parse_sys_file(sample_sys_file_content)
    ap03m_node = next((node for node in parsed_data if node["name"] == "AP03m"), None)
    assert ap03m_node is not None
    assert ap03m_node["name"] == "AP03m"
    assert ap03m_node["ip"] == ""
    assert ap03m_node["tokens"] == ["1a2", "1a3"]
    assert ap03m_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap03_reserve(sample_sys_file_content):
    parsed_data = parse_sys_file(sample_sys_file_content)
    ap03r_node = next((node for node in parsed_data if node["name"] == "AP03r"), None)
    assert ap03r_node is not None
    assert ap03r_node["name"] == "AP03r"
    assert ap03r_node["ip"] == ""
    assert ap03r_node["tokens"] == ["3a2", "3a3"]
    assert ap03r_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap04(sample_sys_file_content):
    parsed_data = parse_sys_file(sample_sys_file_content)
    ap04_node = next((node for node in parsed_data if node["name"] == "AP04"), None)
    assert ap04_node is not None
    assert ap04_node["name"] == "AP04"
    assert ap04_node["ip"] == ""
    assert ap04_node["tokens"] == ["1c2", "1c3"]
    assert ap04_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap05(sample_sys_file_content):
    parsed_data = parse_sys_file(sample_sys_file_content)
    ap05_node = next((node for node in parsed_data if node["name"] == "AP05"), None)
    assert ap05_node is not None
    assert ap05_node["name"] == "AP05"
    assert ap05_node["ip"] == ""
    assert ap05_node["tokens"] == ["1e2", "1e3"]
    assert ap05_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap06(sample_sys_file_content):
    parsed_data = parse_sys_file(sample_sys_file_content)
    ap06_node = next((node for node in parsed_data if node["name"] == "AP06"), None)
    assert ap06_node is not None
    assert ap06_node["name"] == "AP06"
    assert ap06_node["ip"] == ""
    assert ap06_node["tokens"] == ["202", "203"]
    assert ap06_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap07_main(sample_sys_file_content):
    parsed_data = parse_sys_file(sample_sys_file_content)
    ap07m_node = next((node for node in parsed_data if node["name"] == "AP07m"), None)
    assert ap07m_node is not None
    assert ap07m_node["name"] == "AP07m"
    assert ap07m_node["ip"] == ""
    assert ap07m_node["tokens"] == ["222"] # Only _m2 is present in the example
    assert ap07m_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap07_reserve(sample_sys_file_content):
    parsed_data = parse_sys_file(sample_sys_file_content)
    ap07r_node = next((node for node in parsed_data if node["name"] == "AP07r"), None)
    assert ap07r_node is not None
    assert ap07r_node["name"] == "AP07r"
    assert ap07r_node["ip"] == ""
    assert ap07r_node["tokens"] == ["422"] # Only _r2 is present in the example
    assert ap07r_node["types"] == ["FBC", "RPC", "LOG"]

def test_all_nodes_present(sample_sys_file_content):
    parsed_data = parse_sys_file(sample_sys_file_content)
    expected_node_names = {
        "AP01", "AP02m", "AP02r", "AP03m", "AP03r",
        "AP04", "AP05", "AP06", "AP07m", "AP07r"
    }
    actual_node_names = {node["name"] for node in parsed_data}
    assert actual_node_names == expected_node_names

def test_no_ip_addresses_extracted(sample_sys_file_content):
    parsed_data = parse_sys_file(sample_sys_file_content)
    for node in parsed_data:
        assert node["ip"] == ""

def test_default_types_assigned(sample_sys_file_content):
    parsed_data = parse_sys_file(sample_sys_file_content)
    for node in parsed_data:
        assert node["types"] == ["FBC", "RPC", "LOG"]
