package bstool

// fileops.go — Remote file system operations over BsTool TCP protocol.
//
// Implements READ_DIR (0x14), GET_DIR_ENTRY (0x16), FILE_OPEN (0x00),
// FILE_READ (0x02), FILE_CLOSE (0x01) to retrieve .sys files from a remote BU.
//
// Verified against live BU (buc_16.20.exe) on 2026-06-30:
//   - READ_DIR(":s:AB01:*.sys") → param=dir context handle
//   - GET_DIR_ENTRY: pass response param as cursor; stop when param=0
//   - FILE_OPEN(":s:AB01:161.sys\0rb\0") → src=file handle
//   - FILE_READ: src=handle, param=448 → 448-byte chunks
//   - FILE_CLOSE: src=handle
//
// The BU returns directory entries with comm line prefix (e.g. "AB01:1041.sys").
// We strip this prefix so ReadFile builds the correct path ":s:AB01:1041.sys".

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"log"
	"os"
	"strings"
	"time"
)

// DirEntry represents a single directory entry from the BU.
type DirEntry struct {
	Name string // filename (without path prefix)
	Size uint32 // file size in bytes
	Date string // modification date (raw string from BU)
}

// SysFileData holds a retrieved .sys file's name and raw content.
type SysFileData struct {
	Name string // filename without prefix (e.g. "161.sys")
	Data []byte // raw file content
}

// FileTransport wraps a TCPTransport with file system operations.
type FileTransport struct {
	tcp       *TCPTransport
	handshake bool
}

// NewFileTransport creates a FileTransport from host, port, and timeout.
func NewFileTransport(host string, port int, timeout time.Duration) *FileTransport {
	return &FileTransport{
		tcp: NewTCPTransport(
			WithTCPHost(host),
			WithTCPPort(port),
			WithTCPTimeout(timeout),
		),
	}
}

// connectAndHandshake establishes connection and performs the 3x handshake.
func (ft *FileTransport) connectAndHandshake() error {
	if ft.handshake {
		return nil
	}
	if err := ft.tcp.Connect(); err != nil {
		return fmt.Errorf("fileops: connect: %w", err)
	}
	// Handshake: send 3x cmd=0x0C, BU responds param=0x02CC
	for i := 0; i < 3; i++ {
		hsBlock := &Block{
			Header: BlockHeader{
				Command:  CmdHandshake,
				Sequence: 0x0136,
				Source:   0x00EFD61C,
			},
		}
		if err := ft.tcp.sendBlock(hsBlock); err != nil {
			return fmt.Errorf("fileops: handshake send[%d]: %w", i, err)
		}
		resp, err := ft.tcp.recvBlock()
		if err != nil {
			return fmt.Errorf("fileops: handshake recv[%d]: %w", i, err)
		}
		_ = resp // BU responds with param=0x02CC
	}
	ft.handshake = true
	return nil
}

// Close closes the underlying TCP connection.
func (ft *FileTransport) Close() error {
	ft.handshake = false
	return ft.tcp.Close()
}

