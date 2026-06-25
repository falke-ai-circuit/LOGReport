package nodesconfig

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

const sampleNodesJSON = `[
    {
        "name": "AP01m",
        "ip_address": "192.168.1.101",
        "tokens": [
            {"token_id": "162", "token_type": "FBC", "port": 2077, "protocol": "telnet"},
            {"token_id": "163", "token_type": "FBC", "port": 5901, "protocol": "telnet"},
            {"token_id": "363", "token_type": "RPC", "port": 2077, "protocol": "telnet"},
            {"token_id": "361", "token_type": "LOG", "port": 2077, "protocol": "telnet"}
        ]
    },
    {
        "name": "AL01",
        "ip_address": "192.168.1.200",
        "tokens": [
            {"token_id": "200", "token_type": "FBC", "port": 2077, "protocol": "telnet"}
        ]
    }
]`

func TestLoadFromBytes(t *testing.T) {
	configs, err := LoadFromBytes([]byte(sampleNodesJSON))
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}
	if len(configs) != 2 {
		t.Fatalf("expected 2 configs, got %d", len(configs))
	}
	if configs[0].Name != "AP01m" {
		t.Errorf("expected first config name AP01m, got %s", configs[0].Name)
	}
	if configs[0].IPAddress != "192.168.1.101" {
		t.Errorf("expected IP 192.168.1.101, got %s", configs[0].IPAddress)
	}
	if len(configs[0].Tokens) != 4 {
		t.Fatalf("expected 4 tokens for AP01m, got %d", len(configs[0].Tokens))
	}
	if configs[0].Tokens[0].TokenID != "162" {
		t.Errorf("expected first token 162, got %s", configs[0].Tokens[0].TokenID)
	}
	if configs[0].Tokens[0].TokenType != types.TokenFBC {
		t.Errorf("expected token type FBC, got %s", configs[0].Tokens[0].TokenType)
	}
	// Nil-slice safety: empty tokens should yield make([]Token, 0)
	emptyJSON := `[{"name": "X", "ip_address": "1.2.3.4", "tokens": []}]`
	empty, _ := LoadFromBytes([]byte(emptyJSON))
	if empty[0].Tokens == nil {
		t.Error("expected non-nil token slice for empty tokens")
	}
}

func TestLoadFromBytesInvalid(t *testing.T) {
	_, err := LoadFromBytes([]byte(`{invalid json`))
	if err == nil {
		t.Fatal("expected error for invalid JSON")
	}
}

func TestLoadFromFile(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "nodes.json")
	if err := os.WriteFile(path, []byte(sampleNodesJSON), 0644); err != nil {
		t.Fatalf("write file: %v", err)
	}

	configs, err := LoadFromFile(path)
	if err != nil {
		t.Fatalf("LoadFromFile failed: %v", err)
	}
	if len(configs) != 2 {
		t.Fatalf("expected 2 configs, got %d", len(configs))
	}
}

func TestSaveToFile(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "out.json")
	configs := []types.NodeConfig{
		{
			Name:      "TestNode",
			IPAddress: "10.0.0.1",
			Tokens:    []types.Token{{TokenID: "100", TokenType: types.TokenFBC, Port: 2077, Protocol: "telnet"}},
		},
	}
	if err := SaveToFile(path, configs); err != nil {
		t.Fatalf("SaveToFile failed: %v", err)
	}
	// Read back and verify
	loaded, err := LoadFromFile(path)
	if err != nil {
		t.Fatalf("LoadFromFile failed: %v", err)
	}
	if loaded[0].Name != "TestNode" {
		t.Errorf("expected TestNode, got %s", loaded[0].Name)
	}
	if len(loaded[0].Tokens) != 1 {
		t.Fatalf("expected 1 token, got %d", len(loaded[0].Tokens))
	}
	if loaded[0].Tokens[0].TokenID != "100" {
		t.Errorf("expected token 100, got %s", loaded[0].Tokens[0].TokenID)
	}
}

func TestBuildTree(t *testing.T) {
	configs, _ := LoadFromBytes([]byte(sampleNodesJSON))
	tree := BuildTree(configs)

	if tree == nil {
		t.Fatal("expected non-nil tree")
	}
	if tree.Type != "root" {
		t.Errorf("expected root type, got %s", tree.Type)
	}
	if len(tree.Children) != 2 {
		t.Fatalf("expected 2 node children, got %d", len(tree.Children))
	}

	// First node: AP01m
	ap01 := tree.Children[0]
	if ap01.Name != "AP01m" {
		t.Errorf("expected AP01m, got %s", ap01.Name)
	}
	if ap01.Type != "node" {
		t.Errorf("expected node type, got %s", ap01.Type)
	}
	if ap01.IP != "192.168.1.101" {
		t.Errorf("expected IP 192.168.1.101, got %s", ap01.IP)
	}
	// AP01m has FBC, RPC, LOG groups
	if len(ap01.Children) != 3 {
		t.Fatalf("expected 3 group children for AP01m, got %d", len(ap01.Children))
	}
	// First group: FBC
	fbcGroup := ap01.Children[0]
	if fbcGroup.Name != "FBC" {
		t.Errorf("expected FBC group, got %s", fbcGroup.Name)
	}
	if fbcGroup.Type != "group" {
		t.Errorf("expected group type, got %s", fbcGroup.Type)
	}
	// FBC group has 2 tokens (162, 163)
	if len(fbcGroup.Children) != 2 {
		t.Fatalf("expected 2 FBC tokens, got %d", len(fbcGroup.Children))
	}
	// First token
	tok162 := fbcGroup.Children[0]
	if tok162.Name != "162" {
		t.Errorf("expected token 162, got %s", tok162.Name)
	}
	if tok162.Type != "token" {
		t.Errorf("expected token type, got %s", tok162.Type)
	}
	if tok162.TokenID != "162" {
		t.Errorf("expected token_id 162, got %s", tok162.TokenID)
	}
	if tok162.Port != 2077 {
		t.Errorf("expected port 2077, got %d", tok162.Port)
	}
	if tok162.Protocol != "telnet" {
		t.Errorf("expected protocol telnet, got %s", tok162.Protocol)
	}

	// RPC group should be second
	rpcGroup := ap01.Children[1]
	if rpcGroup.Name != "RPC" {
		t.Errorf("expected RPC group second, got %s", rpcGroup.Name)
	}
	if len(rpcGroup.Children) != 1 {
		t.Fatalf("expected 1 RPC token, got %d", len(rpcGroup.Children))
	}

	// LOG group should be third
	logGroup := ap01.Children[2]
	if logGroup.Name != "LOG" {
		t.Errorf("expected LOG group third, got %s", logGroup.Name)
	}
}

func TestBuildTreeEmpty(t *testing.T) {
	tree := BuildTree(nil)
	if tree == nil {
		t.Fatal("expected non-nil tree for nil input")
	}
	if len(tree.Children) != 0 {
		t.Errorf("expected 0 children for nil input, got %d", len(tree.Children))
	}
}