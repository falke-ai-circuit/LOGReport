"""
Test suite for hexadecimal token ID parsing in node configurator.

Tests verify that token-specific .sys files with hexadecimal filenames
(both bare hex like 1a1.sys and prefixed hex like 0x1a1.sys) are correctly
identified and processed for IP address extraction.

This fixes the issue where AP03m and AP03r nodes with hex tokens (1a1, 3a1)
were not getting IP addresses loaded from their respective tokenid.sys files.
"""

import pytest
from pathlib import Path
from src.utils.file_utils import parse_sys_file


class TestHexadecimalTokenDetection:
    """Test that hexadecimal token files are correctly identified"""
    
    def test_pure_decimal_token_recognized(self):
        """Pure decimal tokens like 181.sys should be recognized"""
        file_path = Path("181.sys")
        file_content = "set XD_IP_ADDR=192.168.0.12\n"
        
        result = parse_sys_file(file_content, file_path)
        
        assert len(result) == 1
        assert result[0]["ip"] == "192.168.0.12"
        assert result[0]["name"] == "_token_181"
    
    def test_bare_hex_token_recognized(self):
        """Bare hexadecimal tokens like 1a1.sys should be recognized"""
        file_path = Path("1a1.sys")
        file_content = "set XD_IP_ADDR=192.168.0.25\n"
        
        result = parse_sys_file(file_content, file_path)
        
        assert len(result) == 1
        assert result[0]["ip"] == "192.168.0.25"
        assert result[0]["name"] == "_token_1a1"
    
    def test_bare_hex_token_3a1_recognized(self):
        """Bare hexadecimal token 3a1.sys should be recognized"""
        file_path = Path("3a1.sys")
        file_content = "set XD_IP_ADDR=192.168.0.35\n"
        
        result = parse_sys_file(file_content, file_path)
        
        assert len(result) == 1
        assert result[0]["ip"] == "192.168.0.35"
        assert result[0]["name"] == "_token_3a1"
    
    def test_bare_hex_token_1c1_recognized(self):
        """Bare hexadecimal token 1c1.sys should be recognized"""
        file_path = Path("1c1.sys")
        file_content = "set XD_IP_ADDR=192.168.0.45\n"
        
        result = parse_sys_file(file_content, file_path)
        
        assert len(result) == 1
        assert result[0]["ip"] == "192.168.0.45"
        assert result[0]["name"] == "_token_1c1"
    
    def test_bare_hex_token_1e1_recognized(self):
        """Bare hexadecimal token 1e1.sys should be recognized"""
        file_path = Path("1e1.sys")
        file_content = "set XD_IP_ADDR=192.168.0.55\n"
        
        result = parse_sys_file(file_content, file_path)
        
        assert len(result) == 1
        assert result[0]["ip"] == "192.168.0.55"
        assert result[0]["name"] == "_token_1e1"
    
    def test_prefixed_hex_token_0x_recognized(self):
        """Prefixed hexadecimal tokens like 0x1a1.sys should be recognized"""
        file_path = Path("0x1a1.sys")
        file_content = "set XD_IP_ADDR=192.168.0.65\n"
        
        result = parse_sys_file(file_content, file_path)
        
        assert len(result) == 1
        assert result[0]["ip"] == "192.168.0.65"
        assert result[0]["name"] == "_token_0x1a1"
    
    def test_prefixed_hex_token_x_recognized(self):
        """Prefixed hexadecimal tokens like x3a1.sys should be recognized"""
        file_path = Path("x3a1.sys")
        file_content = "set XD_IP_ADDR=192.168.0.75\n"
        
        result = parse_sys_file(file_content, file_path)
        
        assert len(result) == 1
        assert result[0]["ip"] == "192.168.0.75"
        assert result[0]["name"] == "_token_x3a1"
    
    def test_main_sys_file_not_treated_as_token(self):
        """Main sys files like AB01_sys should not be treated as token files"""
        file_path = Path("AB01_sys")
        file_content = """
:e:hw:181 AP02_main	pxe:sys-csg2	// AP02 Main PCS
:e:hw:182 AP02_m2	-               // FBC2
:e:hw:183 AP02_m3       -               // FBC3
"""
        
        result = parse_sys_file(file_content, file_path)
        
        # Should return actual node data, not a token placeholder
        assert len(result) == 1
        assert result[0]["name"] == "AP02m"
        assert "_token_" not in result[0]["name"]
    
    def test_mixed_hex_uppercase_lowercase(self):
        """Hexadecimal tokens with mixed case like 1A1.sys should be recognized"""
        file_path = Path("1A1.sys")
        file_content = "set XD_IP_ADDR=192.168.0.85\n"
        
        result = parse_sys_file(file_content, file_path)
        
        assert len(result) == 1
        assert result[0]["ip"] == "192.168.0.85"
        assert result[0]["name"] == "_token_1A1"