// ListDir lists files matching the given pattern on the remote BU.
// pattern is the glob (e.g. "*.sys"). The commLine prefix is added automatically.
// Returns directory entries or an error if the directory listing fails.
func (ft *FileTransport) ListDir(commLine, pattern string) ([]DirEntry, error) {
	if err := ft.connectAndHandshake(); err != nil {
		return nil, err
	}

	// READ_DIR: data = ":s:{commLine}:{pattern}\0"
	dirPath := fmt.Sprintf(":s:%s:%s\x00", commLine, pattern)
	readDirBlock := &Block{
		Header: BlockHeader{
			Command: CmdReadDir,
			Source:  0x00EFD61C,
			DataLen: uint32(len(dirPath)),
		},
		Data: []byte(dirPath),
	}

	debug := os.Getenv("BSTOOL_DEBUG") != ""
	if debug {
		log.Printf("[BSTOOL_DEBUG] READ_DIR send: path=%q", dirPath)
	}

	if err := ft.tcp.sendBlock(readDirBlock); err != nil {
		return nil, fmt.Errorf("fileops: READ_DIR send: %w", err)
	}

	resp, err := ft.tcp.recvBlock()
	if err != nil {
		return nil, fmt.Errorf("fileops: READ_DIR recv: %w", err)
	}

	if debug {
		log.Printf("[BSTOOL_DEBUG] READ_DIR recv: cmd=0x%04x param=0x%08x dlen=%d",
			resp.Header.Command, resp.Header.Param, resp.Header.DataLen)
	}

	cursor := resp.Header.Param
	if cursor == 0 {
		return nil, fmt.Errorf("fileops: READ_DIR returned empty (param=0)")
	}

	// Iterate directory entries using GET_DIR_ENTRY
	var entries []DirEntry
	for cursor != 0 {
		entryBlock := &Block{
			Header: BlockHeader{
				Command: CmdGetDirEntry,
				Source:  0x00EFD61C,
				Param:   cursor,
			},
		}

		if err := ft.tcp.sendBlock(entryBlock); err != nil {
			return nil, fmt.Errorf("fileops: GET_DIR_ENTRY send: %w", err)
		}

		entryResp, err := ft.tcp.recvBlock()
		if err != nil {
			return nil, fmt.Errorf("fileops: GET_DIR_ENTRY recv: %w", err)
		}

		if debug {
			log.Printf("[BSTOOL_DEBUG] GET_DIR_ENTRY recv: param=0x%08x size=%d dlen=%d data=%q",
				entryResp.Header.Param, entryResp.Header.Size, entryResp.Header.DataLen, string(entryResp.Data))
		}

		entry := parseDirEntry(entryResp)
		if entry.Name != "" {
			entries = append(entries, entry)
		}

		cursor = entryResp.Header.Param
	}

	return entries, nil
}

// parseDirEntry extracts filename, size, and date from a GET_DIR_ENTRY response.
// The BU returns data as "filename\0date\0" and size in the Size header field.
// Filenames may include the comm line prefix (e.g. "AB01:1041.sys") — we strip it.
func parseDirEntry(resp *Block) DirEntry {
	if len(resp.Data) == 0 {
		return DirEntry{}
	}

	// Data format: "filename\0date\0"
	parts := bytes.SplitN(resp.Data, []byte{0}, 2)
	name := string(parts[0])

	// Strip comm line prefix if present (e.g. "AB01:1041.sys" → "1041.sys")
	// The prefix is everything before the last ":" in the filename
	if idx := strings.LastIndex(name, ":"); idx >= 0 && idx < len(name)-1 {
		// Check if the part before ":" looks like a comm line (alphanumeric, short)
		prefix := name[:idx]
		suffix := name[idx+1:]
		if isCommLinePrefix(prefix) && suffix != "" {
			name = suffix
		}
	}

	// Strip any leading ":s:" prefix
	name = strings.TrimPrefix(name, ":s:")

	var date string
	if len(parts) > 1 {
		dateParts := bytes.SplitN(parts[1], []byte{0}, 2)
		date = string(dateParts[0])
	}

	return DirEntry{
		Name: name,
		Size: resp.Header.Size,
		Date: date,
	}
}

