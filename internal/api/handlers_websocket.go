package api

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/falke-ai-circuit/LOGReport/internal/telnet"
	"github.com/gorilla/websocket"
)

// wsUpgrader is the WebSocket upgrader. Allows all origins for development.
var wsUpgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true // Allow all origins (dev mode)
	},
	ReadBufferSize:  4096,
	WriteBufferSize: 4096,
}

// ─── Telnet WebSocket ──────────────────────────────────────────────

// telnetWSMessage is the JSON message format for telnet WebSocket.
type telnetWSMessage struct {
	Action  string `json:"action"`            // "connect", "command", "disconnect"
	Host    string `json:"host,omitempty"`    // for "connect"
	Port    int    `json:"port,omitempty"`    // for "connect"
	Command string `json:"command,omitempty"` // for "command"
}

// telnetWSResponse is the JSON message sent from server to client.
type telnetWSResponse struct {
	Type       string `json:"type"`                  // "output", "status", "error", "prompt"
	Data       string `json:"data,omitempty"`        // for "output", "prompt"
	Connected  bool   `json:"connected,omitempty"`   // for "status"
	SessionID  string `json:"session_id,omitempty"`  // for "status"
	Message    string `json:"message,omitempty"`     // for "error"
}

// telnetWSHandler handles WebSocket connections for interactive telnet sessions.
//
// URL: ws://host/api/v1/telnet/ws?session={sessionID}
//
// Messages from client (JSON):
//
//	{"action": "connect", "host": "192.168.1.101", "port": 2077}
//	{"action": "command", "command": "show all"}
//	{"action": "disconnect"}
//
// Messages from server (JSON):
//
//	{"type": "output", "data": "FBC agent 162\nPIC  5  6  7..."}
//	{"type": "status", "connected": true, "session_id": "sess-xxx"}
//	{"type": "error", "message": "Connection failed"}
//	{"type": "prompt", "data": "1a% "}
func (s *Server) telnetWSHandler(w http.ResponseWriter, r *http.Request) {
	conn, err := wsUpgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("ws: telnet upgrade error: %v", err)
		return
	}
	defer conn.Close()

	// Set ping/pong deadlines
	conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	conn.SetPongHandler(func(string) error {
		conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})

	// Ping ticker
	pingDone := make(chan struct{})
	go func() {
		ticker := time.NewTicker(30 * time.Second)
		defer ticker.Stop()
		for {
			select {
			case <-ticker.C:
				if err := conn.WriteMessage(websocket.PingMessage, nil); err != nil {
					return
				}
			case <-pingDone:
				return
			}
		}
	}()
	defer close(pingDone)

	var sessionID string

	// Read loop: process messages from client
	for {
		_, msgBytes, err := conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseNormalClosure) {
				log.Printf("ws: telnet read error: %v", err)
			}
			break
		}

		var msg telnetWSMessage
		if err := json.Unmarshal(msgBytes, &msg); err != nil {
			s.writeTelnetWS(conn, telnetWSResponse{Type: "error", Message: "invalid JSON message"})
			continue
		}

		switch msg.Action {
		case "connect":
			if msg.Host == "" {
				s.writeTelnetWS(conn, telnetWSResponse{Type: "error", Message: "host is required for connect"})
				continue
			}
			port := msg.Port
			if port == 0 {
				port = 23
			}

			// Disconnect existing session if any
			if sessionID != "" {
				s.telnetSM.Disconnect(sessionID)
			}

			sess, err := s.telnetSM.Connect("", msg.Host, port, 10*time.Second)
			if err != nil {
				s.writeTelnetWS(conn, telnetWSResponse{Type: "error", Message: fmt.Sprintf("connection failed: %v", err)})
				continue
			}
			sessionID = sess.ID

			s.writeTelnetWS(conn, telnetWSResponse{
				Type:      "status",
				Connected: true,
				SessionID: sessionID,
			})

			// Start output reader goroutine
			go s.streamTelnetOutput(conn, sess, pingDone)

		case "command":
			if sessionID == "" {
				s.writeTelnetWS(conn, telnetWSResponse{Type: "error", Message: "not connected"})
				continue
			}
			if err := s.telnetSM.SendCommand(sessionID, msg.Command); err != nil {
				s.writeTelnetWS(conn, telnetWSResponse{Type: "error", Message: fmt.Sprintf("command failed: %v", err)})
				continue
			}

		case "disconnect":
			if sessionID != "" {
				s.telnetSM.Disconnect(sessionID)
				sessionID = ""
			}
			s.writeTelnetWS(conn, telnetWSResponse{Type: "status", Connected: false})

		default:
			s.writeTelnetWS(conn, telnetWSResponse{Type: "error", Message: "unknown action: " + msg.Action})
		}
	}

	// Clean up session on disconnect
	if sessionID != "" {
		s.telnetSM.Disconnect(sessionID)
	}
}

