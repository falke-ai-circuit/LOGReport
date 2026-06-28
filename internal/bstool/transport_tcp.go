package bstool

// transport_tcp.go — Native Go TCP transport for the BsTool wire protocol.
//
// CORRECTED 2026-06-26 based on deep capstone disassembly:
//   - TCP sends RAW binary blocks (20-byte big-endian header + raw data payload)
//   - NO DLE/STX/ETX framing (that's RS-232 only, via send_block/rcv_block)
//   - NO CRC on TCP (TCP's own reliability replaces serial error detection)
//   - NO "2111" handshake (that's RS-232 only, via zzSend2111/zzRcv2111)
//   - NO DLE byte stuffing (TCP sends raw bytes)
//   - NO session ID / sequence toggle (those are RS-232 handshake state)
//
// The flow is simply:
//   1. Connect to host from COMMUNICATION_LINE env var, port 1516 (default)
//   2. Byte-swap header fields to big-endian (send16/send32)
//   3. send(socket, header+data, total_size) — ONE call
//   4. recv(socket, header, 20) → byte-swap back → recv(socket, data, dlen)
//
// Evidence: docs/bstool-deep-re-2026-06-26.md
//
// zzSendTcpBlk (0x43B570): send16/send32 → tcp_send_wrapper → done
// zzRcvTcpBlk  (0x43ABF0): tcp_recv_wrapper → send16/send32 → tcp_recv_wrapper
// tcp_init_impl (0x43A950): socket → gethostbyname → connect → TCP_NODELAY → SO_RCVTIMEO

import (
	"encoding/binary"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"time"
)

// ─── TCP Transport ──────────────────────────────────────────────────────────

// TCPTransport provides a native Go TCP transport for the BsTool protocol.
// It replaces BsTool.exe for TCP-connected DNA nodes.
//
// IMPORTANT: This uses the RAW binary block protocol (corrected from deep RE).
// The DLE/STX/ETX framing, CRC-16, and "2111" handshake are RS-232 ONLY.
type TCPTransport struct {
	conn      net.Conn
	host      string
	port      int
	timeout   time.Duration
	connected bool
}

// TCPTransportOption configures a TCPTransport.
type TCPTransportOption func(*TCPTransport)

// WithTCPHost sets the DNA node hostname or IP.
func WithTCPHost(host string) TCPTransportOption {
	return func(t *TCPTransport) { t.host = host }
}

// WithTCPPort sets the TCP port (default 1516).
func WithTCPPort(port int) TCPTransportOption {
	return func(t *TCPTransport) { t.port = port }
}

// WithTCPTimeout sets the socket timeout (default 1516ms).
func WithTCPTimeout(d time.Duration) TCPTransportOption {
	return func(t *TCPTransport) { t.timeout = d }
}

// NewTCPTransport creates a new TCP transport.
func NewTCPTransport(opts ...TCPTransportOption) *TCPTransport {
	t := &TCPTransport{
		port:    DefaultTCPPort,
		timeout: time.Duration(TCPDefaultTimeout) * time.Millisecond,
	}
	for _, opt := range opts {
		opt(t)
	}
	return t
}

// Connect establishes a TCP connection to the DNA node.
// Mimics tcp_init_impl (RVA 0x03A950): socket → gethostbyname → connect → setsockopt.
func (t *TCPTransport) Connect() error {
	if t.host == "" {
		return fmt.Errorf("bstool tcp: host not set")
	}

	addr := net.JoinHostPort(t.host, fmt.Sprintf("%d", t.port))

	var lastErr error
	for attempt := 0; attempt < MaxTCPRetries; attempt++ {
		if attempt > 0 {
			time.Sleep(TCPRetryDelay * time.Second)
		}

		conn, err := net.DialTimeout("tcp", addr, t.timeout)
		if err != nil {
			lastErr = err
			continue
		}

		// Set TCP_NODELAY (equivalent to setsockopt IPPROTO_TCP TCP_NODELAY)
		// and set read deadline (equivalent to SO_RCVTIMEO)
		if tcpConn, ok := conn.(*net.TCPConn); ok {
			tcpConn.SetNoDelay(true)
			tcpConn.SetReadDeadline(time.Now().Add(t.timeout))
		}

		t.conn = conn
		t.connected = true
		return nil
	}

	return fmt.Errorf("bstool tcp: failed to connect to %s after %d attempts: %w",
		addr, MaxTCPRetries, lastErr)
}

