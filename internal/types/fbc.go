package types

// ChannelType identifies an I/O unit type on an FBC module.
type ChannelType string

const (
	AI8       ChannelType = "AI8"       // Analog Input 8-channel
	AO4       ChannelType = "AO4"       // Analog Output 4-channel
	AO8       ChannelType = "AO8"       // Analog Output 8-channel
	DI16      ChannelType = "DI16"      // Digital Input 16-channel
	DO16      ChannelType = "DO16"      // Digital Output 16-channel
	BI8       ChannelType = "BI8"       // Binary Input 8-channel
	BI8N      ChannelType = "BI8N"      // Binary Input 8-channel (N variant)
	BO8       ChannelType = "BO8"       // Binary Output 8-channel
	TI6       ChannelType = "TI6"       // Temperature Input 6-channel
	TO6       ChannelType = "TO6"       // Temperature Output 6-channel
	PI4       ChannelType = "PI4"       // Pulse Input 4-channel
	PO4       ChannelType = "PO4"       // Pulse Output 4-channel
	SI8       ChannelType = "SI8"       // Serial Input 8-channel
	SO8       ChannelType = "SO8"       // Serial Output 8-channel
	CI4       ChannelType = "CI4"       // Counter Input 4-channel
	CO4       ChannelType = "CO4"       // Counter Output 4-channel
	RI4       ChannelType = "RI4"       // Relay Input 4-channel
	RO4       ChannelType = "RO4"       // Relay Output 4-channel
	II4       ChannelType = "II4"       // Isolated Input 4-channel
	IO4       ChannelType = "IO4"       // Isolated Output 4-channel
	NotExists ChannelType = "N/E"       // Slot not populated
)

// HeaderType distinguishes between PIC and IBC FBC header formats.
type HeaderType string

const (
	PIC HeaderType = "PIC"
	IBC HeaderType = "IBC"
)

// FBCChannel represents a single I/O channel slot on an FBC module.
type FBCChannel struct {
	Position int         `json:"position"`
	Type     ChannelType `json:"type"`
	Sum      int         `json:"sum"`
}

// FBCModule represents one FBC (Field Bus Controller) module.
type FBCModule struct {
	Position int          `json:"position"`
	Channels []FBCChannel `json:"channels"`
	Exists   bool         `json:"exists"`
}
