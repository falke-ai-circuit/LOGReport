package types

// ModuleType identifies whether an IO point comes from FBC or RPC.
type ModuleType string

const (
	ModuleFBC ModuleType = "fbc"
	ModuleRPC ModuleType = "rpc"
)

// IOPoint represents a single IO point — either an FBC channel or an RPC counter.
// It is the unified type used by the store layer for persistence.
type IOPoint struct {
	NodeAddress     string      `json:"node_address"`
	ModulePosition  int         `json:"module_position"`
	ChannelPosition int         `json:"channel_position"`
	ChannelType     ChannelType `json:"channel_type,omitempty"`
	ModuleType      ModuleType  `json:"module_type"`
	CounterName     string      `json:"counter_name,omitempty"`
	CounterValue    int         `json:"counter_value,omitempty"`
}

// FBCToIOPoints converts FBC modules to a flat list of IOPoints.
func FBCToIOPoints(nodeAddress string, modules []FBCModule) []IOPoint {
	var points []IOPoint
	for _, mod := range modules {
		if !mod.Exists {
			continue
		}
		for _, ch := range mod.Channels {
			points = append(points, IOPoint{
				NodeAddress:     nodeAddress,
				ModulePosition:  mod.Position,
				ChannelPosition: ch.Position,
				ChannelType:     ch.Type,
				ModuleType:      ModuleFBC,
			})
		}
	}
	return points
}

// RPCToIOPoints converts RPC modules to a flat list of IOPoints.
func RPCToIOPoints(nodeAddress string, modules []RPCModule) []IOPoint {
	var points []IOPoint
	for _, mod := range modules {
		if !mod.Exists {
			continue
		}
		for _, ctr := range mod.Counters {
			points = append(points, IOPoint{
				NodeAddress:     nodeAddress,
				ModulePosition:  mod.Position,
				ChannelPosition: 0, // RPC counters don't have channel positions
				ModuleType:      ModuleRPC,
				CounterName:     ctr.Name,
				CounterValue:    ctr.Value,
			})
		}
	}
	return points
}
