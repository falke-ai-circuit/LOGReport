package telnet

import (
	"fmt"
	"net"
	"strings"
	"sync"
	"testing"
	"time"
)

// mockDNAServer starts a TCP listener that mimics a Valmet DNA node.
// It accepts one connection, sends a banner, echoes commands, and
// responds with a prompt. Returns the listening address and a stop function.
func mockDNAServer(t *testing.T, behavior func(conn net.Conn)) (addr string, stop func()) {
	t.Helper()

	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("mock server listen: %v", err)
	}

	addr = listener.Addr().String()

	var wg sync.WaitGroup
	wg.Add(1)
	done := make(chan struct{})

	go func() {
		defer wg.Done()
		conn, err := listener.Accept()
		if err != nil {
			select {
			case <-done:
				return
			default:
				t.Logf("mock server accept: %v", err)
				return
			}
		}
		defer conn.Close()
		behavior(conn)
	}()

	stop = func() {
		close(done)
		listener.Close()
		wg.Wait()
	}

	return addr, stop
}

// standardDNABehavior sends a banner, echoes the command, and returns
// a response with a prompt — mimicking a real DNA node.
func standardDNABehavior(conn net.Conn) {
	buf := make([]byte, 4096)

	// Send banner
	conn.Write([]byte("Welcome to Valmet DNA\r\n"))

	// Read command
	n, _ := conn.Read(buf)
	cmd := string(buf[:n])
	cmd = strings.TrimSpace(cmd)

	// Echo and respond
	response := fmt.Sprintf("Executing: %s\r\nOutput data here\r\n162a%% ", cmd)
	conn.Write([]byte(response))
}

// authFailureBehavior sends a banner then rejects with auth error.
func authFailureBehavior(conn net.Conn) {
	conn.Write([]byte("Welcome to Valmet DNA\r\n"))
	buf := make([]byte, 4096)
	conn.Read(buf)
	conn.Write([]byte("Authentication failed\r\nAccess denied\r\n"))
}

// slowServerBehavior delays response to trigger timeout.
func slowServerBehavior(conn net.Conn) {
	conn.Write([]byte("Welcome to Valmet DNA\r\n"))
	buf := make([]byte, 4096)
	conn.Read(buf)
	// Sleep longer than the test timeout
	time.Sleep(5 * time.Second)
	conn.Write([]byte("162a% "))
}

// chunkedBehavior sends response in small chunks.
func chunkedBehavior(conn net.Conn) {
	conn.Write([]byte("Welcome to Valmet DNA\r\n"))
	buf := make([]byte, 4096)
	conn.Read(buf)

	// Send response in small chunks
	chunks := []string{"Exec", "uting:", " show", " all", "\r\n", "Proc", "ess", " list", "\r\n", "162a% "}
	for _, chunk := range chunks {
		conn.Write([]byte(chunk))
		time.Sleep(50 * time.Millisecond)
	}
}

// dropMidBehavior sends partial response then closes connection.
func dropMidBehavior(conn net.Conn) {
	conn.Write([]byte("Welcome to Valmet DNA\r\n"))
	buf := make([]byte, 4096)
	conn.Read(buf)
	conn.Write([]byte("Partial response data..."))
	conn.Close()
}

// nonASCIIBehavior sends response with non-ASCII bytes.
func nonASCIIBehavior(conn net.Conn) {
	conn.Write([]byte("Welcome to Valmet DNA\r\n"))
	buf := make([]byte, 4096)
	conn.Read(buf)
	// Include some non-ASCII bytes in response
	response := []byte("Data: \x80\x81\x82 valid text here\r\n162a% ")
	conn.Write(response)
}

// TestDialAndSendCommand tests basic Dial → SendCommand → ReadUntilPrompt flow.
func TestDialAndSendCommand(t *testing.T) {
	addr, stop := mockDNAServer(t, standardDNABehavior)
	defer stop()

	host, port := parseAddr(t, addr)

	client, err := Dial(host, port, 5*time.Second)
	if err != nil {
		t.Fatalf("Dial failed: %v", err)
	}
	defer client.Close()

	err = client.SendCommand("show all")
	if err != nil {
		t.Fatalf("SendCommand failed: %v", err)
	}

	response, err := client.ReadUntilPrompt()
	if err != nil {
		t.Fatalf("ReadUntilPrompt failed: %v", err)
	}

	if !strings.Contains(response, "Output data here") {
		t.Errorf("response missing expected data: %q", response)
	}

	if !IsPrompt(response) {
		t.Errorf("response does not end with prompt: %q", response)
	}
}

