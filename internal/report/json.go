package report

import (
	"encoding/json"
	"fmt"
	"os"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// jsonReport is the structured output for JSON reports.
type jsonReport struct {
	Title        string          `json:"title"`
	Node         jsonNode        `json:"node"`
	FBCModules   []jsonFBCModule `json:"fbc_modules"`
	RPCCounters  []jsonRPCCounter `json:"rpc_counters"`
	IOPoints     []types.IOPoint `json:"io_points"`
	GeneratedAt  string          `json:"generated_at"`
	TotalFBC     int             `json:"total_fbc_points"`
	TotalRPC     int             `json:"total_rpc_points"`
	TotalIOPoints int            `json:"total_io_points"`
}

type jsonNode struct {
	Name    string `json:"name"`
	Address string `json:"address"`
	Type    string `json:"type"`
	Status  string `json:"status"`
	Port    int    `json:"port"`
}

type jsonFBCModule struct {
	ModulePosition int              `json:"module_position"`
	Channels       []jsonFBCChannel `json:"channels"`
}

type jsonFBCChannel struct {
	ChannelPosition int    `json:"channel_position"`
	ChannelType     string `json:"channel_type"`
}

type jsonRPCCounter struct {
	ModulePosition int    `json:"module_position"`
	CounterName    string `json:"counter_name"`
	CounterValue   int    `json:"counter_value"`
}

// generateJSON creates a .json report file with full structured data.
// Returns the file path.
func generateJSON(node *types.Node, ioPoints []types.IOPoint, reportID string) (string, error) {
	filePath := outputPath(reportID, ".json")

	// Build FBC module summary
	fbcMap := make(map[int]*jsonFBCModule)
	var rpcCounters []jsonRPCCounter
	fbcCount := 0
	rpcCount := 0

	for _, p := range ioPoints {
		switch p.ModuleType {
		case types.ModuleFBC:
			fbcCount++
			mod, ok := fbcMap[p.ModulePosition]
			if !ok {
				mod = &jsonFBCModule{ModulePosition: p.ModulePosition}
				fbcMap[p.ModulePosition] = mod
			}
			mod.Channels = append(mod.Channels, jsonFBCChannel{
				ChannelPosition: p.ChannelPosition,
				ChannelType:     string(p.ChannelType),
			})
		case types.ModuleRPC:
			rpcCount++
			rpcCounters = append(rpcCounters, jsonRPCCounter{
				ModulePosition: p.ModulePosition,
				CounterName:    p.CounterName,
				CounterValue:   p.CounterValue,
			})
		}
	}

	// Sort FBC modules by position
	fbcModules := make([]jsonFBCModule, 0, len(fbcMap))
	for pos := 1; pos <= 64; pos++ {
		if mod, ok := fbcMap[pos]; ok {
			fbcModules = append(fbcModules, *mod)
		}
	}

	report := jsonReport{
		Title: fmt.Sprintf("LOGReport — %s", node.Name),
		Node: jsonNode{
			Name:    node.Name,
			Address: node.Address,
			Type:    string(node.Type),
			Status:  string(node.Status),
			Port:    node.Port,
		},
		FBCModules:     fbcModules,
		RPCCounters:    rpcCounters,
		IOPoints:       ioPoints,
		GeneratedAt:    time.Now().UTC().Format(time.RFC3339),
		TotalFBC:       fbcCount,
		TotalRPC:       rpcCount,
		TotalIOPoints:  len(ioPoints),
	}

	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return "", fmt.Errorf("json: marshal: %w", err)
	}

	if err := os.WriteFile(filePath, data, 0644); err != nil {
		return "", fmt.Errorf("json: write: %w", err)
	}

	return filePath, nil
}
