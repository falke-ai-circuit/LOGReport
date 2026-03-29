package telnet

import (
	"bufio"
	"fmt"
	"net"
	"strings"
	"sync"
	"time"
)

const (
	DefaultPort    = 23
	ConnectTimeout = 10 * time.Second
	ReadTimeout    = 5 * time.Second
	WriteTimeout   = 5 * time.Second
)

type Client struct {
	mu      sync.Mutex
	conn    net.Conn
	reader  *bufio.Reader
	addr    string
	connected bool
}

func NewClient() *Client {
	return &Client{}
}

func (c *Client) Connect(ip string, port int) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if port == 0 {
		port = DefaultPort
	}
	addr := fmt.Sprintf("%s:%d", ip, port)

	conn, err := net.DialTimeout("tcp", addr, ConnectTimeout)
	if err != nil {
		return fmt.Errorf("connect %s: %w", addr, err)
	}
	c.conn = conn
	c.reader = bufio.NewReader(conn)
	c.addr = addr
	c.connected = true

	// Drain initial banner (up to 500ms)
	c.conn.SetReadDeadline(time.Now().Add(500 * time.Millisecond))
	buf := make([]byte, 4096)
	c.conn.Read(buf) // ignore banner/welcome, best effort
	c.conn.SetReadDeadline(time.Time{})

	return nil
}

func (c *Client) Disconnect() error {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.conn != nil {
		err := c.conn.Close()
		c.conn = nil
		c.connected = false
		return err
	}
	return nil
}

func (c *Client) IsConnected() bool {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.connected
}

func (c *Client) Addr() string {
	return c.addr
}

// SendCommand sends a command and reads response until prompt or timeout
func (c *Client) SendCommand(cmd string, timeoutMs int) (string, error) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if !c.connected || c.conn == nil {
		return "", fmt.Errorf("not connected")
	}

	// Write command
	c.conn.SetWriteDeadline(time.Now().Add(WriteTimeout))
	_, err := fmt.Fprintf(c.conn, "%s\r\n", cmd)
	if err != nil {
		c.connected = false
		return "", fmt.Errorf("write: %w", err)
	}

	// Read response
	timeout := time.Duration(timeoutMs) * time.Millisecond
	if timeout == 0 {
		timeout = ReadTimeout
	}
	c.conn.SetReadDeadline(time.Now().Add(timeout))
	defer c.conn.SetReadDeadline(time.Time{})

	var sb strings.Builder
	buf := make([]byte, 4096)
	for {
		n, err := c.conn.Read(buf)
		if n > 0 {
			sb.Write(buf[:n])
		}
		if err != nil {
			break // timeout or EOF — treat as end of response
		}
	}
	return sb.String(), nil
}

// ResolveCommand expands short aliases to DNA telnet commands
func ResolveCommand(cmd, contextToken string) string {
	cmd = strings.TrimSpace(strings.ToLower(cmd))
	switch cmd {
	case "ps":
		return "show all"
	case "fis":
		if contextToken != "" {
			return fmt.Sprintf("print_fieldbus %s0000", normalizeToken(contextToken))
		}
		return cmd
	case "rc":
		if contextToken != "" {
			return fmt.Sprintf("print_fieldbus_rupi_counters %s0000", normalizeToken(contextToken))
		}
		return cmd
	}
	// pattern: "{token} fis" or "{token} rc"
	parts := strings.Fields(cmd)
	if len(parts) == 2 {
		tok := parts[0]
		switch parts[1] {
		case "fis":
			return fmt.Sprintf("print_fieldbus %s0000", normalizeToken(tok))
		case "rc":
			return fmt.Sprintf("print_fieldbus_rupi_counters %s0000", normalizeToken(tok))
		}
	}
	return cmd
}

func normalizeToken(t string) string {
	t = strings.TrimSpace(t)
	// if pure digits, zero-pad to 3
	allDigit := true
	for _, r := range t {
		if r < '0' || r > '9' {
			allDigit = false
			break
		}
	}
	if allDigit && len(t) < 3 {
		return fmt.Sprintf("%03s", t)
	}
	return t
}
