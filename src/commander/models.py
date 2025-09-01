from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class NodeToken:
    token_id: str
    token_type: str  # FBC/RPC/LOG/LIS - matches file extension exactly
    name: str = "default"
    ip_address: str = "0.0.0.0"
    port: int = 23
    log_path: str = ""
    protocol: str = "telnet"
    
    def __init__(self, token_id: str, token_type: str, name: str = "default",
                 ip_address: str = "0.0.0.0", port: int = 23, **kwargs):
        self.token_id = token_id
        self.token_type = token_type
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.log_path = kwargs.get('log_path', "")
        self.protocol = kwargs.get('protocol', "telnet")


@dataclass
class Node:
    name: str
    ip_address: str
    status: str = "offline"
    tokens: Dict[str, List[NodeToken]] = field(default_factory=dict)

    def add_token(self, token: NodeToken):
        if token.token_id not in self.tokens:
            self.tokens[token.token_id] = []
        # Check if a token of the same type already exists
        for i, existing_token in enumerate(self.tokens[token.token_id]):
            if existing_token.token_type == token.token_type:
                # Replace the existing token of the same type
                self.tokens[token.token_id][i] = token
                return
        # Add the new token
        self.tokens[token.token_id].append(token)

