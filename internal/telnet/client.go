// Package telnet provides a native Go telnet client for communicating
// with Valmet DNA nodes. It replaces the Python telnetlib-based client
// with a pure Go implementation using net.Dial and regex-based prompt
// detection.
//
// IAC (Interpret As Command) handling: DIA sends IAC DO SGA (FF FD 03)
// and WILL ECHO (FF FB 01) during connection. We respond with WILL SGA
// and DO ECHO to accept these options, which is the standard behavior
// expected by DNA diagnostic managers.
package telnet

import (
	"context"
	"fmt"
	"io"
	"net"
	"regexp"
	"time"
)

// Telnet IAC constants (RFC 854)
const (
	IAC  = 0xFF // Interpret As Command
	DONT = 0xFE
	DO   = 0xFD
	WONT = 0xFC
	WILL = 0xFB
	SB   = 0xFA // Subnegotiation Begin
	SE   = 0xF0 // Subnegotiation End

	// Option codes
	OptEcho       = 0x01
	OptSuppressGA = 0x03 // Suppress Go Ahead
	OptTermType   = 0x18 // Terminal Type
	OptWindowSize = 0x1F // Window Size (NAWS)
)

// promptPatterns mirrors the Python telnet_client.py:12-16 prompt regexes.
// These detect the Valmet DNA command prompt (e.g. "162a% ").
var promptPatterns = []*regexp.Regexp{
	regexp.MustCompile(`\n\d+[a-z]%\s*$`),   // prompt after newline
	regexp.MustCompile(`^\d+[a-z]%\s*$`),    // prompt at beginning
	regexp.MustCompile(`\r\n\d+[a-z]%\s*$`), // prompt after CR+LF
}

// Client is a native Go telnet client for DNA node communication.
type Client struct {
	conn    net.Conn
	timeout time.Duration
}

// Dial opens a TCP connection to the DNA node at host:port.
// It returns a connected Client or an error.
func Dial(host string, port int, timeout time.Duration) (*Client, error) {
	addr := net.JoinHostPort(host, fmt.Sprintf("%d", port))

	dialer := net.Dialer{Timeout: timeout}
	conn, err := dialer.Dial("tcp", addr)
	if err != nil {
		return nil, fmt.Errorf("telnet dial %s: %w", addr, err)
	}

	return &Client{
		conn:    conn,
		timeout: timeout,
	}, nil
}

// Close terminates the telnet connection.
func (c *Client) Close() error {
	if c.conn == nil {
		return nil
	}
	err := c.conn.Close()
	c.conn = nil
	return err
}

// handleIAC processes an IAC command sequence from the telnet stream.
// It sends appropriate responses for DO/WILL negotiation options.
// Returns the number of bytes consumed (the IAC sequence length).
func (c *Client) handleIAC(data []byte) int {
	if len(data) < 2 || data[0] != IAC {
		return 0
	}

	code := data[1]
	switch code {
	case DO:
		if len(data) < 3 {
			return 2
		}
		opt := data[2]
		switch opt {
		case OptSuppressGA:
			// Respond WILL SGA — suppress Go Ahead
			c.conn.Write([]byte{IAC, WILL, OptSuppressGA})
		case OptEcho:
			// Respond DO ECHO — let server handle echo
			c.conn.Write([]byte{IAC, DO, OptEcho})
		case OptTermType:
			// Respond WILL terminal type, then send terminal type subneg
			c.conn.Write([]byte{IAC, WILL, OptTermType})
		case OptWindowSize:
			// Respond WILL NAWS, then send window size subneg
			c.conn.Write([]byte{IAC, WILL, OptWindowSize})
			// Send 80x24 window size
			c.conn.Write([]byte{IAC, SB, OptWindowSize, 0x00, 0x00, 0x50, 0x00, 0x18, IAC, SE})
		default:
			// Refuse other options
			c.conn.Write([]byte{IAC, WONT, opt})
		}
		return 3
	case WILL:
		if len(data) < 3 {
			return 2
		}
		opt := data[2]
		switch opt {
		case OptEcho:
			// Accept server echo
			c.conn.Write([]byte{IAC, DO, OptEcho})
		case OptSuppressGA:
			// Accept suppress GA
			c.conn.Write([]byte{IAC, DO, OptSuppressGA})
		default:
			// Refuse
			c.conn.Write([]byte{IAC, DONT, opt})
		}
		return 3
	case DONT, WONT:
		// Acknowledge refusal
		return 3
	case SB:
		// Subnegotiation — skip until IAC SE
		if len(data) < 3 {
			return len(data)
		}
		opt := data[2]
		if opt == OptTermType && len(data) >= 4 && data[3] == 0x01 {
			// Send terminal type: "VT100"
			termType := []byte("VT100")
			resp := []byte{IAC, SB, OptTermType, 0x00}
			resp = append(resp, termType...)
			resp = append(resp, IAC, SE)
			c.conn.Write(resp)
		}
		// Find IAC SE
		for i := 3; i < len(data)-1; i++ {
			if data[i] == IAC && data[i+1] == SE {
				return i + 2
			}
		}
		return len(data)
	default:
		// Other IAC codes (NOP, etc.) — 2 bytes
		return 2
	}
}