// isCommLinePrefix checks if a string looks like a communication line prefix.
// Comm line names are short alphanumeric strings like "AB01", "EAS-C2023".
func isCommLinePrefix(s string) bool {
	if len(s) == 0 || len(s) > 20 {
		return false
	}
	for _, c := range s {
		if !((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '-') {
			return false
		}
	}
	return true
}

// ListSysFiles lists all .sys files on the remote BU.
// Shortcut for ListDir(commLine, "*.sys").
func (ft *FileTransport) ListSysFiles(commLine string) ([]DirEntry, error) {
	return ft.ListDir(commLine, "*.sys")
}

// ReadFile reads a single file from the remote BU.
// filename is the bare filename (e.g. "161.sys"). The commLine prefix is added.
// Returns the complete file content.
func (ft *FileTransport) ReadFile(commLine, filename string) ([]byte, error) {
	if err := ft.connectAndHandshake(); err != nil {
		return nil, err
	}

	// FILE_OPEN: data = ":s:{commLine}:{filename}\0rb\0"
	openPath := fmt.Sprintf(":s:%s:%s\x00rb\x00", commLine, filename)
	openBlock := &Block{
		Header: BlockHeader{
			Command: CmdFileOpen,
			Source:  0x00EFD61C,
			DataLen: uint32(len(openPath)),
		},
		Data: []byte(openPath),
	}

	debug := os.Getenv("BSTOOL_DEBUG") != ""
	if debug {
		log.Printf("[BSTOOL_DEBUG] FILE_OPEN send: path=%q", openPath)
	}

	if err := ft.tcp.sendBlock(openBlock); err != nil {
		return nil, fmt.Errorf("fileops: FILE_OPEN send: %w", err)
	}

	openResp, err := ft.tcp.recvBlock()
	if err != nil {
		return nil, fmt.Errorf("fileops: FILE_OPEN recv: %w", err)
	}

	if debug {
		log.Printf("[BSTOOL_DEBUG] FILE_OPEN recv: cmd=0x%04x src=0x%08x param=0x%08x",
			openResp.Header.Command, openResp.Header.Source, openResp.Header.Param)
	}

	fileHandle := openResp.Header.Source
	if fileHandle == 0 || fileHandle == 0xFFFFFFFF {
		return nil, fmt.Errorf("fileops: FILE_OPEN failed (handle=0x%08x)", fileHandle)
	}

	// Read file in 448-byte chunks
	var fileData []byte
	for {
		readBlock := &Block{
			Header: BlockHeader{
				Command: CmdFileRead,
				Source:  fileHandle,
				Param:   DefaultChunkSize, // 448
			},
		}

		if err := ft.tcp.sendBlock(readBlock); err != nil {
			return nil, fmt.Errorf("fileops: FILE_READ send: %w", err)
		}

		readResp, err := ft.tcp.recvBlock()
		if err != nil {
			return nil, fmt.Errorf("fileops: FILE_READ recv: %w", err)
		}

		if debug {
			log.Printf("[BSTOOL_DEBUG] FILE_READ recv: dlen=%d data=%d bytes", readResp.Header.DataLen, len(readResp.Data))
		}

		if len(readResp.Data) > 0 {
			fileData = append(fileData, readResp.Data...)
		}

		// If we got less than the chunk size, we're done
		if readResp.Header.DataLen < DefaultChunkSize || len(readResp.Data) == 0 {
			break
		}
	}

	// FILE_CLOSE
	closeBlock := &Block{
		Header: BlockHeader{
			Command: CmdFileClose,
			Source:  fileHandle,
		},
	}
	_ = ft.tcp.sendBlock(closeBlock)
	_, _ = ft.tcp.recvBlock()

	return fileData, nil
}

// RetrieveSysFileData lists all .sys files on the remote BU and reads each one.
// Returns a slice of SysFileData (name + raw content) for each .sys file.
func RetrieveSysFileData(host string, port int, commLine string, timeout time.Duration) ([]SysFileData, error) {
	ft := NewFileTransport(host, port, timeout)
	defer ft.Close()

	debug := os.Getenv("BSTOOL_DEBUG") != ""

	entries, err := ft.ListSysFiles(commLine)
	if err != nil {
		return nil, fmt.Errorf("retrieve sys files: list: %w", err)
	}

	if debug {
		log.Printf("[BSTOOL_DEBUG] ListSysFiles returned %d entries", len(entries))
	}

	var files []SysFileData
	for _, entry := range entries {
		name := strings.ToLower(entry.Name)
		if !strings.HasSuffix(name, ".sys") {
			continue
		}

		data, err := ft.ReadFile(commLine, entry.Name)
		if err != nil {
			if debug {
				log.Printf("[BSTOOL_DEBUG] ReadFile %s failed: %v", entry.Name, err)
			}
			continue
		}

		if debug {
			log.Printf("[BSTOOL_DEBUG] ReadFile %s: %d bytes", entry.Name, len(data))
		}

		files = append(files, SysFileData{
			Name: entry.Name,
			Data: data,
		})
	}

	return files, nil
}

// stripNodeSuffix removes trailing m/r suffix from node names (e.g. "AP01m" → "AP01").
// This is already defined in transport_tcp.go but exported here for reference.
var _ = stripNodeSuffix

// ensure binary import is used (for future use)
var _ = binary.LittleEndian