from pathlib import Path
import re
import pytest
from typing import List, Dict

# Sys file content provided in the problem description
sys_file_content_ap = """
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

sys_file_content_al = """
// HW     LID           PARAMETER          COMMENT

:e:hw:501 AL01		pxe:sys-csg2	// AL01 Node
:e:hw:502 AL01_t1	-               // LIS Token 1
:e:hw:503 AL01_t2       -               // LIS Token 2

:e:hw:511 AL02		pxe:sys-csg2	// AL02 Node
:e:hw:512 AL02_t1	-               // LIS Token 1

:e:hw:521 AL03		pxe:sys-csg2	// AL03 Node

:e:hw:531 AL08		pxe:sys-csg2	// AL08 Node
:e:hw:532 AL08_t1	-               // LIS Token 1
:e:hw:533 AL08_t2       -               // LIS Token 2
:e:hw:534 AL08_t3       -               // LIS Token 3
"""

def parse_sys_file(file_path: str) -> List[Dict]:
    nodes_data = {}

    # Regex patterns
    ap_main_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+(AP\d{2})\s+pxe:sys-csg2.*")
    ap_main_m_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+(AP\d{2})_main\s+pxe:sys-csg2.*")
    ap_reserve_r_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+(AP\d{2})_reserve\s+pxe:sys-csg2.*")
    al_main_node_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+(AL\d{2})\s+.*")
    token_entry_regex = re.compile(r"^:e:hw:([0-9a-fA-F]{2,4})\s+((?:AP|AL)\d{2})((?:_m\d|_r\d|_t\d)+)\s+.*")
    
    lines = []
    try:
        # For testing purposes, we'll treat file_path as content if it's not a real path
        if Path(file_path).exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = file_path.splitlines() # Assume file_path is content for testing
    except Exception as e:
        raise Exception(f"Error reading file {file_path}: {str(e)}")

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
        elif al_match := al_main_node_regex.match(line):
            lid, node_name = al_match.groups()
            nodes_data[node_name] = {
                "name": node_name,
                "ip": "",
                "tokens": [],
                "types": ["FBC", "RPC", "LOG", "LIS"]
            }

    # Second pass: Extract tokens and assign to the correct node
    for line in lines:
        token_match = token_entry_regex.match(line)
        if token_match:
            token_lid, node_prefix, suffix = token_match.groups()
            
            parent_node_name = None
            if suffix.startswith("_m"):
                if f"{node_prefix}m" in nodes_data:
                    parent_node_name = f"{node_prefix}m"
                elif node_prefix in nodes_data:
                    parent_node_name = node_prefix
            elif suffix.startswith("_r"):
                if f"{node_prefix}r" in nodes_data:
                    parent_node_name = f"{node_prefix}r"
            else: # For main nodes (APXX or ALXX)
                if node_prefix in nodes_data:
                    parent_node_name = node_prefix
            
            if parent_node_name and token_lid not in nodes_data[parent_node_name]["tokens"]:
                nodes_data[parent_node_name]["tokens"].append(token_lid)
    
    # Sort tokens for consistent output
    for node_name in nodes_data:
        nodes_data[node_name]["tokens"].sort()

    return list(nodes_data.values())

@pytest.fixture
def sample_sys_file_content_ap():
    return sys_file_content_ap

@pytest.fixture
def sample_sys_file_content_al():
    return sys_file_content_al

def test_sys_file_parsing_ap01(sample_sys_file_content_ap):
    parsed_data = parse_sys_file(sample_sys_file_content_ap)
    ap01_node = next((node for node in parsed_data if node["name"] == "AP01"), None)
    assert ap01_node is not None
    assert ap01_node["name"] == "AP01"
    assert ap01_node["ip"] == ""
    assert ap01_node["tokens"] == ["162", "163"]
    assert ap01_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap02_main(sample_sys_file_content_ap):
    parsed_data = parse_sys_file(sample_sys_file_content_ap)
    ap02m_node = next((node for node in parsed_data if node["name"] == "AP02m"), None)
    assert ap02m_node is not None
    assert ap02m_node["name"] == "AP02m"
    assert ap02m_node["ip"] == ""
    assert ap02m_node["tokens"] == ["182", "183"]
    assert ap02m_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap02_reserve(sample_sys_file_content_ap):
    parsed_data = parse_sys_file(sample_sys_file_content_ap)
    ap02r_node = next((node for node in parsed_data if node["name"] == "AP02r"), None)
    assert ap02r_node is not None
    assert ap02r_node["name"] == "AP02r"
    assert ap02r_node["ip"] == ""
    assert ap02r_node["tokens"] == ["382", "383"]
    assert ap02r_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap03_main(sample_sys_file_content_ap):
    parsed_data = parse_sys_file(sample_sys_file_content_ap)
    ap03m_node = next((node for node in parsed_data if node["name"] == "AP03m"), None)
    assert ap03m_node is not None
    assert ap03m_node["name"] == "AP03m"
    assert ap03m_node["ip"] == ""
    assert ap03m_node["tokens"] == ["1a2", "1a3"]
    assert ap03m_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap03_reserve(sample_sys_file_content_ap):
    parsed_data = parse_sys_file(sample_sys_file_content_ap)
    ap03r_node = next((node for node in parsed_data if node["name"] == "AP03r"), None)
    assert ap03r_node is not None
    assert ap03r_node["name"] == "AP03r"
    assert ap03r_node["ip"] == ""
    assert ap03r_node["tokens"] == ["3a2", "3a3"]
    assert ap03r_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap04(sample_sys_file_content_ap):
    parsed_data = parse_sys_file(sample_sys_file_content_ap)
    ap04_node = next((node for node in parsed_data if node["name"] == "AP04"), None)
    assert ap04_node is not None
    assert ap04_node["name"] == "AP04"
    assert ap04_node["ip"] == ""
    assert ap04_node["tokens"] == ["1c2", "1c3"]
    assert ap04_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap05(sample_sys_file_content_ap):
    parsed_data = parse_sys_file(sample_sys_file_content_ap)
    ap05_node = next((node for node in parsed_data if node["name"] == "AP05"), None)
    assert ap05_node is not None
    assert ap05_node["name"] == "AP05"
    assert ap05_node["ip"] == ""
    assert ap05_node["tokens"] == ["1e2", "1e3"]
    assert ap05_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap06(sample_sys_file_content_ap):
    parsed_data = parse_sys_file(sample_sys_file_content_ap)
    ap06_node = next((node for node in parsed_data if node["name"] == "AP06"), None)
    assert ap06_node is not None
    assert ap06_node["name"] == "AP06"
    assert ap06_node["ip"] == ""
    assert ap06_node["tokens"] == ["202", "203"]
    assert ap06_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap07_main(sample_sys_file_content_ap):
    parsed_data = parse_sys_file(sample_sys_file_content_ap)
    ap07m_node = next((node for node in parsed_data if node["name"] == "AP07m"), None)
    assert ap07m_node is not None
    assert ap07m_node["name"] == "AP07m"
    assert ap07m_node["ip"] == ""
    assert ap07m_node["tokens"] == ["222"] # Only _m2 is present in the example
    assert ap07m_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_ap07_reserve(sample_sys_file_content_ap):
    parsed_data = parse_sys_file(sample_sys_file_content_ap)
    ap07r_node = next((node for node in parsed_data if node["name"] == "AP07r"), None)
    assert ap07r_node is not None
    assert ap07r_node["name"] == "AP07r"
    assert ap07r_node["ip"] == ""
    assert ap07r_node["tokens"] == ["422"] # Only _r2 is present in the example
    assert ap07r_node["types"] == ["FBC", "RPC", "LOG"]

def test_sys_file_parsing_al01(sample_sys_file_content_al):
    parsed_data = parse_sys_file(sample_sys_file_content_al)
    al01_node = next((node for node in parsed_data if node["name"] == "AL01"), None)
    assert al01_node is not None
    assert al01_node["name"] == "AL01"
    assert al01_node["ip"] == ""
    assert al01_node["tokens"] == ["502", "503"]
    assert al01_node["types"] == ["FBC", "RPC", "LOG", "LIS"]

def test_sys_file_parsing_al02(sample_sys_file_content_al):
    parsed_data = parse_sys_file(sample_sys_file_content_al)
    al02_node = next((node for node in parsed_data if node["name"] == "AL02"), None)
    assert al02_node is not None
    assert al02_node["name"] == "AL02"
    assert al02_node["ip"] == ""
    assert al02_node["tokens"] == ["512"]
    assert al02_node["types"] == ["FBC", "RPC", "LOG", "LIS"]

def test_sys_file_parsing_al03(sample_sys_file_content_al):
    parsed_data = parse_sys_file(sample_sys_file_content_al)
    al03_node = next((node for node in parsed_data if node["name"] == "AL03"), None)
    assert al03_node is not None
    assert al03_node["name"] == "AL03"
    assert al03_node["ip"] == ""
    assert al03_node["tokens"] == []
    assert al03_node["types"] == ["FBC", "RPC", "LOG", "LIS"]

def test_sys_file_parsing_al08(sample_sys_file_content_al):
    parsed_data = parse_sys_file(sample_sys_file_content_al)
    al08_node = next((node for node in parsed_data if node["name"] == "AL08"), None)
    assert al08_node is not None
    assert al08_node["name"] == "AL08"
    assert al08_node["ip"] == ""
    assert al08_node["tokens"] == ["532", "533", "534"]
    assert al08_node["types"] == ["FBC", "RPC", "LOG", "LIS"]

def test_all_nodes_present(sample_sys_file_content_ap, sample_sys_file_content_al):
    parsed_data_ap = parse_sys_file(sample_sys_file_content_ap)
    parsed_data_al = parse_sys_file(sample_sys_file_content_al)
    
    expected_node_names_ap = {
        "AP01", "AP02m", "AP02r", "AP03m", "AP03r",
        "AP04", "AP05", "AP06", "AP07m", "AP07r"
    }
    expected_node_names_al = {
        "AL01", "AL02", "AL03", "AL08"
    }
    
    actual_node_names_ap = {node["name"] for node in parsed_data_ap}
    actual_node_names_al = {node["name"] for node in parsed_data_al}
    
    assert actual_node_names_ap == expected_node_names_ap
    assert actual_node_names_al == expected_node_names_al

def test_no_ip_addresses_extracted(sample_sys_file_content_ap, sample_sys_file_content_al):
    parsed_data_ap = parse_sys_file(sample_sys_file_content_ap)
    parsed_data_al = parse_sys_file(sample_sys_file_content_al)
    
    for node in parsed_data_ap:
        assert node["ip"] == ""
    for node in parsed_data_al:
        assert node["ip"] == ""

def test_default_types_assigned(sample_sys_file_content_ap, sample_sys_file_content_al):
    parsed_data_ap = parse_sys_file(sample_sys_file_content_ap)
    parsed_data_al = parse_sys_file(sample_sys_file_content_al)
    
    for node in parsed_data_ap:
        assert node["types"] == ["FBC", "RPC", "LOG"]
    for node in parsed_data_al:
        assert node["types"] == ["FBC", "RPC", "LOG", "LIS"]
