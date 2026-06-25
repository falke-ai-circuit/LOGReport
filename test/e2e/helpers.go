package e2e

import (
	"strings"

	"github.com/falke-ai-circuit/LOGReport/internal/parser"
	"github.com/falke-ai-circuit/LOGReport/internal/telnet"
	"github.com/falke-ai-circuit/LOGReport/internal/types"
)

// parserParseRPC wraps the parser.ParseRPC function for E2E tests.
func parserParseRPC(output string) ([]types.RPCModule, error) {
	return parser.ParseRPC(output)
}

// parserParseFBC wraps the parser.ParseFBC function for E2E tests.
func parserParseFBC(output string) ([]types.FBCModule, error) {
	return parser.ParseFBC(output)
}

// getCommandResolver returns the resolver function for a shorthand command.
func getCommandResolver(shorthand string) (func(string) string, bool) {
	fn, ok := telnet.CommandResolver[shorthand]
	return fn, ok
}

// generateTelnetCommand generates a full-form telnet command.
func generateTelnetCommand(cmdName, token string) string {
	switch cmdName {
	case "FBCPrint(162)":
		return telnet.FBCPrint(token)
	case "FBCClear(162)":
		return telnet.FBCClear(token)
	case "RPCPrint(162)":
		return telnet.RPCPrint(token)
	case "RPCClear(162)":
		return telnet.RPCClear(token)
	}
	return ""
}

// stripSuffix removes trailing 'm' or 'r' from a node name (BsTool compatibility).
func stripSuffix(name string) string {
	return strings.TrimSuffix(strings.TrimSuffix(name, "m"), "r")
}