// streamTelnetOutput reads from the session's Output channel and writes
// to the WebSocket. Detects prompt patterns to send "prompt" messages.
func (s *Server) streamTelnetOutput(conn *websocket.Conn, sess *telnet.Session, done <-chan struct{}) {
	for {
		select {
		case <-done:
			return
		case output, ok := <-sess.Output:
			if !ok {
				return
			}
			// Check for prompt pattern
			isPrompt := telnet.IsPrompt(output)
			s.writeTelnetWS(conn, telnetWSResponse{Type: "output", Data: output})
			if isPrompt {
				s.writeTelnetWS(conn, telnetWSResponse{Type: "prompt", Data: output})
			}
		}
	}
}

// writeTelnetWS writes a WebSocket message safely.
// Uses a per-connection mutex to prevent concurrent write races between
// the output streaming goroutine and the main read loop.
type wsConn struct {
	mu sync.Mutex
}

// wsMuMap protects WebSocket connections from concurrent writes.
// Each goroutine that writes to the same WebSocket must acquire the lock.
// We use a package-level mutex per Server instance instead, since
// typically only one WebSocket connection is active at a time per handler.
var wsWriteMu sync.Mutex

// writeTelnetWS writes a WebSocket message with mutex protection.
func (s *Server) writeTelnetWS(conn *websocket.Conn, resp telnetWSResponse) {
	data, err := json.Marshal(resp)
	if err != nil {
		return
	}
	wsWriteMu.Lock()
	defer wsWriteMu.Unlock()
	if err := conn.WriteMessage(websocket.TextMessage, data); err != nil {
		log.Printf("ws: telnet write error: %v", err)
	}
}

// ─── BsTool WebSocket ──────────────────────────────────────────────

// bstoolWSMessage is the JSON message format for BsTool WebSocket.
type bstoolWSMessage struct {
	Action     string `json:"action"`                       // "execute"
	ServerName string `json:"server_name,omitempty"`        // for "execute"
	Command    string `json:"command,omitempty"`            // for "execute" (future)
}

// bstoolWSResponse is the JSON message sent from server to client.
type bstoolWSResponse struct {
	Type     string `json:"type"`                // "output", "done", "error"
	Data     string `json:"data,omitempty"`      // for "output"
	ExitCode int    `json:"exit_code,omitempty"` // for "done"
	Message  string `json:"message,omitempty"`   // for "error"
}

// bstoolWSHandler handles WebSocket for BsTool output streaming.
// URL: ws://host/api/v1/bstool/ws
// Messages from client: {"action": "execute", "server_name": "AP01", "command": "..."}
// Messages from server: {"type": "output", "data": "..."}, {"type": "done", "exit_code": 0}
func (s *Server) bstoolWSHandler(w http.ResponseWriter, r *http.Request) {
	conn, err := wsUpgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("ws: bstool upgrade error: %v", err)
		return
	}
	defer conn.Close()

	conn.SetReadDeadline(time.Now().Add(120 * time.Second))
	conn.SetPongHandler(func(string) error {
		conn.SetReadDeadline(time.Now().Add(120 * time.Second))
		return nil
	})

	pingDone := make(chan struct{})
	go func() {
		ticker := time.NewTicker(30 * time.Second)
		defer ticker.Stop()
		for {
			select {
			case <-ticker.C:
				if err := conn.WriteMessage(websocket.PingMessage, nil); err != nil {
					return
				}
			case <-pingDone:
				return
			}
		}
	}()
	defer close(pingDone)

	for {
		_, msgBytes, err := conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseNormalClosure) {
				log.Printf("ws: bstool read error: %v", err)
			}
			break
		}

		var msg bstoolWSMessage
		if err := json.Unmarshal(msgBytes, &msg); err != nil {
			s.writeBsToolWS(conn, bstoolWSResponse{Type: "error", Message: "invalid JSON message"})
			continue
		}

		switch msg.Action {
		case "execute":
			if msg.ServerName == "" {
				s.writeBsToolWS(conn, bstoolWSResponse{Type: "error", Message: "server_name is required"})
				continue
			}

			// Execute BsTool errlog
			result, err := s.bstoolClient.ErrLog(r.Context(), msg.ServerName)
			if err != nil {
				s.writeBsToolWS(conn, bstoolWSResponse{
					Type:    "error",
					Message: fmt.Sprintf("bstool error: %v", err),
				})
				continue
			}

			// Stream output
			if result.RawOutput != "" {
				s.writeBsToolWS(conn, bstoolWSResponse{Type: "output", Data: result.RawOutput})
			}
			s.writeBsToolWS(conn, bstoolWSResponse{
				Type:     "done",
				ExitCode: result.ExitCode,
			})

		default:
			s.writeBsToolWS(conn, bstoolWSResponse{Type: "error", Message: "unknown action: " + msg.Action})
		}
	}
}

// writeBsToolWS writes a BsTool WebSocket message safely with mutex protection.
func (s *Server) writeBsToolWS(conn *websocket.Conn, resp bstoolWSResponse) {
	data, err := json.Marshal(resp)
	if err != nil {
		return
	}
	wsWriteMu.Lock()
	defer wsWriteMu.Unlock()
	if err := conn.WriteMessage(websocket.TextMessage, data); err != nil {
		log.Printf("ws: bstool write error: %v", err)
	}
}