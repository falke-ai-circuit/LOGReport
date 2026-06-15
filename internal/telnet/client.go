// Package telnet provides a native Go telnet client for communicating
// with Valmet DNA nodes. It replaces the Python telnetlib-based client
// with a pure Go implementation using net.Dial and regex-based prompt
// detection.
package telnet

import (
	"context"
	"fmt"
	"io"
	"net"
	"regexp"
	"time"
)

// promptPatterns mirrors the Python telnet_client.py:12-16 prompt regexes.
// These detect the Valmet DNA command prompt (e.g. "162a% ").
var promptPatterns = []*regexp.Regexp{
	regexp.MustCompile(`\n\d+[a-z]%\s*$`),  // prompt after newline
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
	addr := fmt.Sprintf("%s:%d", host, port)

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
func (c *Client) ReadUntilPrompt() (string, error) {
	return c.ReadUntilPromptContext(context.Background())
}

// ReadUntilPromptContext reads until prompt with context-based timeout.
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
			response = append(response, buf[:n]...)
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
