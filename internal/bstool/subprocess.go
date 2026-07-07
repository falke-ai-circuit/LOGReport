package bstool

// subprocess.go — BsTool.exe subprocess wrapper for file operations.
//
// Runs BsTool.exe -ls and -cat as subprocesses to list and retrieve .sys files
// from a remote BU. This is a fallback for BUs where the native Go TCP protocol
// doesn't work (e.g. some BU firmware versions that require zzInitTcpLineIO
// reconnection logic that's hard to replicate).
//
// The subprocess approach uses the same BsTool.exe binary that BsGUI uses,
// guaranteeing compatibility with any BU that BsTool.exe supports.

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"regexp"
	"strings"
	"time"
)

// SubprocessRetrieveSysFiles runs BsTool.exe -ls to list .sys files,
// then BsTool.exe -cat to retrieve each file's content.
// Returns a slice of SysFileData (name + raw content) for each .sys file.
func SubprocessRetrieveSysFiles(bstoolPath, commLine string) ([]SysFileData, error) {
	// Step 1: List .sys files
	entries, err := subprocessListDir(bstoolPath, commLine, "*.sys")
	if err != nil {
		return nil, fmt.Errorf("subprocess list: %w", err)
	}
	if len(entries) == 0 {
		return nil, fmt.Errorf("no .sys files found via BsTool.exe -ls")
	}

	// Step 2: Retrieve each file
	var files []SysFileData
	for _, entry := range entries {
		data, err := subprocessCatFile(bstoolPath, commLine, entry.Name)
		if err != nil {
			continue // skip failed files
		}
		if len(data) > 0 {
			files = append(files, SysFileData{
				Name: entry.Name,
				Data: data,
			})
		}
	}

	if len(files) == 0 {
		return nil, fmt.Errorf("BsTool.exe listed %d .sys files but could not retrieve any", len(entries))
	}

	return files, nil
}

// subprocessListDir runs BsTool.exe -ls to list files matching a pattern.
func subprocessListDir(bstoolPath, commLine, pattern string) ([]DirEntry, error) {
	dirPath := fmt.Sprintf(":s:%s:%s", commLine, pattern)

	cmd := exec.Command(bstoolPath, "-ls", dirPath)
	// Inherit parent environment and add COMMUNICATION_LINE
	cmd.Env = append(os.Environ(), "COMMUNICATION_LINE="+commLine)
	// Set working directory to BsTool.exe's directory — it may need
	// to find DLLs or config files relative to its own location
	if idx := strings.LastIndexByte(bstoolPath, '\\'); idx >= 0 {
		cmd.Dir = bstoolPath[:idx]
	}

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("BsTool.exe -ls failed: %w (stderr: %s)", err, stderr.String())
	}

	return parseListOutput(stdout.String()), nil
}

// subprocessCatFile runs BsTool.exe -cat to retrieve file content.
func subprocessCatFile(bstoolPath, commLine, filename string) ([]byte, error) {
	filePath := fmt.Sprintf(":s:%s:%s", commLine, filename)

	cmd := exec.Command(bstoolPath, "-cat", filePath)
	cmd.Env = append(os.Environ(), "COMMUNICATION_LINE="+commLine)
	if idx := strings.LastIndexByte(bstoolPath, '\\'); idx >= 0 {
		cmd.Dir = bstoolPath[:idx]
	}

	var stdout bytes.Buffer
	cmd.Stdout = &stdout

	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("BsTool.exe -cat %s failed: %w", filename, err)
	}

	return stdout.Bytes(), nil
}

// parseListOutput parses the output of BsTool.exe -ls.
// Format: ":s:AB01:161.sys  : Jun 13 22:37:05 2024      9009 bytes"
var listLineRegex = regexp.MustCompile(`^:s:\S+:(\S+)\s*:\s*(.+?)\s+(\d+)\s*bytes\s*$`)

func parseListOutput(output string) []DirEntry {
	var entries []DirEntry
	for _, line := range strings.Split(output, "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.Contains(line, "### TOTAL ###") {
			continue
		}
		matches := listLineRegex.FindStringSubmatch(line)
		if len(matches) == 4 {
			entries = append(entries, DirEntry{
				Name: matches[1],
				Date: matches[2],
				Size: parseUint32(matches[3]),
			})
		}
	}
	return entries
}

func parseUint32(s string) uint32 {
	var n uint32
	fmt.Sscanf(s, "%d", &n)
	return n
}

// subprocessTimeout is the default timeout for BsTool.exe subprocess calls.
const subprocessTimeout = 30 * time.Second