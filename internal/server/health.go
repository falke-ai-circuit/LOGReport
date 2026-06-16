package server

import (
	"database/sql"
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

// GetHealth builds a Health struct from the database connection and start time.
func GetHealth(db *sql.DB, startTime time.Time) Health {
	h := Health{
		Status:  "ok",
		Version: "0.1.0",
		Uptime:  formatUptime(time.Since(startTime)),
	}

	// Check DB status
	if db == nil {
		h.DBStatus = "disconnected"
		h.Status = "degraded"
	} else if err := db.Ping(); err != nil {
		h.DBStatus = fmt.Sprintf("error: %v", err)
		h.Status = "degraded"
	} else {
		h.DBStatus = "connected"
	}

	// Count nodes
	if db != nil {
		var count int
		if err := db.QueryRow("SELECT COUNT(*) FROM nodes").Scan(&count); err == nil {
			h.NodeCount = count
		}
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