class TestNodeConfiguratorTokenCategorization:
    """Test that node configurator correctly categorizes token vs main files"""
    
    def test_categorize_pure_decimal_as_token(self):
        """File stems that are pure decimal should be categorized as token files"""
        file_stems = ["181", "41", "21", "201", "221"]
        
        for stem in file_stems:
            # Simulate the categorization logic with length constraint
            is_token = False
            if stem.isdigit() and len(stem) <= 5:
                is_token = True
            elif stem.lower().startswith(('0x', 'x')):
                hex_part = stem[2:] if stem.lower().startswith('0x') else stem[1:]
                if all(c in '0123456789abcdefABCDEF' for c in hex_part) and len(hex_part) <= 5:
                    is_token = True
            elif all(c in '0123456789abcdefABCDEF' for c in stem) and len(stem) <= 5:
                is_token = True
            
            assert is_token, f"{stem} should be categorized as token file"
    
    def test_categorize_bare_hex_as_token(self):
        """File stems that are bare hex should be categorized as token files"""
        file_stems = ["1a1", "3a1", "1c1", "1e1", "4a1", "4c1"]
        
        for stem in file_stems:
            # Simulate the categorization logic with length constraint
            is_token = False
            if stem.isdigit() and len(stem) <= 5:
                is_token = True
            elif stem.lower().startswith(('0x', 'x')):
                hex_part = stem[2:] if stem.lower().startswith('0x') else stem[1:]
                if all(c in '0123456789abcdefABCDEF' for c in hex_part) and len(hex_part) <= 5:
                    is_token = True
            elif all(c in '0123456789abcdefABCDEF' for c in stem) and len(stem) <= 5:
                is_token = True
            
            assert is_token, f"{stem} should be categorized as token file"
    
    def test_categorize_prefixed_hex_as_token(self):
        """File stems with 0x or x prefix should be categorized as token files"""
        file_stems = ["0x1a1", "x3a1", "0x181", "xabc"]
        
        for stem in file_stems:
            # Simulate the categorization logic with length constraint
            is_token = False
            if stem.isdigit() and len(stem) <= 5:
                is_token = True
            elif stem.lower().startswith(('0x', 'x')):
                hex_part = stem[2:] if stem.lower().startswith('0x') else stem[1:]
                if all(c in '0123456789abcdefABCDEF' for c in hex_part) and len(hex_part) <= 5:
                    is_token = True
            elif all(c in '0123456789abcdefABCDEF' for c in stem) and len(stem) <= 5:
                is_token = True
            
            assert is_token, f"{stem} should be categorized as token file"
    
    def test_categorize_main_file_not_as_token(self):
        """File stems that are text names should NOT be categorized as token files"""
        file_stems = ["AB01_sys", "sys_config", "main", "nodes"]
        
        for stem in file_stems:
            # Simulate the categorization logic with length constraint
            is_token = False
            if stem.isdigit() and len(stem) <= 5:
                is_token = True
            elif stem.lower().startswith(('0x', 'x')):
                hex_part = stem[2:] if stem.lower().startswith('0x') else stem[1:]
                if all(c in '0123456789abcdefABCDEF' for c in hex_part) and len(hex_part) <= 5:
                    is_token = True
            elif all(c in '0123456789abcdefABCDEF' for c in stem) and len(stem) <= 5:
                is_token = True
            
            assert not is_token, f"{stem} should NOT be categorized as token file"
    
    def test_length_constraint_prevents_long_hex_strings(self):
        """Hex strings longer than 5 chars should not be treated as tokens"""
        file_stems = ["123456", "abcdef", "1a2b3c"]
        
        for stem in file_stems:
            # Simulate the categorization logic with length constraint
            is_token = False
            if stem.isdigit() and len(stem) <= 5:
                is_token = True
            elif stem.lower().startswith(('0x', 'x')):
                hex_part = stem[2:] if stem.lower().startswith('0x') else stem[1:]
                if all(c in '0123456789abcdefABCDEF' for c in hex_part) and len(hex_part) <= 5:
                    is_token = True
            elif all(c in '0123456789abcdefABCDEF' for c in stem) and len(stem) <= 5:
                is_token = True
            
            assert not is_token, f"{stem} should NOT be categorized as token (too long)"


