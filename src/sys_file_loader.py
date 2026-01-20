import re
import json
import os
from typing import List, Dict, Any, Optional

class SysFileParser:
    def __init__(self, config_path: str = "config/sys_parsing_rules.json"):
        self.config = self._load_config(config_path)
        self.ip_address_regex = re.compile(self.config["regex_patterns"]["ip_address"])
        self.token_regex = re.compile(self.config["regex_patterns"]["token_id"])
        self.node_name_regex = re.compile(self.config["regex_patterns"]["node_name"])

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Loads parsing rules and regex patterns from a JSON configuration file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found at {config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON from configuration file at {config_path}: {e}")

    def parse_sys_files(self, file_paths: List[str]) -> List[Dict]:
        """
        Parses multiple sys files to extract node configuration.
        """
        parsed_nodes = []
        for file_path in file_paths:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                node_name = self._extract_node_name(content)
                ip_address = self._extract_ip_address(content)
                tokens = self._extract_tokens(content)

                if node_name and ip_address and tokens:
                    parsed_nodes.append({
                        "name": node_name,
                        "ip": ip_address,
                        "tokens": tokens,
                        "types": ["FBC", "RPC"] # Default types for now, can be refined
                    })
            except Exception as e:
                print(f"Error parsing file {file_path}: {e}")
        return parsed_nodes

    def _extract_node_name(self, content: str) -> Optional[str]:
        match = self.node_name_regex.search(content)
        return match.group("node_name") if match else None

    def _extract_ip_address(self, content: str) -> Optional[str]:
        match = self.ip_address_regex.search(content)
        return match.group("ip_address") if match else None

    def _extract_tokens(self, content: str) -> List[str]:
        return self.token_regex.findall(content)

class SysFileLoader:
    def __init__(self, config_path: str = "config/sys_parsing_rules.json"):
        self.config = self._load_config(config_path)
        self.token_detection_line_regex = re.compile(self.config["regex_patterns"]["token_detection_line"])
        self.sys_file_parser = SysFileParser(config_path)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Loads parsing rules and regex patterns from a JSON configuration file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found at {config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON from configuration file at {config_path}: {e}")

    def load_sys_files_from_directory(self, directory_path: str) -> Dict[str, str]:
        """
        Scans a directory for .sys files, reads their content, and returns a dictionary
        where keys are filenames and values are file contents.
        """
        sys_file_contents = {}
        if not os.path.isdir(directory_path):
            raise FileNotFoundError(f"Directory not found at {directory_path}")

        for filename in os.listdir(directory_path):
            if filename.endswith(".sys"):
                file_path = os.path.join(directory_path, filename)
                try:
                    with open(file_path, 'r') as f:
                        sys_file_contents[filename] = f.read()
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
        return sys_file_contents

    def detect_tokens_from_content(self, file_content: str) -> Dict[str, List[str]]:
        """
        Detects node IDs and their associated tokens from the content of a sys file.
        Returns a dictionary where keys are node IDs (e.g., 'AP01m') and values are lists of token IDs (e.g., ['181', '182']).
        """
        detected_tokens = {}
        for line in file_content.splitlines():
            match = self.token_detection_line_regex.search(line)
            if match:
                node_id = match.group("node_id")
                tokens_str = match.group("tokens")
                token_list = [t.strip() for t in tokens_str.split(',') if t.strip()]
                
                if node_id not in detected_tokens:
                    detected_tokens[node_id] = []
                detected_tokens[node_id].extend(token_list)
        return detected_tokens

    def parse_token_sys_files(self, token_ids: List[str], directory_path: str) -> List[Dict]:
        """
        Parses individual [tokenid].sys files using the SysFileParser.
        """
        token_file_paths = []
        for token_id in token_ids:
            file_path = os.path.join(directory_path, f"{token_id}.sys")
            if os.path.exists(file_path):
                token_file_paths.append(file_path)
            else:
                print(f"Warning: Token sys file not found for token ID: {token_id} at {file_path}")
        
        return self.sys_file_parser.parse_sys_files(token_file_paths)

    def _get_token_id_for_node(self, node_id: str, tokens: List[str]) -> Optional[str]:
        """
        Determines the correct token ID to use based on node type (AL vs. AP).
        For AL nodes, it uses the single token. For AP nodes, it uses the first token from the list.
        """
        if not tokens:
            return None

        if node_id.startswith("AL"):
            # AL-based nodes use a single token.
            # Assuming 'tokens' list will contain only one element for AL nodes.
            return tokens if tokens else None
        elif node_id.startswith("AP"):
            # AP-based nodes use the first token from the list.
            return tokens if tokens else None
        return None

    def load_sys_file_and_extract_ip(self, node_id: str, tokens: List[str], directory_path: str) -> Optional[str]:
        """
        Loads a [tokenid].sys file, extracts the IP address from the 'set XD_IP_ADDR=' field.
        The token_id is determined based on the node_id (AL vs. AP).
        """
        selected_token_id = self._get_token_id_for_node(node_id, tokens)
        if not selected_token_id:
            print(f"Warning: No valid token ID found for node: {node_id} with tokens: {tokens}")
            return None

        file_path = os.path.join(directory_path, f"{selected_token_id}.sys")
        if not os.path.exists(file_path):
            print(f"Warning: Token sys file not found for token ID: {selected_token_id} at {file_path}")
            return None

        try:
            with open(file_path, 'r') as f:
                file_content = f.read()
            
            ip_address_regex = re.compile(r"set XD_IP_ADDR=(?P<ip_address>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
            match = ip_address_regex.search(file_content)
            if match:
                return match.group("ip_address")
            else:
                print(f"Warning: IP address not found in {file_path}")
                return None
        except Exception as e:
            print(f"Error reading or parsing file {file_path}: {e}")
            return None
