import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Terminal,
  Loader2,
  Copy,
  Trash2,
  Eraser,
} from 'lucide-react';
import type { TelnetWSMessage, TelnetWSResponse } from '../types/api';

export interface TelnetTerminalProps {
  currentToken?: string;
  currentTokenType?: string;
  currentNodeName?: string;
  pendingCommand?: string | null;
  onCommandSent?: () => void;
  onOutputChange?: (output: string) => void;
}

// Client-side command resolver (matching telnet_commands.py)
function resolveCommand(cmd: string, currentToken?: string): string {
  const resolver: Record<string, (token: string) => string> = {
    ps: () => 'show all',
    fis: (t) => `print_fieldbus ${t}0000`,
    rc: (t) => `print_fieldbus_rupi_counters ${t}0000`,
  };
  const parts = cmd.trim().toLowerCase().split(/\s+/);
  if (resolver[parts[0]]) {
    return resolver[parts[0]](currentToken || parts[1] || '');
  }
  return cmd;
}

export default function TelnetTerminal({
  currentToken,
  currentTokenType,
  currentNodeName,
  pendingCommand,
  onCommandSent,
  onOutputChange,
}: TelnetTerminalProps) {
  const [host, setHost] = useState(() => localStorage.getItem('telnetHost') || '');
  const [port, setPort] = useState(() => {
    const stored = localStorage.getItem('telnetPort');
    return stored ? parseInt(stored, 10) : 1234;
  });
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [output, setOutput] = useState<string[]>([]);
  const [cmdInput, setCmdInput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<string[]>([]);
  const [historyIdx, setHistoryIdx] = useState(-1);
  const [copying, setCopying] = useState(false);
  const [clearing, setClearing] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const outputRef = useRef<HTMLPreElement>(null);
  const outputLinesRef = useRef<string[]>([]);

  // ─── Output helpers ──────────────────────────────────────────

  const appendOutput = useCallback((text: string) => {
    outputLinesRef.current = [...outputLinesRef.current, text];
    setOutput(outputLinesRef.current);
    onOutputChange?.(outputLinesRef.current.join('\n'));
  }, [onOutputChange]);

  // ─── WebSocket ───────────────────────────────────────────────

  const connectWS = useCallback(() => {
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/api/v1/telnet/ws`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const msg: TelnetWSResponse = JSON.parse(event.data);
        if (msg.type === 'output' && msg.data) {
          appendOutput(msg.data);
        } else if (msg.type === 'status') {
          setConnected(msg.connected ?? false);
          if (msg.connected && msg.session_id) {
            appendOutput(`[Connected — session ${msg.session_id}]`);
          } else if (!msg.connected) {
            appendOutput('[Disconnected]');
          }
        } else if (msg.type === 'error' && msg.message) {
          setError(msg.message);
          appendOutput(`[ERROR] ${msg.message}`);
        } else if (msg.type === 'prompt' && msg.data) {
          // Prompt detected — command complete
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onerror = () => {
      setError('WebSocket error');
      setConnecting(false);
    };

    ws.onclose = () => {
      setConnected(false);
      setConnecting(false);
    };

    return ws;
  }, [appendOutput]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  // ─── Connect / Disconnect ────────────────────────────────────

  async function handleConnect() {
    if (!host) {
      setError('Host is required');
      return;
    }
    setConnecting(true);
    setError(null);
    appendOutput(`[Connecting to ${host}:${port}...]`);
    localStorage.setItem('telnetHost', host);
    localStorage.setItem('telnetPort', String(port));

    try {
      // Ensure WebSocket is open
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        const ws = connectWS();
        await new Promise<void>((resolve, reject) => {
          const timeout = setTimeout(() => reject(new Error('WebSocket timeout')), 5000);
          ws.onopen = () => {
            clearTimeout(timeout);
            resolve();
          };
          ws.onerror = () => {
            clearTimeout(timeout);
            reject(new Error('WebSocket connection failed'));
          };
        });
      }

      const msg: TelnetWSMessage = { action: 'connect', host, port };
      wsRef.current?.send(JSON.stringify(msg));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
      appendOutput(`[ERROR] ${err instanceof Error ? err.message : 'Connection failed'}`);
    } finally {
      setConnecting(false);
    }
  }

  function handleDisconnect() {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const msg: TelnetWSMessage = { action: 'disconnect' };
      wsRef.current.send(JSON.stringify(msg));
    }
    setConnected(false);
  }

  // ─── Send command ────────────────────────────────────────────

  function sendCommand(rawCmd: string) {
    const cmd = rawCmd.trim();
    if (!cmd) return;
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('Not connected to WebSocket');
      return;
    }
    if (!connected) {
      setError('Not connected to telnet host');
      return;
    }

    const resolved = resolveCommand(cmd, currentToken);
    appendOutput(`> ${cmd}${resolved !== cmd ? ` → ${resolved}` : ''}`);

    const msg: TelnetWSMessage = { action: 'command', command: resolved };
    wsRef.current.send(JSON.stringify(msg));

    // Add to history
    setHistory((prev) => [...prev, cmd]);
    setHistoryIdx(-1);
    setCmdInput('');
    onCommandSent?.();
  }

  // ─── Pending command from context menu ──────────────────────

  useEffect(() => {
    if (pendingCommand && connected) {
      sendCommand(pendingCommand);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingCommand, connected]);

  // ─── Auto-scroll ─────────────────────────────────────────────

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  // ─── History navigation ──────────────────────────────────────

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (history.length === 0) return;
      const newIdx = historyIdx === -1 ? history.length - 1 : Math.max(0, historyIdx - 1);
      setHistoryIdx(newIdx);
      setCmdInput(history[newIdx]);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIdx === -1) return;
      const newIdx = historyIdx + 1;
      if (newIdx >= history.length) {
        setHistoryIdx(-1);
        setCmdInput('');
      } else {
        setHistoryIdx(newIdx);
        setCmdInput(history[newIdx]);
      }
    } else if (e.key === 'Enter') {
      e.preventDefault();
      sendCommand(cmdInput);
    }
  }

  // ─── Copy to log ─────────────────────────────────────────────

  async function handleCopyToLog() {
    if (!currentNodeName || !currentToken) {
      setError('No node/token selected');
      return;
    }
    setCopying(true);
    setError(null);
    try {
      const outputText = outputLinesRef.current.join('\n');
      const res = await fetch(`/api/v1/logs/${encodeURIComponent(currentNodeName)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token_type: currentTokenType || 'FBC',
          token_id: currentToken,
          output: outputText,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Write failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      appendOutput('[Log saved]');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save log');
    } finally {
      setCopying(false);
    }
  }

  // ─── Clear terminal ──────────────────────────────────────────

  function handleClearTerminal() {
    outputLinesRef.current = [];
    setOutput([]);
    onOutputChange?.('');
  }

  // ─── Clear log ───────────────────────────────────────────────

  async function handleClearLog() {
    if (!currentNodeName || !currentToken) {
      setError('No node/token selected');
      return;
    }
    setClearing(true);
    try {
      // Write empty content to overwrite log
      await fetch(`/api/v1/logs/${encodeURIComponent(currentNodeName)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token_type: currentTokenType || 'FBC',
          token_id: currentToken,
          output: '',
        }),
      });
      appendOutput('[Log cleared]');
    } catch {
      setError('Failed to clear log');
    } finally {
      setClearing(false);
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      {/* Connection bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 12px',
          borderBottom: '1px solid var(--border)',
          flexWrap: 'wrap',
        }}
      >
        <Terminal size={16} color="var(--accent)" />
        <input
          type="text"
          placeholder="IP address"
          value={host}
          onChange={(e) => setHost(e.target.value)}
          disabled={connected}
          style={{
            width: '140px',
            padding: '4px 8px',
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border)',
            borderRadius: '4px',
            color: 'var(--text-primary)',
            fontSize: '12px',
            fontFamily: 'var(--font-mono)',
            outline: 'none',
          }}
        />
        <input
          type="number"
          placeholder="Port"
          value={port}
          onChange={(e) => setPort(Number(e.target.value) || 1234)}
          disabled={connected}
          style={{
            width: '70px',
            padding: '4px 8px',
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border)',
            borderRadius: '4px',
            color: 'var(--text-primary)',
            fontSize: '12px',
            fontFamily: 'var(--font-mono)',
            outline: 'none',
          }}
        />
        {connected ? (
          <button className="btn btn-secondary" style={{ fontSize: '12px', padding: '4px 12px' }} onClick={handleDisconnect}>
            Disconnect
          </button>
        ) : (
          <button
            className="btn btn-primary"
            style={{ fontSize: '12px', padding: '4px 12px' }}
            onClick={handleConnect}
            disabled={connecting}
          >
            {connecting ? (
              <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />
            ) : (
              'Connect'
            )}
          </button>
        )}
        {/* Status indicator */}
        <span
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: connected ? 'var(--success)' : 'var(--text-muted)',
            flexShrink: 0,
          }}
        />
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          {connected ? 'Connected' : 'Disconnected'}
        </span>

        {/* Token display */}
        {currentToken && (
          <span
            style={{
              fontSize: '11px',
              color: 'var(--accent)',
              fontFamily: 'var(--font-mono)',
              marginLeft: 'auto',
            }}
          >
            Token: {currentToken}
          </span>
        )}
      </div>

      {/* Error */}
      {error && (
        <div
          style={{
            padding: '6px 12px',
            fontSize: '11px',
            color: 'var(--error)',
            backgroundColor: 'rgba(239,68,68,0.1)',
          }}
        >
          {error}
        </div>
      )}

      {/* Terminal output */}
      <pre
        ref={outputRef}
        style={{
          flex: 1,
          overflow: 'auto',
          margin: 0,
          padding: '12px',
          backgroundColor: 'var(--bg-primary)',
          color: 'var(--text-primary)',
          fontFamily: 'Courier New, monospace',
          fontSize: '12px',
          lineHeight: '1.5',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {output.length === 0
          ? 'Terminal output will appear here...\n'
          : output.join('\n')}
      </pre>

      {/* Command input */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '8px 12px',
          borderTop: '1px solid var(--border)',
          backgroundColor: 'var(--bg-secondary)',
        }}
      >
        <span style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)', fontSize: '13px' }}>
          {connected ? '>' : '○'}
        </span>
        <input
          type="text"
          placeholder="Enter command (ps, fis, rc, or raw command)..."
          value={cmdInput}
          onChange={(e) => setCmdInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={!connected}
          style={{
            flex: 1,
            padding: '6px 8px',
            backgroundColor: 'var(--bg-primary)',
            border: '1px solid var(--border)',
            borderRadius: '4px',
            color: 'var(--text-primary)',
            fontSize: '12px',
            fontFamily: 'var(--font-mono)',
            outline: 'none',
          }}
        />
        <button
          className="btn btn-primary"
          style={{ fontSize: '11px', padding: '4px 10px' }}
          onClick={() => sendCommand(cmdInput)}
          disabled={!connected || !cmdInput.trim()}
        >
          Send
        </button>

        {/* Action buttons */}
        <button
          className="btn btn-ghost"
          style={{ padding: '4px' }}
          onClick={handleCopyToLog}
          disabled={copying || !currentNodeName}
          title="Copy to Log"
        >
          {copying ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Copy size={14} />}
        </button>
        <button
          className="btn btn-ghost"
          style={{ padding: '4px' }}
          onClick={handleClearTerminal}
          title="Clear Terminal"
        >
          <Eraser size={14} />
        </button>
        <button
          className="btn btn-ghost"
          style={{ padding: '4px' }}
          onClick={handleClearLog}
          disabled={clearing || !currentNodeName}
          title="Clear Log"
        >
          <Trash2 size={14} />
        </button>
      </div>
    </div>
  );
}