// Close closes the TCP connection.
func (t *TCPTransport) Close() error {
	if t.conn != nil {
		err := t.conn.Close()
		t.conn = nil
		t.connected = false
		return err
	}
	return nil
}

// sendBlock sends a raw binary block over TCP.
// Mimics zzSendTcpBlk (RVA 0x43B570):
//  1. Byte-swap header fields to big-endian (send16/send32)
//  2. Send entire block (header + data) in ONE write call
//
// The Block.MarshalBinary() method already produces big-endian wire format,
// so we just marshal and write.
func (t *TCPTransport) sendBlock(block *Block) error {
	wire, err := block.MarshalBinary()
	if err != nil {
		return err
	}

	// Refresh read deadline before each send
	if tcpConn, ok := t.conn.(*net.TCPConn); ok {
		tcpConn.SetReadDeadline(time.Now().Add(t.timeout))
	}

	_, err = t.conn.Write(wire)
	return err
}

// recvBlock receives a raw binary block from TCP.
// Mimics zzRcvTcpBlk (RVA 0x43ABF0):
//  1. Read 20-byte header via tcp_recv_wrapper
//  2. Byte-swap header fields back to host order (send16/send32)
//  3. Extract data_length from header[0x10]
//  4. Read data_length bytes of payload
func (t *TCPTransport) recvBlock() (*Block, error) {
	// Refresh read deadline
	if tcpConn, ok := t.conn.(*net.TCPConn); ok {
		tcpConn.SetReadDeadline(time.Now().Add(t.timeout))
	}

	// Read 20-byte header
	headerBuf := make([]byte, HeaderSize)
	if _, err := io.ReadFull(t.conn, headerBuf); err != nil {
		return nil, fmt.Errorf("bstool tcp: failed to read header: %w", err)
	}

	// Parse header (UnmarshalBinary reads big-endian)
	var block Block
	if err := block.Header.UnmarshalBinary(headerBuf); err != nil {
		return nil, err
	}

	// Read data payload (data_length bytes)
	if block.Header.DataLen > 0 {
		// Sanity check: don't read absurdly large payloads
		if block.Header.DataLen > 1024*1024 {
			return nil, fmt.Errorf("bstool tcp: data length too large: %d", block.Header.DataLen)
		}
		block.Data = make([]byte, block.Header.DataLen)
		if _, err := io.ReadFull(t.conn, block.Data); err != nil {
			return nil, fmt.Errorf("bstool tcp: failed to read data (%d bytes): %w",
				block.Header.DataLen, err)
		}
	}

	return &block, nil
}

