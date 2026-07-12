// Package lisdiag implements a telnet client for LisDiag.exe / ntLisDiag.
// LisDiag runs on a PCS station and exposes a telnet server on port 4321.
// It reads from shared memory (_LIS_IO_<station>) populated by libLISb.dll
// inside the PCS process. The telnet interface provides irb/orb/imb/omb/io
// commands to display recently received/transmitted LIS frames.
//
// Reverse-engineered from LisDiag.exe (57KB, VS2005, PDB: DNA_CA_PCS_8.118)
// using Ghidra 12.1.2. Key findings:
//   - Binds to 0.0.0.0:4321 (INADDR_ANY) — accepts from any IP
//   - Optional -i flag restricts to specific IP/subnet
//   - Optional -x flag requires access code before commands
//   - Output function FUN_00407820 writes to both socket and logfile
//   - Ring buffer structure: 9 channels (exe 0-8), 12-byte ring entries
//   - Max 128 bytes per message frame
package lisdiag

import (
	"bufio"
	"fmt"
	"net"
	"strings"
	"time"
)

// Client connects to a LisDiag telnet server.
type Client struct {
	host     string
	port     int
	password string
	conn     net.Conn
	reader   *bufio.Reader
}

// NewClient creates a new LisDiag telnet client.
// host is the PCS station IP, port is typically 4321, password is the
// access code (empty if none configured).
func NewClient(host string, port int, password string) *Client {
	return &Client{
		host:     host,
		port:     port,
		password: password,
	}
}

// Connect establishes a TCP connection to the LisDiag server.
// If a password is configured, it sends the access code and waits for
// the command prompt.
func (c *Client) Connect(timeout time.Duration) error {
	addr := fmt.Sprintf("%s:%d", c.host, c.port)
	conn, err := net.DialTimeout("tcp", addr, timeout)
	if err != nil {
		return fmt.Errorf("lisdiag: connect %s: %w", addr, err)
	}
	c.conn = conn
	c.reader = bufio.NewReader(conn)

	// If no password, just wait for the prompt
	if c.password == "" {
		// Wait for initial prompt or welcome text
		_, err := c.readUntil(">>", 5*time.Second)
		if err != nil {
			// Some versions may not send a prompt immediately
			// Try reading whatever is available
			_ = c.conn.SetReadDeadline(time.Now().Add(2 * time.Second))
			line, _ := c.reader.ReadString('\n')
			_ = line
		}
		return nil
	}

	// Wait for "Access code:" prompt (LisDiag sends "Access code : " with space before colon)
	_, err = c.readUntil("Access code", 5*time.Second)
	if err != nil {
		// Maybe no access code required despite being configured
		// Try reading available data
		_ = c.conn.SetReadDeadline(time.Now().Add(2 * time.Second))
		line, _ := c.reader.ReadString('\n')
		if strings.Contains(line, ">>") {
			return nil
		}
		return fmt.Errorf("lisdiag: waiting for access code prompt: %w", err)
	}

	// Send password
	if _, err := fmt.Fprintf(c.conn, "%s\r\n", c.password); err != nil {
		return fmt.Errorf("lisdiag: sending access code: %w", err)
	}

	// Wait for command prompt ">>" (LisDiag sends "AL01:1(0)>> ")
	_, err = c.readUntil(">>", 5*time.Second)
	if err != nil {
		return fmt.Errorf("lisdiag: waiting for prompt after auth: %w", err)
	}

	return nil
}

// Close closes the connection gracefully.
// LisDiag.exe (VS2005 C++ binary) CRASHES when sent the 'q' command —
// the quit handler has a bug that triggers an access violation.
// Instead of sending 'q', we simply close the TCP connection.
// LisDiag.exe detects the closed socket via recv() returning 0/error
// and cleans up the session internally — this is safe and does NOT crash.
// Verified: closing without 'q' allows LisDiag.exe to accept new connections
// immediately afterward.
func (c *Client) Close() {
	if c.conn != nil {
		// Do NOT send 'q' — it crashes LisDiag.exe.
		// Just close the TCP connection. LisDiag detects the closed
		// socket and cleans up internally.
		c.conn.Close()
		c.conn = nil
	}
}

