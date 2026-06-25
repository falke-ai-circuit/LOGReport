// Package server provides server configuration, health checks, and
// graceful shutdown for the LOGReport HTTP API.
package server

import (
	"flag"
	"fmt"
	"os"
)

// Config holds server configuration parsed from command-line flags.
type Config struct {
	Port          int
	DBPath        string
	LogLevel      string
	CORSOrigin    string
	BsToolPath    string
	BsToolRemote  string
	BsToolTimeout int
}

// ParseFlags parses command-line flags and returns a Config.
// Supported flags: --port, --db-path, --log-level, --cors-origin,
// --bstool-path, --bstool-remote, --bstool-timeout.
func ParseFlags() *Config {
	cfg := &Config{}

	// Only parse if flags haven't been parsed yet (test-safe)
	if flag.Lookup("port") == nil {
		flag.IntVar(&cfg.Port, "port", 8642, "HTTP server port")
		flag.StringVar(&cfg.DBPath, "db-path", "logreport.db", "SQLite database path")
		flag.StringVar(&cfg.LogLevel, "log-level", "info", "Log level (debug, info, warn, error)")
		flag.StringVar(&cfg.CORSOrigin, "cors-origin", "", "CORS allowed origin (empty = no CORS)")
		flag.StringVar(&cfg.BsToolPath, "bstool-path", "", "Path to BsTool.exe (auto-detect if empty)")
		flag.StringVar(&cfg.BsToolRemote, "bstool-remote", "", "hermes-remote agent for remote BsTool execution")
		flag.IntVar(&cfg.BsToolTimeout, "bstool-timeout", 15, "Default BsTool timeout in seconds")
	}

	// Parse os.Args[1:] but don't fail on unknown flags in test environments
	// Use a custom FlagSet to avoid interfering with go test flags
	fs := flag.NewFlagSet("logreport", flag.ContinueOnError)
	fs.IntVar(&cfg.Port, "port", 8642, "HTTP server port")
	fs.StringVar(&cfg.DBPath, "db-path", "logreport.db", "SQLite database path")
	fs.StringVar(&cfg.LogLevel, "log-level", "info", "Log level")
	fs.StringVar(&cfg.CORSOrigin, "cors-origin", "", "CORS allowed origin")
	fs.StringVar(&cfg.BsToolPath, "bstool-path", "", "Path to BsTool.exe")
	fs.StringVar(&cfg.BsToolRemote, "bstool-remote", "", "hermes-remote agent for remote BsTool execution")
	fs.IntVar(&cfg.BsToolTimeout, "bstool-timeout", 15, "Default BsTool timeout in seconds")

	// Filter out test flags
	var args []string
	for _, a := range os.Args[1:] {
		if a == "-test.v" || a == "-test.run" || a == "-test.count" ||
			a == "-test.timeout" || a == "-test.paniconexit0" ||
			a == "-test.coverprofile" || a == "-test.outputdir" ||
			a == "-test.bench" || a == "-test.benchtime" ||
			a == "-test.mutexprofile" || a == "-test.trace" ||
			a == "-test.blockprofile" || a == "-test.memprofile" ||
			a == "-test.cpuprofile" || a == "-test.list" ||
			a == "-test.failfast" || a == "-test.short" ||
			a == "-test.shuffle" || a == "-test.fullpath" {
			continue
		}
		// Skip values that follow test flags
		if len(args) > 0 {
			prev := args[len(args)-1]
			if prev == "-test.run" || prev == "-test.count" ||
				prev == "-test.timeout" || prev == "-test.coverprofile" ||
				prev == "-test.outputdir" || prev == "-test.bench" ||
				prev == "-test.benchtime" || prev == "-test.mutexprofile" ||
				prev == "-test.trace" || prev == "-test.blockprofile" ||
				prev == "-test.memprofile" || prev == "-test.cpuprofile" ||
				prev == "-test.list" || prev == "-test.shuffle" {
				args = args[:len(args)-1] // remove the flag itself too
				continue
			}
		}
		args = append(args, a)
	}

	fs.Parse(args)

	return cfg
}

// Addr returns the listen address string (e.g., ":8080").
func (c *Config) Addr() string {
	return fmt.Sprintf(":%d", c.Port)
}