// TestAuthFailure tests that auth failure response is read correctly.
func TestAuthFailure(t *testing.T) {
	addr, stop := mockDNAServer(t, authFailureBehavior)
	defer stop()

	host, port := parseAddr(t, addr)

	client, err := Dial(host, port, 5*time.Second)
	if err != nil {
		t.Fatalf("Dial failed: %v", err)
	}
	defer client.Close()

	err = client.SendCommand("show all")
	if err != nil {
		t.Fatalf("SendCommand failed: %v", err)
	}

	response, err := client.ReadUntilPrompt()
	// May get EOF or timeout since no prompt is sent
	if err != nil {
		t.Logf("ReadUntilPrompt returned error (expected, no prompt): %v", err)
	}

	if !strings.Contains(response, "Authentication failed") {
		t.Errorf("response missing auth failure message: %q", response)
	}
}

// TestTimeout tests that a slow server triggers timeout.
func TestTimeout(t *testing.T) {
	addr, stop := mockDNAServer(t, slowServerBehavior)
	defer stop()

	host, port := parseAddr(t, addr)

	client, err := Dial(host, port, 1*time.Second)
	if err != nil {
		t.Fatalf("Dial failed: %v", err)
	}
	defer client.Close()

	err = client.SendCommand("show all")
	if err != nil {
		t.Fatalf("SendCommand failed: %v", err)
	}

	_, err = client.ReadUntilPrompt()
	if err == nil {
		t.Error("expected timeout error, got nil")
	}
}

// TestEncodingEdgeCases tests non-ASCII bytes in response.
func TestEncodingEdgeCases(t *testing.T) {
	addr, stop := mockDNAServer(t, nonASCIIBehavior)
	defer stop()

	host, port := parseAddr(t, addr)

	client, err := Dial(host, port, 5*time.Second)
	if err != nil {
		t.Fatalf("Dial failed: %v", err)
	}
	defer client.Close()

	err = client.SendCommand("show all")
	if err != nil {
		t.Fatalf("SendCommand failed: %v", err)
	}

	response, err := client.ReadUntilPrompt()
	if err != nil {
		t.Fatalf("ReadUntilPrompt failed: %v", err)
	}

	if !strings.Contains(response, "valid text here") {
		t.Errorf("response missing valid text: %q", response)
	}

	if !IsPrompt(response) {
		t.Errorf("response does not end with prompt: %q", response)
	}
}

// TestPartialResponse tests data arriving in chunks.
func TestPartialResponse(t *testing.T) {
	addr, stop := mockDNAServer(t, chunkedBehavior)
	defer stop()

	host, port := parseAddr(t, addr)

	client, err := Dial(host, port, 5*time.Second)
	if err != nil {
		t.Fatalf("Dial failed: %v", err)
	}
	defer client.Close()

	err = client.SendCommand("show all")
	if err != nil {
		t.Fatalf("SendCommand failed: %v", err)
	}

	response, err := client.ReadUntilPrompt()
	if err != nil {
		t.Fatalf("ReadUntilPrompt failed: %v", err)
	}

	if !strings.Contains(response, "Process list") {
		t.Errorf("response missing chunked data: %q", response)
	}

	if !IsPrompt(response) {
		t.Errorf("response does not end with prompt: %q", response)
	}
}

// TestConnectionDropMidOperation tests connection drop mid-operation.
func TestConnectionDropMidOperation(t *testing.T) {
	addr, stop := mockDNAServer(t, dropMidBehavior)
	defer stop()

	host, port := parseAddr(t, addr)

	client, err := Dial(host, port, 5*time.Second)
	if err != nil {
		t.Fatalf("Dial failed: %v", err)
	}
	defer client.Close()

	err = client.SendCommand("show all")
	if err != nil {
		t.Fatalf("SendCommand failed: %v", err)
	}

	response, err := client.ReadUntilPrompt()
	// EOF is expected
	if err != nil {
		t.Logf("ReadUntilPrompt returned error (expected on drop): %v", err)
	}

	if !strings.Contains(response, "Partial response data") {
		t.Errorf("response missing partial data: %q", response)
	}
}

// TestSendCommandNotConnected tests error when sending without connection.
func TestSendCommandNotConnected(t *testing.T) {
	client := &Client{conn: nil}
	err := client.SendCommand("show all")
	if err == nil {
		t.Error("expected error for SendCommand on nil connection")
	}
}

// TestReadUntilPromptNotConnected tests error when reading without connection.
func TestReadUntilPromptNotConnected(t *testing.T) {
	client := &Client{conn: nil}
	_, err := client.ReadUntilPrompt()
	if err == nil {
		t.Error("expected error for ReadUntilPrompt on nil connection")
	}
}

// TestCloseNilClient tests Close on nil connection is safe.
func TestCloseNilClient(t *testing.T) {
	client := &Client{conn: nil}
	err := client.Close()
	if err != nil {
		t.Errorf("Close on nil conn should not error: %v", err)
	}
}

// TestDialInvalidHost tests Dial with invalid host.
func TestDialInvalidHost(t *testing.T) {
	_, err := Dial("invalid-host-that-does-not-exist.example", 23, 1*time.Second)
	if err == nil {
		t.Error("expected error for invalid host")
	}
}