// SendCommand sends a command and returns the output text.
// Reads until the next ">>" prompt appears or timeout.
// The LisDiag output function writes frame data as text lines.
// If buffers are empty, LisDiag may just echo the command and return to prompt
// with no data — the output will be empty but the command succeeds.
func (c *Client) SendCommand(command string, timeout time.Duration) (string, error) {
	if c.conn == nil {
		return "", fmt.Errorf("lisdiag: not connected")
	}

	// Send command
	if _, err := fmt.Fprintf(c.conn, "%s\r\n", command); err != nil {
		return "", fmt.Errorf("lisdiag: send %q: %w", command, err)
	}

	// Read output until we see the prompt again
	// LisDiag echoes the command on a line, then outputs data, then shows ">>"
	// With empty buffers, "io 0" is echoed and then "AL01:1(0)>> " appears immediately
	output, err := c.readUntil(">>", timeout)
	if err != nil {
		// Return partial output even on timeout — the command may have succeeded
		// but produced no data (empty buffers)
		return output, fmt.Errorf("lisdiag: reading response for %q: %w", command, err)
	}

	return output, nil
}

// readUntil reads text until the given prompt string appears.
// Returns all text read (excluding the prompt itself) or error on timeout.
// Uses byte-by-byte reading because LisDiag's prompt "AL01:1(0)>> " has no
// trailing newline — ReadString('\n') would block forever waiting for one.
func (c *Client) readUntil(prompt string, timeout time.Duration) (string, error) {
	_ = c.conn.SetReadDeadline(time.Now().Add(timeout))
	var sb strings.Builder
	buf := make([]byte, 1)

	for {
		n, err := c.conn.Read(buf)
		if n > 0 {
			sb.Write(buf[:n])
			// Check if the prompt appeared in the accumulated text
			if strings.Contains(sb.String(), prompt) {
				result := sb.String()
				idx := strings.LastIndex(result, prompt)
				if idx >= 0 {
					result = result[:idx]
				}
				return strings.TrimRight(result, "\r\n"), nil
			}
		}
		if err != nil {
			return sb.String(), err
		}
	}
}

// IOCommand builds an io command for a given channel (exe number).
// io displays BOTH recently received (irb) AND transmitted (orb) LIS frames
// with timestamps in a single output. This replaces separate irb+orb calls.
// channel is 0-indexed (exe1=0, exe2=1, ..., exe6=5).
// Reverse-engineered: FUN_00406530 in LisDiag.exe reads from both irb and orb
// ring buffers and outputs them together.
func IOCommand(channel int) string {
	return fmt.Sprintf("io %d", channel)
}

// IRBCommand builds an irb command for a given channel (exe number).
// irb displays recently received LIS frames with timestamps.
// Deprecated: prefer IOCommand which combines irb+orb in one output.
func IRBCommand(channel int) string {
	return fmt.Sprintf("irb %d", channel)
}

// ORBCommand builds an orb command for a given channel (exe number).
// orb displays recently transmitted LIS frames with timestamps.
// Deprecated: prefer IOCommand which combines irb+orb in one output.
func ORBCommand(channel int) string {
	return fmt.Sprintf("orb %d", channel)
}

// ExeCommand switches to a specific execution/channel.
// exe command sets the current channel (1-indexed: exe1 through exe6).
func ExeCommand(exeNum int) string {
	return fmt.Sprintf("exe %d", exeNum)
}

// ParseParameters extracts the LisDiag port and password from a PARAMETERS
// string like "-s AL02 -p 4321 -x password -i 192.168.255.255".
// Returns port (default 4321) and password (default "" if no -x flag).
func ParseParameters(params string) (port int, password string) {
	port = 4321 // default
	parts := splitArgs(params)
	for i := 0; i < len(parts); i++ {
		switch parts[i] {
		case "-p":
			if i+1 < len(parts) {
				fmt.Sscanf(parts[i+1], "%d", &port)
			}
		case "-x":
			if i+1 < len(parts) {
				password = parts[i+1]
			}
		}
	}
	return port, password
}

// splitArgs splits a parameter string into individual args, handling
// whitespace separation. Quoted args are not supported (Valmet .sys
// files don't use quotes in PARAMETERS).
func splitArgs(s string) []string {
	var args []string
	for _, part := range fmt.Sprintf("%s", s) {
		_ = part
	}
	// Simple whitespace split
	current := ""
	for _, c := range s {
		if c == ' ' || c == '	' {
			if current != "" {
				args = append(args, current)
				current = ""
			}
		} else {
			current += string(c)
		}
	}
	if current != "" {
		args = append(args, current)
	}
	return args
}