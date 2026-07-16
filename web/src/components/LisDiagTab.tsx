import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Terminal,
  Wifi,
  WifiOff,
  Key,
  CheckCircle,
  Loader2,
  Send,
} from 'lucide-react';
import type { QueueStatusResponse, QueuedCommand } from '../types/api';

interface LisDiagTabProps {
  targetIP: string;
  targetNode: string;
  tokenID: string;
  password: string;
  exeNum: number;
  commands: string[];
}

type ConnState = 'idle' | 'connecting' | 'connected' | 'authenticated' | 'failed';

export default function LisDiagTab({
  targetIP,
  targetNode,
  tokenID,
  password,
  exeNum,
  commands,
}: LisDiagTabProps) {
  // ─── State ──────────────────────────────────────────────────────
  const [ipAddress, setIpAddress] = useState(targetIP || '127.0.0.1');
  const [port, setPort] = useState(4321);
  const [pwdInput, setPwdInput] = useState(password);
  const [connState, setConnState] = useState<ConnState>('idle');
  const [sessionLog, setSessionLog] = useState<string[]>([]);
  const [cmdInput, setCmdInput] = useState('');
  const [polling, setPolling] = useState(false);
  const [sending, setSending] = useState(false);

  // Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const seenCommandIds = useRef<Set<string>>(new Set());
  const seenStatuses = useRef<Map<string, string>>(new Map());

  // ─── Helpers ────────────────────────────────────────────────────

  const timestamp = () => new Date().toLocaleTimeString();

  const appendLog = useCallback((line: string) => {
    setSessionLog((prev) => {
      if (prev[prev.length - 1] === line) return prev;
      return [...prev, line];
    });
  }, []);

  // ─── Queue polling ──────────────────────────────────────────────

  const fetchQueueStatus = useCallback(async () => {
    setPolling(true);
    try {
      const res = await fetch('/api/v1/commandqueue/status');
      if (!res.ok) return;
      const data: QueueStatusResponse = await res.json();
      const allCmds: QueuedCommand[] = data.commands || [];
      const filtered = allCmds.filter(
        (c) => c.type === 'lisdiag' && c.node_name === targetNode && c.token_id === tokenID
      );

      // Detect transitions and update log
      for (const cmd of filtered) {
        const cmdKey = cmd.id || `${cmd.command}:${cmd.status}`;
        const prevStatus = seenStatuses.current.get(cmdKey);

        if (cmd.status === 'running' && prevStatus !== 'running') {
          appendLog(`[${timestamp()}] >> ${cmd.command}`);
        } else if (cmd.status === 'completed' && prevStatus !== 'completed') {
          const output = cmd.output || '';
          appendLog(`[${timestamp()}] << ${cmd.command} — OK`);
          if (output) {
            output.split('\n').forEach((line) => {
              if (line.trim()) appendLog(line);
            });
          }
        } else if ((cmd.status === 'failed' || cmd.status === 'error') && prevStatus !== 'failed' && prevStatus !== 'error') {
          const errMsg = cmd.error || 'Command failed';
          appendLog(`[${timestamp()}] !! ${cmd.command} — FAILED: ${errMsg}`);
        }

        seenStatuses.current.set(cmdKey, cmd.status);
        seenCommandIds.current.add(cmdKey);
      }

      // Update connection state from command statuses
      const hasRunning = filtered.some((c) => c.status === 'running');
      const hasCompleted = filtered.some((c) => c.status === 'completed');
      const hasFailed = filtered.some((c) => c.status === 'failed' || c.status === 'error');
      const allDone =
        filtered.length > 0 &&
        filtered.every((c) => c.status === 'completed' || c.status === 'failed' || c.status === 'error');

      if (hasFailed) {
        setConnState('failed');
      } else if (allDone && hasCompleted) {
        setConnState('authenticated');
      } else if (hasRunning || hasCompleted) {
        setConnState('connected');
      } else if (filtered.length > 0) {
        setConnState('connecting');
      }
    } catch {
      // Network error — keep existing state
    } finally {
      setPolling(false);
    }
  }, [targetNode, tokenID, appendLog]);

  // ─── Initial session setup ─────────────────────────────────────

  useEffect(() => {
    if (commands.length > 0) {
      setSessionLog([
        `[${timestamp()}] LisDiag session — ${targetNode} (${targetIP}:4321)`,
        `[${timestamp()}] Token: ${tokenID}, Exe: ${exeNum}`,
        `[${timestamp()}] Password: ${password ? 'configured' : 'none (no auth)'}`,
        `[${timestamp()}] Commands: ${commands.join(', ')}`,
        '',
      ]);
      seenCommandIds.current = new Set();
      seenStatuses.current = new Map();
      setConnState('connecting');
      fetchQueueStatus();
      const interval = setInterval(fetchQueueStatus, 2000);
      return () => clearInterval(interval);
    } else {
      // No target — show ready state, don't auto-poll
      setSessionLog([
        `[${timestamp()}] LisDiag terminal ready`,
        `[${timestamp()}] Enter IP and port, then click Connect to start a session.`,
        '',
      ]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetIP, targetNode, tokenID, password, exeNum, commands]);

  // ─── Auto-scroll (FIXED: scrollTop instead of scrollIntoView) ──

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [sessionLog]);

  // ─── Connect button handler (visual only) ──────────────────────

  async function handleConnect() {
    if (connState === 'connected' || connState === 'authenticated') {
      setConnState('idle');
      appendLog(`[${timestamp()}] Disconnected`);
      return;
    }
    setConnState('connecting');
    appendLog(`[${timestamp()}] Connecting to ${ipAddress}:${port}...`);
    try {
      // Check if there are already pending lisdiag commands in the queue
      // (from right-click → Run LisDiag). If so, just start the queue.
      const statusRes = await fetch('/api/v1/commandqueue/status');
      if (statusRes.ok) {
        const statusData: QueueStatusResponse = await statusRes.json();
        const hasPendingLisdiag = (statusData.commands || []).some(
          (c) => c.type === 'lisdiag' && c.status === 'pending'
        );
        if (hasPendingLisdiag) {
          // Commands already queued — start the queue to execute them
          await fetch('/api/v1/commandqueue/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: '{}',
          });
          setConnState('connected');
          appendLog(`[${timestamp()}] Connected to ${ipAddress}:${port} — executing queued commands`);
          return;
        }
      }
      // No pending commands — add a test command to verify connection
      const res = await fetch('/api/v1/commandqueue/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'lisdiag',
          node_name: targetNode || 'manual',
          token_id: tokenID || 'manual',
          command: '\n',  // empty command just to test connection
          ip_address: ipAddress,
          lisdiag_pwd: pwdInput || undefined,
        }),
      });
      if (res.ok) {
        setConnState('connected');
        appendLog(`[${timestamp()}] Connected to ${ipAddress}:${port}`);
        // Start the queue to process the test command
        fetch('/api/v1/commandqueue/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: '{}',
        }).catch(() => {});
      } else {
        setConnState('failed');
        appendLog(`[${timestamp()}] !! Connection failed: HTTP ${res.status}`);
      }
    } catch (err) {
      setConnState('failed');
      appendLog(`[${timestamp()}] !! Connection error: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  // ─── Send command ───────────────────────────────────────────────

  async function handleSendCommand() {
    const cmd = cmdInput.trim();
    if (!cmd) return;

    appendLog(`[${timestamp()}] >> ${cmd}`);
    setCmdInput('');
    setSending(true);

    try {
      await fetch('/api/v1/commandqueue/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'lisdiag',
          node_name: targetNode,
          token_id: tokenID,
          command: cmd,
          ip_address: ipAddress,
          lisdiag_pwd: pwdInput || undefined,
        }),
      });
      // Auto-start the queue
      fetch('/api/v1/commandqueue/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}',
      }).catch(() => {});
    } catch (err) {
      appendLog(`[${timestamp()}] !! ${cmd} — FAILED: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setSending(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSendCommand();
    }
  }

  // ─── Connection status config ───────────────────────────────────

  const connStatusConfig: Record<ConnState, { color: string; icon: React.ReactNode; label: string }> = {
    idle: { color: 'var(--text-muted)', icon: <Terminal size={14} />, label: 'Disconnected' },
    connecting: { color: '#f59e0b', icon: <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />, label: 'Connecting...' },
    connected: { color: '#3b82f6', icon: <Wifi size={14} />, label: 'Connected' },
    authenticated: { color: 'var(--accent)', icon: <CheckCircle size={14} />, label: 'Authenticated' },
    failed: { color: '#ef4444', icon: <WifiOff size={14} />, label: 'Failed' },
  };

  const connInfo = connStatusConfig[connState];

  // ─── Line color helper ──────────────────────────────────────────

  function getLineColor(line: string): string {
    const trimmed = line.trim();
    if (trimmed.startsWith('>>')) return '#58a6ff'; // sent commands — blue
    if (trimmed.startsWith('<<')) return '#3fb950'; // OK — green
    if (trimmed.startsWith('!!') || trimmed.includes('FAILED') || trimmed.includes('Error')) return '#f85149'; // errors — red
    if (trimmed.startsWith('[') && trimmed.includes(']')) return '#8b949e'; // timestamps/info — gray
    if (trimmed.startsWith('LisDiag session') || trimmed.startsWith('Token:') || trimmed.startsWith('Password:') || trimmed.startsWith('Commands:') || trimmed.startsWith('Connecting')) return '#79c0ff'; // session info — light blue
    return '#c9d1d9'; // default output
  }

  // ─── Render ─────────────────────────────────────────────────────

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', backgroundColor: 'var(--bg-primary)' }}>
      {/* Connection bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 12px',
          borderBottom: '1px solid var(--border)',
          backgroundColor: 'var(--bg-secondary)',
          flexWrap: 'wrap',
          flexShrink: 0,
        }}
      >
        <Terminal size={16} color="var(--accent)" />

        {/* IP address input */}
        <input
          type="text"
          placeholder="IP address"
          value={ipAddress}
          onChange={(e) => setIpAddress(e.target.value)}
          disabled={connState === 'connected' || connState === 'authenticated'}
          style={{
            width: '140px',
            padding: '4px 8px',
            backgroundColor: 'var(--bg-primary)',
            border: '1px solid var(--border)',
            borderRadius: '4px',
            color: 'var(--text-primary)',
            fontSize: '12px',
            fontFamily: 'var(--font-mono)',
            outline: 'none',
          }}
        />

        {/* Port input */}
        <input
          type="number"
          placeholder="Port"
          value={port}
          onChange={(e) => setPort(Number(e.target.value) || 4321)}
          disabled={connState === 'connected' || connState === 'authenticated'}
          style={{
            width: '70px',
            padding: '4px 8px',
            backgroundColor: 'var(--bg-primary)',
            border: '1px solid var(--border)',
            borderRadius: '4px',
            color: 'var(--text-primary)',
            fontSize: '12px',
            fontFamily: 'var(--font-mono)',
            outline: 'none',
          }}
        />

        {/* Connect button */}
        <button
          className="btn btn-primary"
          style={{ fontSize: '12px', padding: '4px 12px' }}
          onClick={handleConnect}
          disabled={connState === 'connecting'}
        >
          {connState === 'connecting' ? (
            <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />
          ) : connState === 'connected' || connState === 'authenticated' ? (
            'Disconnect'
          ) : (
            'Connect'
          )}
        </button>

        {/* Connection status indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '2px 8px',
            borderRadius: '4px',
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            color: connInfo.color,
            backgroundColor: `${connInfo.color}15`,
          }}
        >
          {connInfo.icon}
          {connInfo.label}
        </div>

        {/* Password input */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Key size={14} color="var(--text-muted)" />
          <input
            type="password"
            placeholder="No Auth"
            value={pwdInput}
            onChange={(e) => setPwdInput(e.target.value)}
            disabled={connState === 'connected' || connState === 'authenticated'}
            style={{
              width: '100px',
              padding: '4px 8px',
              backgroundColor: 'var(--bg-primary)',
              border: '1px solid var(--border)',
              borderRadius: '4px',
              color: 'var(--text-primary)',
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
              outline: 'none',
            }}
          />
        </div>

        {/* Token/node info */}
        <span
          style={{
            fontSize: '11px',
            color: 'var(--text-muted)',
            marginLeft: 'auto',
            fontFamily: 'var(--font-mono)',
          }}
        >
          {targetNode} · exe{exeNum} · {tokenID}
        </span>
      </div>

      {/* Terminal output area */}
      <div
        ref={containerRef}
        style={{
          flex: 1,
          overflow: 'auto',
          backgroundColor: '#0d1117',
          padding: '12px 16px',
          fontFamily: 'var(--font-mono)',
          fontSize: '12px',
          lineHeight: '1.6',
        }}
      >
        {sessionLog.map((line, i) => (
          <div
            key={i}
            style={{
              color: getLineColor(line),
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {line || '\u00A0'}
          </div>
        ))}
        {polling && (
          <div
            style={{
              color: '#484f58',
              fontSize: '10px',
              marginTop: '4px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            <Loader2 size={10} style={{ animation: 'spin 1s linear infinite' }} /> polling queue...
          </div>
        )}
      </div>

      {/* Command input bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '8px 12px',
          borderTop: '1px solid var(--border)',
          backgroundColor: 'var(--bg-secondary)',
          flexShrink: 0,
        }}
      >
        <span style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)', fontSize: '13px' }}>
          {'>'}
        </span>
        <input
          type="text"
          placeholder="Enter LisDiag command (exe N, io N, q)..."
          value={cmdInput}
          onChange={(e) => setCmdInput(e.target.value)}
          onKeyDown={handleKeyDown}
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
          style={{ fontSize: '11px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '4px' }}
          onClick={handleSendCommand}
          disabled={!cmdInput.trim() || sending}
        >
          {sending ? (
            <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />
          ) : (
            <Send size={12} />
          )}
          Send
        </button>
      </div>
    </div>
  );
}