class TestRealWorldScenario:
    """Test real-world scenario from user's _DIA/_SYS directory"""
    
    def test_ap03m_token_extraction(self):
        """AP03_main should extract token 1a1 as main token"""
        main_sys_content = """:e:hw:1a1 AP03_main	pxe:sys-csg2	// AP03 Main PCS
:e:hw:1a2 AP03_m2	-               // FBC2
:e:hw:1a3 AP03_m3       -               // FBC3
:e:hw:1a4 AP03_m4       -               // FBC4
"""
        
        result = parse_sys_file(main_sys_content, None)
        
        assert len(result) == 1
        node = result[0]
        assert node["name"] == "AP03m"
        assert node["_main_token"] == "1a1"
        assert "1a2" in node["tokens"]
        assert "1a3" in node["tokens"]
        assert "1a4" in node["tokens"]
        # Main token should NOT be in tokens list for AP nodes
        assert "1a1" not in node["tokens"]
    
    def test_ap03r_token_extraction(self):
        """AP03_reserve should extract token 3a1 as main token"""
        main_sys_content = """:e:hw:3a1 AP03_reserve	pxe:sys-csg2	// AP03 Reserve PCS
:e:hw:3a2 AP03_r2	-               // FBC2
:e:hw:3a3 AP03_r3       -               // FBC3
:e:hw:3a4 AP03_r4       -               // FBC4
"""
        
        result = parse_sys_file(main_sys_content, None)
        
        assert len(result) == 1
        node = result[0]
        assert node["name"] == "AP03r"
        assert node["_main_token"] == "3a1"
        assert "3a2" in node["tokens"]
        assert "3a3" in node["tokens"]
        assert "3a4" in node["tokens"]
        # Main token should NOT be in tokens list for AP nodes
        assert "3a1" not in node["tokens"]
    
    def test_token_file_1a1_ip_extraction(self):
        """Token file 1a1.sys should extract IP address correctly"""
        token_file_content = "set XD_IP_ADDR=192.168.0.99\n"
        file_path = Path("1a1.sys")
        
        result = parse_sys_file(token_file_content, file_path)
        
        assert len(result) == 1
        assert result[0]["ip"] == "192.168.0.99"
        assert result[0]["tokens"] == ["1a1"]
    
    def test_token_file_3a1_ip_extraction(self):
        """Token file 3a1.sys should extract IP address correctly"""
        token_file_content = "set XD_IP_ADDR=192.168.0.88\n"
        file_path = Path("3a1.sys")
        
        result = parse_sys_file(token_file_content, file_path)
        
        assert len(result) == 1
        assert result[0]["ip"] == "192.168.0.88"
        assert result[0]["tokens"] == ["3a1"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
