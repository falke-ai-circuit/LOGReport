package telnet

import "fmt"

// FBCPrint generates the "print from fbc io structure" command for a token.
// Matches Python command_generator.py:52: "print from fbc io structure {token}0000"
func FBCPrint(token string) string {
	return fmt.Sprintf("print from fbc io structure %s0000", token)
}

// FBCClear generates the "clear fbc io structure" command for a token.
// Matches Python command_generator.py:53: "clear fbc io structure {token}0000"
func FBCClear(token string) string {
	return fmt.Sprintf("clear fbc io structure %s0000", token)
}

// RPCPrint generates the "print from fbc rupi counters" command for a token.
// Matches Python command_generator.py:57: "print from fbc rupi counters {token}0000"
func RPCPrint(token string) string {
	return fmt.Sprintf("print from fbc rupi counters %s0000", token)
}

// RPCClear generates the "clear fbc rupi counters" command for a token.
// Matches Python command_generator.py:58: "clear fbc rupi counters {token}0000"
func RPCClear(token string) string {
	return fmt.Sprintf("clear fbc rupi counters %s0000", token)
}

// CommandResolver maps short command keywords to their resolved telnet
// command strings. Mirrors Python telnet_commands.py:11-21.
//
// Usage:
//
//	resolved := CommandResolver["ps"]          // "show all"
//	resolved := CommandResolver["fis"]("162")   // "print_fieldbus 1620000"
//	resolved := CommandResolver["rc"]("162")    // "print_fieldbus_rupi_counters 1620000"
var CommandResolver = map[string]func(token string) string{
	"ps": func(_ string) string {
		return "show all"
	},
	"fis": func(token string) string {
		return fmt.Sprintf("print_fieldbus %s0000", token)
	},
	"rc": func(token string) string {
		return fmt.Sprintf("print_fieldbus_rupi_counters %s0000", token)
	},
}