// stripIAC removes IAC command sequences from the data buffer.
// It processes and responds to IAC commands, then returns the
// cleaned data with all IAC sequences removed.
func (c *Client) stripIAC(data []byte) []byte {
	var clean []byte
	i := 0
	for i < len(data) {
		if data[i] == IAC {
			consumed := c.handleIAC(data[i:])
			i += consumed
		} else {
			clean = append(clean, data[i])
			i++
		}
	}
	return clean
}

// SendCommand writes a command string to the connection, appending "\r\n"
// as the line terminator (matching Python telnet_client.py:93).
func (c *Client) SendCommand(cmd string) error {
	if c.conn == nil {
		return fmt.Errorf("telnet: not connected")
	}

	// Set write deadline
	if c.timeout > 0 {
		c.conn.SetWriteDeadline(time.Now().Add(c.timeout))
		defer c.conn.SetWriteDeadline(time.Time{})
	}

	data := []byte(cmd + "\r\n")
	n, err := c.conn.Write(data)
	if err != nil {
		return fmt.Errorf("telnet write: %w", err)
	}
	if n != len(data) {
		return fmt.Errorf("telnet: short write (%d/%d bytes)", n, len(data))
	}
	return nil
}

// ReadUntilPrompt reads from the connection until one of the prompt
// patterns is detected or the timeout expires. It returns the accumulated
// response text (ASCII-decoded, ignoring non-ASCII bytes).
// IAC commands are automatically processed and stripped.
func (c *Client) ReadUntilPrompt() (string, error) {
	return c.ReadUntilPromptContext(context.Background())
}

// ReadUntilPromptContext reads until prompt with context-based timeout.
// IAC commands are automatically processed and stripped from the output.
func (c *Client) ReadUntilPromptContext(ctx context.Context) (string, error) {
	if c.conn == nil {
		return "", fmt.Errorf("telnet: not connected")
	}

	// Apply timeout via context
	if c.timeout > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, c.timeout)
		defer cancel()
	}

	buf := make([]byte, 4096)
	var response []byte

	for {
		// Check context before reading
		select {
		case <-ctx.Done():
			return string(response), ctx.Err()
		default:
		}

		// Set read deadline for this chunk
		if c.timeout > 0 {
			c.conn.SetReadDeadline(time.Now().Add(500 * time.Millisecond))
		}

		n, err := c.conn.Read(buf)
		if n > 0 {
			// Strip IAC commands from the data
			cleaned := c.stripIAC(buf[:n])
			response = append(response, cleaned...)
			decoded := string(response)

			// Check for prompt patterns
			for _, pat := range promptPatterns {
				if pat.MatchString(decoded) {
					c.conn.SetReadDeadline(time.Time{})
					return decoded, nil
				}
			}
		}

		if err != nil {
			if err == io.EOF {
				c.conn.SetReadDeadline(time.Time{})
				return string(response), nil
			}
			// Timeout on individual read is expected — continue loop
			if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
				// Check context again
				select {
				case <-ctx.Done():
					return string(response), ctx.Err()
				default:
					continue
				}
			}
			return string(response), fmt.Errorf("telnet read: %w", err)
		}
	}
}

// IsPrompt checks whether a string ends with a recognized DNA prompt.
func IsPrompt(s string) bool {
	for _, pat := range promptPatterns {
		if pat.MatchString(s) {
			return true
		}
	}
	return false
}
