package models

type NodeToken struct {
	TokenID   string `json:"token_id"`
	TokenType string `json:"token_type"`
	Port      int    `json:"port"`
	Protocol  string `json:"protocol"`
}

type Node struct {
	Name      string      `json:"name"`
	IPAddress string      `json:"ip_address"`
	Status    string      `json:"status"`
	Tokens    []NodeToken `json:"tokens"`
}
