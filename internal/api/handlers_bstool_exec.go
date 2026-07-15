package api

import (
	"context"
	"log"

	"github.com/falke-ai-circuit/LOGReport/internal/bstool"
)

// executeBsToolErrLog is the shared BsTool errlog execution logic used by
// the REST handler, WebSocket handler, and queue executor. It reads settings
// to determine whether to use BsTool.exe subprocess or native TCP.
//
// Priority:
// 1. If bstool_path is set and exists (local_exe mode) → BsTool.exe subprocess
// 2. If subprocess fails or no exe → TCP transport using bstool_host:bstool_port
// 3. If no TCP host → default bstoolClient (subprocess from PATH or error on Linux)
func (s *Server) executeBsToolErrLog(ctx context.Context, serverName string, _ string) (*bstool.ErrLogResult, error) {
	if !globalSettings.loaded {
		s.initSettings()
	}
	st := getSettings()

	// If there's an active project, use project-specific settings
	if s.activeProjectID > 0 {
		st = s.getSettingsForProject(s.activeProjectID)
	}

	// Try BsTool.exe subprocess first if configured
	if isLocalExeMode(st) {
		exePath := resolveBsToolPath(st)
		if exePath != "" {
			subprocessClient := bstool.NewClient(
				bstool.WithPath(exePath),
				bstool.WithCommunicationLine(st.CommunicationLine),
			)
			result, err := subprocessClient.ErrLog(ctx, serverName)
			if err == nil {
				return result, nil
			}
			log.Printf("bstool: subprocess failed, falling back to TCP: %v", err)
		}
	}

	// Fall back to TCP
	if st.BsToolHost != "" {
		tcpOpts := []bstool.TCPTransportOption{
			bstool.WithTCPHost(st.BsToolHost),
		}
		if st.BsToolPort > 0 {
			tcpOpts = append(tcpOpts, bstool.WithTCPPort(st.BsToolPort))
		}
		tcp := bstool.NewTCPTransport(tcpOpts...)
		defer tcp.Close()
		tcpClient := bstool.NewClient(bstool.WithTCPTransport(tcp))
		return tcpClient.ErrLog(ctx, serverName)
	}

	// Default: use the client created at startup
	return s.bstoolClient.ErrLog(ctx, serverName)
}