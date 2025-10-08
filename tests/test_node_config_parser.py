import unittest
import os
import json
from unittest.mock import patch, mock_open
from src.node_config_parser import SysFileParser

class TestSysFileParser(unittest.TestCase):

    def setUp(self):
        # Create a dummy config file for testing
        self.config_path = "config/test_sys_parsing_rules.json"
        self.dummy_config = {
            "regex_patterns": {
                "ip_address": "set XD_IP_ADDR=([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3})",
                "ap_node": "^:e:hw:(?P<lid>[0-9a-fA-F]{2,4})\\s+(?P<node_name>AP\\d{2})(?:m|r|t)?\\d*\\s+.*",
                "al_node": "^:e:hw:(?P<lid>[0-9a-fA-F]{2,4})\\s+(?P<node_name>AL\\d{2})\\s+(?:pxe:sys-csg2)?.*",
                "token_entry": "^:e:hw:(?P<lid>[0-9a-fA-F]{2,4})\\s+(?P<node_prefix>(?:AP|AL)\\d{2})(?P<suffix>(?:_m|_r|_t)?\\d*)?\\s+.*"
            },
            "node_types": {
                "ap_based": {
                    "default_types": ["AP"],
                    "token_suffixes": ["_m2", "_m3", "_r2", "_r3"]
                },
                "al_based": {
                    "default_types": ["AL", "LIS"]
                }
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.dummy_config, f)

        self.parser = SysFileParser(config_path=self.config_path)
        # print(f"AP Node Regex in Test: {self.parser.ap_node_regex.pattern}")
        # print(f"AL Node Regex in Test: {self.parser.al_node_regex.pattern}")
        # print(f"Token Entry Regex in Test: {self.parser.token_entry_regex.pattern}")

        self.ap_sys_content = [
            "some other line",
            ":e:hw:1234 AP01m some_data",
            "set XD_IP_ADDR=192.168.1.100",
            ":e:hw:5678 AP01_m2 more_data",
            ":e:hw:90ab AP01_r2 even_more_data",
            ":e:hw:cdef AP01_m3 final_data"
        ]

        self.al_sys_content = [
            "another line",
            ":e:hw:abcd AL01 pxe:sys-csg2",
            "set XD_IP_ADDR=10.0.0.50",
            ":e:hw:1122 AL01_t1 data_for_al"
        ]

        self.multi_sys_content = [
            "some header",
            ":e:hw:1111 AP02m data",
            "set XD_IP_ADDR=172.16.0.1",
            ":e:hw:2222 AP02_m2 data",
            ":e:hw:3333 AL03 pxe:sys-csg2",
            "set XD_IP_ADDR=10.10.10.10"
        ]

    def tearDown(self):
        # Clean up dummy files
        os.remove(self.config_path)
        if os.path.exists("config"):
            try:
                os.rmdir("config")
            except OSError:
                # Directory might not be empty if other tests created files
                pass

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_load_config_success(self, mock_json_load, mock_file_open):
        mock_json_load.return_value = self.dummy_config
        parser = SysFileParser(config_path="dummy_path.json")
        mock_file_open.assert_called_once_with("dummy_path.json", 'r')
        mock_json_load.assert_called_once_with(mock_file_open())
        self.assertEqual(parser.config, self.dummy_config)

    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_file_not_found(self, mock_file_open):
        mock_file_open.side_effect = FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            SysFileParser(config_path="non_existent.json")

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_load_config_json_decode_error(self, mock_json_load, mock_file_open):
        mock_json_load.side_effect = json.JSONDecodeError("Expecting value", "doc", 1)
        with self.assertRaises(ValueError) as cm:
            SysFileParser(config_path="invalid.json")
        self.assertIn("Error decoding JSON", str(cm.exception))

    def test_parse_single_sys_file_content_ap_node(self):
        parsed_node = self.parser._parse_single_sys_file_content(self.ap_sys_content, "test_ap_node.sys")
        self.assertIsNotNone(parsed_node)
        self.assertEqual(parsed_node["name"], "AP01")
        self.assertEqual(parsed_node["ip_address"], "192.168.1.100")
        self.assertIn("AP", parsed_node["types"])
        self.assertEqual(len(parsed_node["tokens"]), 3)
        self.assertIn({"token_id": "5678", "token_type": "FBC", "port": 23, "protocol": "telnet"}, parsed_node["tokens"])
        self.assertIn({"token_id": "90ab", "token_type": "FBC", "port": 23, "protocol": "telnet"}, parsed_node["tokens"])
        self.assertIn({"token_id": "cdef", "token_type": "FBC", "port": 23, "protocol": "telnet"}, parsed_node["tokens"])

    def test_parse_single_sys_file_content_al_node(self):
        parsed_node = self.parser._parse_single_sys_file_content(self.al_sys_content, "test_al_node.sys")
        self.assertIsNotNone(parsed_node)
        self.assertEqual(parsed_node["name"], "AL01")
        self.assertEqual(parsed_node["ip_address"], "10.0.0.50")
        self.assertIn("AL", parsed_node["types"])
        self.assertIn("LIS", parsed_node["types"])
        self.assertEqual(len(parsed_node["tokens"]), 1)
        self.assertIn({"token_id": "abcd", "token_type": "LIS", "port": 23, "protocol": "telnet"}, parsed_node["tokens"])

    @patch('builtins.open', new_callable=mock_open)
    def test_parse_sys_files(self, mock_file_open):
        mock_file_open.side_effect = [
            mock_open(read_data="\n".join(self.ap_sys_content)).return_value,
            mock_open(read_data="\n".join(self.al_sys_content)).return_value
        ]
        parsed_nodes = self.parser.parse_sys_files(["dummy_ap.sys", "dummy_al.sys"])
        self.assertEqual(len(parsed_nodes), 2)
        
        # Check for AP01 node
        ap_node_found = False
        for node in parsed_nodes:
            if node["name"] == "AP01":
                self.assertEqual(node["ip_address"], "192.168.1.100")
                self.assertIn("AP", node["types"])
                ap_node_found = True
                break
        self.assertTrue(ap_node_found, "AP01 node not found in parsed_nodes")

        # Check for AL01 node
        al_node_found = False
        for node in parsed_nodes:
            if node["name"] == "AL01":
                self.assertEqual(node["ip_address"], "10.0.0.50")
                self.assertIn("AL", node["types"])
                self.assertIn("LIS", node["types"])
                al_node_found = True
                break
        self.assertTrue(al_node_found, "AL01 node not found in parsed_nodes")

    def test_parse_single_sys_file_content_no_ip_address(self):
        content = ["some content", ":e:hw:1234 AP01m some_data"]
        parsed_node = self.parser._parse_single_sys_file_content(content, "no_ip.sys")
        self.assertIsNone(parsed_node)

    def test_parse_single_sys_file_content_no_node_name(self):
        content = ["some content", "set XD_IP_ADDR=192.168.1.1"]
        parsed_node = self.parser._parse_single_sys_file_content(content, "no_node.sys")
        self.assertIsNone(parsed_node)

    def test_parse_single_sys_file_content_empty_file(self):
        content = []
        parsed_node = self.parser._parse_single_sys_file_content(content, "empty.sys")
        self.assertIsNone(parsed_node)

    def test_parse_single_sys_file_content_ap_node_token_suffixes(self):
        # Ensure only specified suffixes are collected for AP nodes
        ap_node_content = [
            "set XD_IP_ADDR=1.1.1.1",
            ":e:hw:1234 AP01m data",
            ":e:hw:5678 AP01_m2 data",
            ":e:hw:90ab AP01_m1 data" # This should NOT be collected
        ]
        parsed_node = self.parser._parse_single_sys_file_content(ap_node_content, "ap_node_suffixes.sys")
        self.assertIsNotNone(parsed_node)
        self.assertEqual(len(parsed_node["tokens"]), 1)
        self.assertIn({"token_id": "5678", "token_type": "FBC", "port": 23, "protocol": "telnet"}, parsed_node["tokens"])
        self.assertNotIn({"token_id": "90ab", "token_type": "FBC", "port": 23, "protocol": "telnet"}, parsed_node["tokens"])

    def test_parse_single_sys_file_content_al_node_single_token_only(self):
        # Ensure only the main AL node's LID is collected as a token
        al_node_content = [
            "set XD_IP_ADDR=2.2.2.2",
            ":e:hw:abcd AL02 pxe:sys-csg2",
            ":e:hw:ef01 AL02_t1 data" # This should NOT be collected as a token
        ]
        parsed_node = self.parser._parse_single_sys_file_content(al_node_content, "al_node_single_token.sys")
        self.assertIsNotNone(parsed_node)
        self.assertEqual(len(parsed_node["tokens"]), 1)
        self.assertIn({"token_id": "abcd", "token_type": "LIS", "port": 23, "protocol": "telnet"}, parsed_node["tokens"])
        self.assertNotIn({"token_id": "ef01", "token_type": "LIS", "port": 23, "protocol": "telnet"}, parsed_node["tokens"])

if __name__ == '__main__':
    unittest.main()