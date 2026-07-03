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

	// Wait for "Access code:" prompt
	_, err = c.readUntil("Access code:", 5*time.Second)
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

	// Wait for command prompt ">>"
	_, err = c.readUntil(">>", 5*time.Second)
	if err != nil {
		return fmt.Errorf("lisdiag: waiting for prompt after auth: %w", err)
	}

	return nil
}

// Close closes the connection.
func (c *Client) Close() {
	if c.conn != nil {
		// Send quit command before closing
		fmt.Fprintf(c.conn, "q\r\n")
		c.conn.Close()
		c.conn = nil
	}
}

// SendCommand sends a command and returns the output text.
// Reads until the next ">>" prompt appears or timeout.
// The LisDiag output function writes frame data as text lines.
func (c *Client) SendCommand(command string, timeout time.Duration) (string, error) {
	if c.conn == nil {
		return "", fmt.Errorf("lisdiag: not connected")
	}

	// Send command
	if _, err := fmt.Fprintf(c.conn, "%s\r\n", command); err != nil {
		return "", fmt.Errorf("lisdiag: send %q: %w", command, err)
	}

	// Read output until we see the prompt again
	output, err := c.readUntil(">>", timeout)
	if err != nil {
		return output, fmt.Errorf("lisdiag: reading response for %q: %w", command, err)
	}

	return output, nil
}

// readUntil reads text until the given prompt string appears.
// Returns all text read (excluding the prompt itself) or error on timeout.
func (c *Client) readUntil(prompt string, timeout time.Duration) (string, error) {
	_ = c.conn.SetReadDeadline(time.Now().Add(timeout))
	var sb strings.Builder

	for {
		line, err := c.reader.ReadString('\n')
		sb.WriteString(line)

		if strings.Contains(line, prompt) {
			// Found the prompt — return everything before it
			result := sb.String()
			idx := strings.LastIndex(result, prompt)
			if idx >= 0 {
				result = result[:idx]
			}
			return strings.TrimRight(result, "\r\n"), nil
		}

		if err != nil {
			return sb.String(), err
		}
	}
}

// IRBCommand builds an irb command for a given channel (exe number).
// irb displays recently received LIS frames with timestamps.
// irb alone shows a few recent frames; irb <n> shows n frames.
// channel is 0-indexed (exe1=0, exe2=1, ..., exe6=5).
func IRBCommand(channel int) string {
	return fmt.Sprintf("irb %d", channel)
}

// ORBCommand builds an orb command for a given channel (exe number).
// orb displays recently transmitted LIS frames with timestamps.
func ORBCommand(channel int) string {
	return fmt.Sprintf("orb %d", channel)
}

// IRBAllCommand shows a few most recently received frames on current channel.
func IRBAllCommand() string {
	return "irb"
}

// ORBAllCommand shows a few most recently transmitted frames on current channel.
func ORBAllCommand() string {
	return "orb"
}

// ExeCommand switches to a specific execution/channel.
// exe command sets the current channel (1-indexed: exe1 through exe6).
func ExeCommand(exeNum int) string {
	return fmt.Sprintf("exe %d", exeNum)
}