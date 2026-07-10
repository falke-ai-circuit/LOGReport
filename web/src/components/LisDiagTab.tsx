import { useState, useEffect, useRef, useCallback } from 'react';
import { Terminal, Wifi, WifiOff, Key, Play, CheckCircle, AlertCircle, Loader2, FileText, ChevronRight } from 'lucide-react';
import type { QueueStatusResponse, QueuedCommand } from '../types/api';

interface LisDiagTabProps {
  targetIP: string;
  targetNode: string;
  tokenID: string;
  password: string;
  exeNum: number;
  commands: string[];
  onCommandOutput?: (cmd: string, output: string) => void;
}

type ConnState = 'connecting' | 'connected' | 'authenticated' | 'failed' | 'idle';

export default function LisDiagTab({ targetIP, targetNode, tokenID, password, exeNum, commands }: LisDiagTabProps) {
  const [connState, setConnState] = useState<ConnState>('idle');
  const [matchedCommands, setMatchedCommands] = useState<QueuedCommand[]>([]);
  const [sessionLog, setSessionLog] = useState<string[]>([]);
  const [polling, setPolling] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);
  const seenCommandIds = useRef<Set<string>>(new Set());

  const appendLog = useCallback((line: string) => {
    setSessionLog(prev => {
      if (prev[prev.length - 1] === line) return prev;
      return [...prev, line];
    });
  }, []);

  const fetchQueueStatus = useCallback(async () => {
    setPolling(true);
    try {
      const res = await fetch('/api/v1/commandqueue/status');
      if (!res.ok) return;
      const data: QueueStatusResponse = await res.json();
      const allCmds: QueuedCommand[] = data.commands || [];
      // Filter to lisdiag commands matching our node and token
      const filtered = allCmds.filter(
        (c) => c.type === 'lisdiag' && c.node_name === targetNode && c.token_id === tokenID
      );
      setMatchedCommands(filtered);

      // Detect connection state from command statuses
      const hasRunning = filtered.some(c => c.status === 'running');
      const hasCompleted = filtered.some(c => c.status === 'completed');
      const hasFailed = filtered.some(c => c.status === 'failed' || c.status === 'error');
      const allDone = filtered.length > 0 && filtered.every(c => c.status === 'completed' || c.status === 'failed' || c.status === 'error');

      if (hasFailed) {
        setConnState('failed');
      } else if (allDone && hasCompleted) {
        setConnState('authenticated');
      } else if (hasRunning || hasCompleted) {
        setConnState('connected');
      } else if (filtered.length > 0) {
        setConnState('connecting');
      }

      // Accumulate session log from command results
      for (const cmd of filtered) {
        const cmdKey = cmd.id || `${cmd.command}:${cmd.status}`;
        if (!seenCommandIds.current.has(cmdKey)) {
          if (cmd.status === 'running') {
            appendLog(`[${new Date().toLocaleTimeString()}] >> ${cmd.command}`);
          } else if (cmd.status === 'completed') {
            const output = cmd.output || '';
            appendLog(`[${new Date().toLocaleTimeString()}] << ${cmd.command} — OK`);
            if (output) appendLog(output);
          } else if (cmd.status === 'failed' || cmd.status === 'error') {
            const errMsg = cmd.error || 'Command failed';
            appendLog(`[${new Date().toLocaleTimeString()}] !! ${cmd.command} — FAILED: ${errMsg}`);
          }
          seenCommandIds.current.add(cmdKey);
        }
      }
    } catch {
      // Network error — keep existing state
    } finally {
      setPolling(false);
    }
  }, [targetNode, tokenID, appendLog]);

  useEffect(() => {
    // Initial log lines
    setSessionLog([
      `[${new Date().toLocaleTimeString()}] LisDiag session started — ${targetNode} (${targetIP}:4321)`,
      `[${new Date().toLocaleTimeString()}] Token: ${tokenID}, Exe: ${exeNum}`,
      password
        ? `[${new Date().toLocaleTimeString()}] Password: configured (${password.length} chars)`
        : `[${new Date().toLocaleTimeString()}] Password: none (no auth)`,
      `[${new Date().toLocaleTimeString()}] Commands: ${commands.join(', ')}`,
      '',
    ]);
    // Reset seen commands for new session
    seenCommandIds.current = new Set();
    setConnState('connecting');
    fetchQueueStatus();
    const interval = setInterval(fetchQueueStatus, 2000);
    return () => clearInterval(interval);
  }, [targetIP, targetNode, tokenID, password, exeNum, commands, fetchQueueStatus]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [sessionLog]);

  const connStatusConfig: Record<ConnState, { color: string; icon: React.ReactNode; label: string }> = {
    idle: { color: 'var(--text-muted)', icon: <Terminal size={14} />, label: 'Idle' },
    connecting: { color: '#f59e0b', icon: <Loader2 size={14} className="spin" />, label: 'Connecting...' },
    connected: { color: '#3b82f6', icon: <Wifi size={14} />, label: 'Connected' },
    authenticated: { color: 'var(--accent)', icon: <CheckCircle size={14} />, label: 'Authenticated' },
    failed: { color: '#ef4444', icon: <WifiOff size={14} />, label: 'Failed' },
  };

  const cmdStatusConfig: Record<string, { color: string; icon: React.ReactNode }> = {
    pending: { color: 'var(--text-muted)', icon: <Play size={12} /> },
    running: { color: '#f59e0b', icon: <Loader2 size={12} className="spin" /> },
    completed: { color: 'var(--accent)', icon: <CheckCircle size={12} /> },
    failed: { color: '#ef4444', icon: <AlertCircle size={12} /> },
    error: { color: '#ef4444', icon: <AlertCircle size={12} /> },
  };

  const connInfo = connStatusConfig[connState];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', backgroundColor: 'var(--bg-primary)' }}>
      {/* Header bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '8px 16px',
        borderBottom: '1px solid var(--border)',
        backgroundColor: 'var(--bg-secondary)',
        flexShrink: 0,
      }}>
        <Terminal size={16} color="var(--accent)" />
        <span style={{ fontSize: '13px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
          LisDiag — {targetNode} ({targetIP}:4321)
        </span>
        {/* Connection status badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: '2px 8px',
          borderRadius: '4px',
          fontSize: '11px',
          fontFamily: 'var(--font-mono)',
          color: connInfo.color,
          backgroundColor: `${connInfo.color}15`,
        }}>
          {connInfo.icon}
          {connInfo.label}
        </div>
        {/* Password badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: '2px 8px',
          borderRadius: '4px',
          fontSize: '11px',
          fontFamily: 'var(--font-mono)',
          color: password ? 'var(--accent)' : 'var(--text-muted)',
          backgroundColor: password ? 'rgba(0,138,0,0.1)' : 'transparent',
          border: password ? 'none' : '1px solid var(--border)',
        }}>
          <Key size={12} />
          {password ? 'Auth' : 'No Auth'}
        </div>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: 'auto', fontFamily: 'var(--font-mono)' }}>
          exe{exeNum} · {tokenID}
        </span>
      </div>

      {/* Command timeline */}
      <div style={{
        padding: '8px 16px',
        borderBottom: '1px solid var(--border)',
        backgroundColor: 'var(--bg-secondary)',
        flexShrink: 0,
      }}>
        <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Command Sequence
        </div>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {commands.map((cmd, i) => {
            // Match this command to a queued command
            const matched = matchedCommands.find(c => c.command === cmd);
            const status = matched?.status || 'pending';
            const sc = cmdStatusConfig[status] || cmdStatusConfig.pending;
            return (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                {i > 0 && <ChevronRight size={12} color="var(--text-muted)" />}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '3px 8px',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontFamily: 'var(--font-mono)',
                  color: sc.color,
                  backgroundColor: `${sc.color}10`,
                }}>
                  {sc.icon}
                  {cmd}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Terminal output area */}
      <div style={{
        flex: 1,
        overflow: 'auto',
        backgroundColor: '#0d1117',
        padding: '12px 16px',
        fontFamily: 'var(--font-mono)',
        fontSize: '12px',
        lineHeight: '1.6',
      }}>
        {sessionLog.map((line, i) => {
          const trimmed = line.trim();
          let color = '#c9d1d9';
          if (trimmed.startsWith('[') && trimmed.includes(']')) {
            color = '#8b949e';
          } else if (trimmed.startsWith('>>')) {
            color = '#58a6ff';
          } else if (trimmed.startsWith('<<')) {
            color = '#3fb950';
          } else if (trimmed.startsWith('!!') || trimmed.includes('FAILED') || trimmed.includes('Error') || trimmed.includes('error')) {
            color = '#f85149';
          } else if (trimmed.startsWith('Password:')) {
            color = '#d2a8ff';
          } else if (trimmed.startsWith('LisDiag session') || trimmed.startsWith('Token:') || trimmed.startsWith('Commands:')) {
            color = '#79c0ff';
          }
          return <div key={i} style={{ color, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{line || '\u00A0'}</div>;
        })}
        {polling && (
          <div style={{ color: '#484f58', fontSize: '10px', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Loader2 size={10} className="spin" /> polling queue...
          </div>
        )}
        <div ref={logEndRef} />
      </div>

      {/* Footer info */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '4px 16px',
        borderTop: '1px solid var(--border)',
        backgroundColor: 'var(--bg-secondary)',
        flexShrink: 0,
      }}>
        <FileText size={12} color="var(--text-muted)" />
        <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          {matchedCommands.length} command(s) tracked · auto-refresh 2s
        </span>
      </div>
    </div>
  );
}