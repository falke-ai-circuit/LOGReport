package server

import (
	"fmt"
	"time"
)

// Health represents the server health status returned by GET /health.
type Health struct {
	Status    string `json:"status"`
	Version   string `json:"version"`
	Uptime    string `json:"uptime"`
	DBStatus  string `json:"db_status"`
	NodeCount int    `json:"node_count"`
}

// GetHealth builds a Health struct from the database connection status and start time.
// dbConnected is true when the store is operational.
func GetHealth(dbConnected bool, startTime time.Time) Health {
	h := Health{
		Status:  "ok",
		Version: "1.0.0",
		Uptime:  formatUptime(time.Since(startTime)),
	}

	if dbConnected {
		h.DBStatus = "connected"
	} else {
		h.DBStatus = "disconnected"
		h.Status = "degraded"
	}

	return h
}

// formatUptime formats a duration as a human-readable uptime string.
func formatUptime(d time.Duration) string {
	if d < time.Second {
		return "0s"
	}
	hours := int(d.Hours())
	minutes := int(d.Minutes()) % 60
	seconds := int(d.Seconds()) % 60

	if hours > 0 {
		return fmt.Sprintf("%dh%dm%ds", hours, minutes, seconds)
	}
	if minutes > 0 {
		return fmt.Sprintf("%dm%ds", minutes, seconds)
	}
	return fmt.Sprintf("%ds", seconds)
}