// ErrLog retrieves RS log messages from a DNA node over TCP.
// This replaces `BsTool.exe -errlog <server>`.
//
// Debug: set BSTOOL_DEBUG=1 to log raw hex of all sent/received blocks.
//
// Flow (from zzOpenErrLog + zzGetLog disassembly):
//  1. Connect to node (host from COMMUNICATION_LINE, port 1516)
//  2. Send OPEN_ERRLOG block (cmd=0x48, data=server name + null terminator)
//  3. Receive response block (check for error codes)
//  4. Send GET_LOG_DATA blocks (cmd=0x1F, field_2=offset, field_3=chunk_size)
//  5. On first response: check field_2 (Source) for error, read field_3 (Param)
//     for total_size — this tells us how many bytes to retrieve
//  6. Read log data in 448-byte chunks
//  7. Concatenate and decode from CP1252
func (t *TCPTransport) ErrLog(serverName string) (string, error) {
	debug := os.Getenv("BSTOOL_DEBUG") != ""
	if !t.connected {
		if err := t.Connect(); err != nil {
			return "", err
		}
	}

	// Strip m/r suffix (e.g., "AP01m" → "AP01")
	stripped := stripNodeSuffix(serverName)
	if stripped == "" {
		return "", &ErrInvalidServer{}
	}

	// Phase 1: Open error log (cmd=0x48)
	serverBytes := append([]byte(stripped), 0x00) // null-terminated
	openBlock := &Block{
		Header: BlockHeader{
			Command: CmdOpenErrLog,
			DataLen: uint32(len(serverBytes)),
		},
		Data: serverBytes,
	}
	if debug {
		wire, _ := openBlock.MarshalBinary()
		log.Printf("[BSTOOL_DEBUG] OPEN_ERRLOG send: %x", wire)
	}
	if err := t.sendBlock(openBlock); err != nil {
		return "", fmt.Errorf("bstool tcp: OPEN_ERRLOG send failed: %w", err)
	}

	respBlock, err := t.recvBlock()
	if err != nil {
		return "", fmt.Errorf("bstool tcp: OPEN_ERRLOG recv failed: %w", err)
	}
	if debug {
		hdr, _ := respBlock.Header.MarshalBinary()
		log.Printf("[BSTOOL_DEBUG] OPEN_ERRLOG recv header: %x", hdr)
		log.Printf("[BSTOOL_DEBUG] OPEN_ERRLOG recv: cmd=0x%04x seq=0x%04x src=0x%08x param=0x%08x size=0x%08x dlen=%d data=%x",
			respBlock.Header.Command, respBlock.Header.Sequence,
			respBlock.Header.Source, respBlock.Header.Param,
			respBlock.Header.Size, respBlock.Header.DataLen, respBlock.Data)
	}

	// Check for error states
	if respBlock.Header.Source == 0xFFFFFFFF {
		return "", fmt.Errorf("bstool tcp: server not found (0x16)")
	}

	// Phase 2: Retrieve log data in chunks
	var logData []byte
	offset := uint32(0)
	totalSize := uint32(0)
	firstRead := true

	for {
		chunkSize := uint32(DefaultChunkSize) // 448 bytes

		req := make([]byte, 8)
		binary.LittleEndian.PutUint32(req[0:], offset)
		binary.LittleEndian.PutUint32(req[4:], chunkSize)

		getBlock := &Block{
			Header: BlockHeader{
				Command:  CmdGetLogData,
				Source:   offset,    // field_2 = offset
				Param:    chunkSize, // field_3 = chunk_size
				DataLen:  uint32(len(req)),
			},
			Data: req,
		}
		if debug {
			wire, _ := getBlock.MarshalBinary()
			log.Printf("[BSTOOL_DEBUG] GET_LOG_DATA send (offset=%d): %x", offset, wire)
		}
		if err := t.sendBlock(getBlock); err != nil {
			break
		}

		respBlock, err := t.recvBlock()
		if err != nil {
			if debug {
				log.Printf("[BSTOOL_DEBUG] GET_LOG_DATA recv error: %v", err)
			}
			break
		}
		if debug {
			hdr, _ := respBlock.Header.MarshalBinary()
			log.Printf("[BSTOOL_DEBUG] GET_LOG_DATA recv header: %x", hdr)
			log.Printf("[BSTOOL_DEBUG] GET_LOG_DATA recv: cmd=0x%04x src=0x%08x param=0x%08x size=0x%08x dlen=%d datalen=%d",
				respBlock.Header.Command, respBlock.Header.Source,
				respBlock.Header.Param, respBlock.Header.Size,
				respBlock.Header.DataLen, len(respBlock.Data))
			if len(respBlock.Data) > 0 {
				showLen := len(respBlock.Data)
				if showLen > 64 {
					showLen = 64
				}
				log.Printf("[BSTOOL_DEBUG] GET_LOG_DATA data[0:%d]: %x", showLen, respBlock.Data[:showLen])
			}
		}

		if firstRead {
			firstRead = false
			if respBlock.Header.Source == 0xFFFFFFFF {
				return "", nil
			}
			totalSize = respBlock.Header.Param
			if debug {
				log.Printf("[BSTOOL_DEBUG] first read: totalSize=%d", totalSize)
			}
			if totalSize == 0 {
				return "", nil
			}
		}

		if len(respBlock.Data) == 0 {
			break
		}

		logData = append(logData, respBlock.Data...)
		offset += uint32(len(respBlock.Data))

		if totalSize > 0 && offset >= totalSize {
			break
		}
		if len(respBlock.Data) < int(chunkSize) {
			break
		}
	}

	decoded, err := decodeWindows1252(logData)
	if err != nil {
		decoded = string(logData)
	}

	filtered := filterStatusMessages(decoded)

	return filtered, nil
}

// IsConnected returns whether the transport has an active connection.
func (t *TCPTransport) IsConnected() bool {
	return t.connected
}

// Host returns the connected host.
func (t *TCPTransport) Host() string {
	return t.host
}

// String returns a human-readable description.
func (t *TCPTransport) String() string {
	return fmt.Sprintf("TCPTransport{host=%s, port=%d, connected=%v}",
		t.host, t.port, t.connected)
}

// stripNodeSuffix is defined in client.go.
// init() is in protocol.go.
