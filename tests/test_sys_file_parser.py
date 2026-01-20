"""
Tests for the SYS file parser
"""
import pytest
import os
import tempfile
from src.commander.utils.sys_file_parser import (
    SysFileParser, SysEntry, SysFileInfo,
    parse_sys_file, get_tokens_from_sys_file
)


class TestSysFileParser:
    """Test cases for SysFileParser"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = SysFileParser()
        
    def test_parse_entry_with_pxe_csg2(self):
        """Test parsing entry with pxe:sys-csg2 config"""
        line = ":e:hw:501   AL01          pxe:sys-csg2    // For single LIS."
        entry = self.parser._parse_line(line, 1)
        
        assert entry is not None
        assert entry.hardware_address == "501"
        assert entry.lid == "AL01"
        assert entry.config == "pxe:sys-csg2"
        assert entry.comment == "For single LIS."
    
    def test_parse_entry_with_pxe_csg3(self):
        """Test parsing entry with pxe:sys-csg3 config"""
        line = ":e:hw:501   AL01          pxe:sys-csg3    // Alternative config."
        entry = self.parser._parse_line(line, 1)
        
        assert entry is not None
        assert entry.hardware_address == "501"
        assert entry.lid == "AL01"
        assert entry.config == "pxe:sys-csg3"
    
    def test_parse_entry_with_pxe_lite(self):
        """Test parsing entry with pxe:sys-lite config"""
        line = ":e:hw:501   AL01          pxe:sys-lite"
        entry = self.parser._parse_line(line, 1)
        
        assert entry is not None
        assert entry.hardware_address == "501"
        assert entry.lid == "AL01"
        assert entry.config == "pxe:sys-lite"
        assert entry.comment == ""
    
    def test_parse_entry_with_dash_config(self):
        """Test parsing entry with dash (-) config"""
        line = ":e:hw:5aa   AD01         -"
        entry = self.parser._parse_line(line, 1)
        
        assert entry is not None
        assert entry.hardware_address == "5aa"
        assert entry.lid == "AD01"
        assert entry.config == "-"
    
    def test_parse_entry_with_tabs(self):
        """Test parsing entry with tab separators"""
        line = ":e:hw:64a   BD01\t-"
        entry = self.parser._parse_line(line, 1)
        
        assert entry is not None
        assert entry.hardware_address == "64a"
        assert entry.lid == "BD01"
        assert entry.config == "-"
    
    def test_parse_pcs_main_reserve(self):
        """Test parsing PCS main/reserve entries"""
        main_line = ":e:hw:161   AP01_main    pxe:sys-csg2      // Main PCS."
        reserve_line = ":e:hw:361   AP01_reserve pxe:sys-csg2      // Reserve PCS."
        
        main_entry = self.parser._parse_line(main_line, 1)
        reserve_entry = self.parser._parse_line(reserve_line, 2)
        
        assert main_entry is not None
        assert main_entry.lid == "AP01_main"
        
        assert reserve_entry is not None
        assert reserve_entry.lid == "AP01_reserve"
    
    def test_parse_fbc_card_entry(self):
        """Test parsing FBC card entries"""
        line = ":e:hw:162   AP01_m2       pxe:sys-csg2    // Main PCS's FBC card in slot2."
        entry = self.parser._parse_line(line, 1)
        
        assert entry is not None
        assert entry.hardware_address == "162"
        assert entry.lid == "AP01_m2"
        assert entry.config == "pxe:sys-csg2"
    
    def test_skip_comment_lines(self):
        """Test that pure comment lines are skipped"""
        # Comments should return None when parsed
        line = "// This is a comment"
        entry = self.parser._parse_line(line, 1)
        assert entry is None
    
    def test_skip_commented_entry(self):
        """Test that commented-out entries are not parsed"""
        # A line starting with // that looks like an entry
        line = "// :e:hw:561   AC01         -"
        entry = self.parser._parse_line(line, 1)
        assert entry is None
    
    def test_get_node_type_from_lid(self):
        """Test node type detection from LID"""
        assert self.parser.get_node_type_from_lid("AL01") == "LIS"
        assert self.parser.get_node_type_from_lid("AD01") == "DIA"
        assert self.parser.get_node_type_from_lid("AP01_main") == "PCS"
        assert self.parser.get_node_type_from_lid("A1O1") == "OPS"
        assert self.parser.get_node_type_from_lid("INFO") == "HISTORY"
        assert self.parser.get_node_type_from_lid("NW01") == "NETWATCH"
        assert self.parser.get_node_type_from_lid("UNKNOWN") == "UNKNOWN"
    
    def test_get_token_id_from_hardware_address(self):
        """Test token ID generation from hardware address"""
        assert self.parser.get_token_id_from_hardware_address("501") == "501"
        assert self.parser.get_token_id_from_hardware_address("5A") == "05a"
        assert self.parser.get_token_id_from_hardware_address("5AA") == "5aa"
    
    def test_extract_bus_unit(self):
        """Test bus unit extraction from filename"""
        assert self.parser._extract_bus_unit("AB01_10.1_sys") == "AB01"
        assert self.parser._extract_bus_unit("CD02_sys") == "CD02"
        assert self.parser._extract_bus_unit("unknown_file") == "UNKNOWN"
    
    def test_parse_full_file(self):
        """Test parsing a complete sys file"""
        content = """// DIA in PC node:
:e:hw:5aa   AD01         -
:e:hw:58a   AD02         -

// LIS in PC node:
:e:hw:501   AL01          pxe:sys-csg2    // For single LIS. 
:e:hw:581   AL10          pxe:sys-csg3    // For single LIS. 
:e:hw:521   AL16          pxe:sys-lite   // For single LIS. 

// Redundant PCS in ACN Compact node:
:e:hw:161   AP01_main 	 pxe:sys-csg2	  // Main PCS.
:e:hw:361   AP01_reserve pxe:sys-csg2	  // Reserve PCS.
"""
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='_sys', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            info = self.parser.parse_file(temp_path)
            
            assert info.token_count == 7
            assert len(info.parse_errors) == 0
            
            # Check specific entries
            dia_entries = info.get_entries_by_type("AD")
            assert len(dia_entries) == 2
            
            lis_entries = info.get_entries_by_type("AL")
            assert len(lis_entries) == 3
            
            pcs_entries = info.get_entries_by_type("AP")
            assert len(pcs_entries) == 2
            
            # Check that all config types are parsed
            configs = [e.config for e in info.entries]
            assert "-" in configs
            assert "pxe:sys-csg2" in configs
            assert "pxe:sys-csg3" in configs
            assert "pxe:sys-lite" in configs
            
        finally:
            os.unlink(temp_path)
    
    def test_entries_to_tokens(self):
        """Test conversion of entries to token format"""
        entries = [
            SysEntry("501", "AL01", "pxe:sys-csg2", "For LIS", 1),
            SysEntry("5aa", "AD01", "-", "", 2),
        ]
        
        tokens = self.parser.entries_to_tokens(entries)
        
        assert len(tokens) == 2
        
        assert tokens[0]['token_id'] == "501"
        assert tokens[0]['lid'] == "AL01"
        assert tokens[0]['token_type'] == "LIS"
        
        assert tokens[1]['token_id'] == "5aa"
        assert tokens[1]['lid'] == "AD01"
        assert tokens[1]['token_type'] == "DIA"


class TestSysFileParserModule:
    """Test module-level functions"""
    
    def test_get_tokens_from_sys_file(self):
        """Test the get_tokens_from_sys_file helper function"""
        content = """:e:hw:501   AL01          pxe:sys-csg2
:e:hw:5aa   AD01         -
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_sys', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            tokens = get_tokens_from_sys_file(temp_path)
            assert len(tokens) == 2
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
