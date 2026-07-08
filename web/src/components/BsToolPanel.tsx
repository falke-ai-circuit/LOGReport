import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Terminal,
  Loader2,
  Copy,
  Eraser,
  Play,
} from 'lucide-react';
import type { BsToolWSMessage, BsToolWSResponse } from '../types/api';

export interface BsToolPanelProps {
  pendingServerName?: string | null;
  onServerNameConsumed?: () => void;
  currentNodeName?: string;
  onOutputChange?: (output: string) => void;
  onExecutionComplete?: () => void;
}

export default function BsToolPanel({
  pendingServerName,
  onServerNameConsumed,
  currentNodeName,
  onOutputChange,
  onExecutionComplete,
}: BsToolPanelProps) {
  const [bstoolPath, setBstoolPath] = useState(() => localStorage.getItem('bstoolPath') || '');
  const [commLine, setCommLine] = useState(() => localStorage.getItem('bstoolCommLine') || 'AB01');
  const [serverName, setServerName] = useState(() => localStorage.getItem('bstoolServerName') || '');
  const [output, setOutput] = useState<string[]>([]);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copying, setCopying] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const outputRef = useRef<HTMLPreElement>(null);
  const outputLinesRef = useRef<string[]>([]);

  const appendOutput = useCallback((text: string) => {
    outputLinesRef.current = [...outputLinesRef.current, text];
    setOutput(outputLinesRef.current);
    onOutputChange?.(outputLinesRef.current.join('\n'));
  }, [onOutputChange]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  // ─── Execute via WebSocket ───────────────────────────────────

  async function executeBsTool(srvName: string) {
    if (!srvName) {
      setError('Server name is required');
      return;
    }
    setExecuting(true);
    setError(null);
    appendOutput(`[Executing BsTool errlog for ${srvName}...]`);
    localStorage.setItem('bstoolServerName', srvName);
    localStorage.setItem('bstoolCommLine', commLine);
    if (bstoolPath) localStorage.setItem('bstoolPath', bstoolPath);

    try {
      // Use REST endpoint as fallback if WebSocket not available
      // Try WebSocket first
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/api/v1/bstool/ws`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onmessage = (event) => {
          try {
            const msg: BsToolWSResponse = JSON.parse(event.data);
            if (msg.type === 'output' && msg.data) {
              appendOutput(msg.data);
            } else if (msg.type === 'done') {
              appendOutput(`[Done — exit code: ${msg.exit_code ?? 0}]`);
              setExecuting(false);
              onExecutionComplete?.();
            } else if (msg.type === 'error' && msg.message) {
              setError(msg.message);
              appendOutput(`[ERROR] ${msg.message}`);
              setExecuting(false);
            }
          } catch {
            // ignore
          }
        };

        ws.onerror = () => {
          // Fall back to REST
          executeRest(srvName);
        };

        ws.onopen = () => {
          const msg: BsToolWSMessage = { action: 'execute', server_name: srvName };
          ws.send(JSON.stringify(msg));
        };
      } else {
        const msg: BsToolWSMessage = { action: 'execute', server_name: srvName };
        wsRef.current.send(JSON.stringify(msg));
      }
    } catch {
      // Fall back to REST
      executeRest(srvName);
    }
  }

  async function executeRest(srvName: string) {
    try {
      const res = await fetch('/api/v1/bstool/errlog', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server_name: srvName }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'BsTool failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      const data = await res.json();
      if (data.raw_output) {
        appendOutput(data.raw_output);
      }
      appendOutput(`[Done — exit code: ${data.exit_code ?? 0}]`);
      onExecutionComplete?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'BsTool execution failed');
      appendOutput(`[ERROR] ${err instanceof Error ? err.message : 'BsTool failed'}`);
    } finally {
      setExecuting(false);
    }
  }

  // ─── Pending server name from context menu ──────────────────

  useEffect(() => {
    if (pendingServerName) {
      setServerName(pendingServerName);
      executeBsTool(pendingServerName);
      onServerNameConsumed?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingServerName]);

  // ─── Auto-scroll ─────────────────────────────────────────────

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  // ─── Copy to log ─────────────────────────────────────────────

  async function handleCopyToLog() {
    if (!currentNodeName) {
      setError('No node selected');
      return;
    }
    setCopying(true);
    try {
      const outputText = outputLinesRef.current.join('\n');
      const res = await fetch(`/api/v1/logs/${encodeURIComponent(currentNodeName)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token_type: 'BSTOOL',
          token_id: 'errlog',
          output: outputText,
        }),
      });
      if (!res.ok) throw new Error('Write failed');
      appendOutput('[Log saved]');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save log');
    } finally {
      setCopying(false);
    }
  }

  function handleClear() {
    outputLinesRef.current = [];
    setOutput([]);
    onOutputChange?.('');
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      {/* Top bar */}
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
        <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>BsTool Path:</label>
        <input
          type="text"
          placeholder="/path/to/BsTool.exe"
          value={bstoolPath}
          onChange={(e) => setBstoolPath(e.target.value)}
          style={{
            width: '180px',
            padding: '4px 8px',
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border)',
            borderRadius: '4px',
            color: 'var(--text-primary)',
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            outline: 'none',
          }}
        />
        <label style={{ fontSize: '11px', color: 'var(--text-secondary)', marginLeft: '8px' }}>
          COMMUNICATION_LINE:
        </label>
        <input
          type="text"
          value={commLine}
          onChange={(e) => setCommLine(e.target.value)}
          style={{
            width: '80px',
            padding: '4px 8px',
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border)',
            borderRadius: '4px',
            color: 'var(--text-primary)',
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            outline: 'none',
          }}
        />
      </div>

      {/* Server name input */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 12px',
          borderBottom: '1px solid var(--border)',
        }}
      >
        <input
          type="text"
          placeholder="Server name (e.g. AP01)"
          value={serverName}
          onChange={(e) => setServerName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') executeBsTool(serverName);
          }}
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
          style={{ fontSize: '12px', padding: '4px 12px' }}
          onClick={() => executeBsTool(serverName)}
          disabled={executing || !serverName.trim()}
        >
          {executing ? (
            <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />
          ) : (
            <Play size={12} />
          )}
          Execute
        </button>
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

      {/* Output */}
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
        {output.length === 0 ? 'BsTool output will appear here...\n' : output.join('\n')}
      </pre>

      {/* Action bar */}
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
          onClick={handleClear}
          title="Clear Terminal"
        >
          <Eraser size={14} />
        </button>
      </div>
    </div>
  );
}