// TestDialConnectionRefused tests Dial to a port with no listener.
func TestDialConnectionRefused(t *testing.T) {
	// Use a random high port that likely has no listener
	_, err := Dial("127.0.0.1", 19999, 500*time.Millisecond)
	if err == nil {
		t.Error("expected connection refused error")
	}
}

// TestFilterOutput tests the output filter against known patterns.
func TestFilterOutput(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "empty string",
			input:    "",
			expected: "",
		},
		{
			name:     "ansi escape codes",
			input:    "\x1b[32mHello\x1b[0m World",
			expected: "Hello World",
		},
		{
			name:     "control characters preserved newlines",
			input:    "line1\nline2\x00\x01\x02\nline3",
			expected: "line1\nline2\nline3",
		},
		{
			name:     "texitoggleure artifact",
			input:    "some texitoggleure data here",
			expected: "some  data here", // texitoggleure removed, spaces around it remain
		},
		{
			name:     "multiple spaces preserved (ASCII table formatting)",
			input:    "hello    world		tab",
			expected: "hello    worldtab", // tabs (\x09) removed; spaces preserved for table alignment
		},
		{
			name:     "leading whitespace after newline preserved (ASCII table formatting)",
			input:    "line1\n    indented line\n  another",
			expected: "line1\n    indented line\n  another", // whitespace preserved for table column alignment
		},
		{
			name:     "combined artifacts",
			input:    "\x1b[1mHeader\x1b[0m\n    texitoggleure  \x00data\x1b[31m\x1b[0m\n  more",
			expected: "Header\n      data\n  more", // texitoggleure removed, spaces preserved (4 from indent + 2 after texitoggleure = 6)
		},
		{
			name:     "ansi clear line code",
			input:    "text\x1b[2Kmore",
			expected: "textmore",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := FilterOutput(tt.input)
			if result != tt.expected {
				t.Errorf("FilterOutput(%q) = %q, want %q", tt.input, result, tt.expected)
			}
		})
	}
}

// TestCommandFunctions tests command generation functions.
func TestCommandFunctions(t *testing.T) {
	tests := []struct {
		name     string
		fn       func(string) string
		token    string
		expected string
	}{
		{"FBCPrint", FBCPrint, "162", "print from fbc io structure 1620000"},
		{"FBCClear", FBCClear, "162", "clear fbc io structure 1620000"},
		{"RPCPrint", RPCPrint, "162", "print from fbc rupi counters 1620000"},
		{"RPCClear", RPCClear, "162", "clear fbc rupi counters 1620000"},
		{"FBCPrint short token", FBCPrint, "5", "print from fbc io structure 50000"},
		{"RPCPrint long token", RPCPrint, "1234", "print from fbc rupi counters 12340000"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.fn(tt.token)
			if result != tt.expected {
				t.Errorf("%s(%q) = %q, want %q", tt.name, tt.token, result, tt.expected)
			}
		})
	}
}

// TestCommandResolver tests the CommandResolver map.
func TestCommandResolver(t *testing.T) {
	tests := []struct {
		key      string
		token    string
		expected string
	}{
		{"ps", "", "show all"},
		{"fis", "162", "print_fieldbus 1620000"},
		{"rc", "162", "print_fieldbus_rupi_counters 1620000"},
		{"fis", "5", "print_fieldbus 50000"},
	}

	for _, tt := range tests {
		t.Run(tt.key+"_"+tt.token, func(t *testing.T) {
			fn, ok := CommandResolver[tt.key]
			if !ok {
				t.Fatalf("CommandResolver missing key %q", tt.key)
			}
			result := fn(tt.token)
			if result != tt.expected {
				t.Errorf("CommandResolver[%q](%q) = %q, want %q", tt.key, tt.token, result, tt.expected)
			}
		})
	}
}

// TestIsPrompt tests prompt detection.
func TestIsPrompt(t *testing.T) {
	tests := []struct {
		input    string
		isPrompt bool
	}{
		{"some output\n162a% ", true},
		{"162a% ", true},
		{"data\r\n162a% ", true},
		{"no prompt here", false},
		{"162a%", true}, // \s* allows zero trailing whitespace
		{"\n999z%  ", true},
	}

	for _, tt := range tests {
		t.Run("", func(t *testing.T) {
			result := IsPrompt(tt.input)
			if result != tt.isPrompt {
				t.Errorf("IsPrompt(%q) = %v, want %v", tt.input, result, tt.isPrompt)
			}
		})
	}
}

// parseAddr splits "host:port" into host string and port int.
func parseAddr(t *testing.T, addr string) (string, int) {
	t.Helper()
	host, portStr, err := net.SplitHostPort(addr)
	if err != nil {
		t.Fatalf("split host port %q: %v", addr, err)
	}
	var port int
	fmt.Sscanf(portStr, "%d", &port)
	return host, port
}
