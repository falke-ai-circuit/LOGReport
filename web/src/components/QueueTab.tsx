import { useState, useEffect, useCallback, useRef } from 'react';
import { Play, Pause, Square, Trash2, ArrowUp, ArrowDown, Plus, X, Loader2, CheckCircle, AlertCircle, Circle, ListChecks, RotateCcw } from 'lucide-react';
import type { QueueStatusResponse } from '../types/api';

interface QueueTabProps {
  onQueueChange?: (status: QueueStatusResponse | null) => void;
}

const stateColors: Record<string, string> = {
  idle: '#6b7280',
  running: '#008a00',
  paused: '#f59e0b',
  done: '#6b7280',
};

const statusIcons: Record<string, React.ReactNode> = {
  pending: <Circle size={12} color="#6b7280" />,
  running: <Loader2 size={12} color="#008a00" className="spin" />,
  completed: <CheckCircle size={12} color="#10b981" />,
  failed: <AlertCircle size={12} color="#ef4444" />,
  cancelled: <X size={12} color="#6b7280" />,
};

const typeColors: Record<string, string> = {
  fbc: '#3b82f6',
  rpc: '#8b5cf6',
  log: '#f59e0b',
  lis: '#ec4899',
  lisdiag: '#ec4899',
  bstool: '#06b6d4',
  raw: '#6b7280',
};

const typeLabels: Record<string, string> = {
  fbc: 'FBC',
  rpc: 'RPC',
  log: 'LOG',
  lis: 'LIS',
  lisdiag: 'LISDiag',
  bstool: 'BsTool',
  raw: 'RAW',
};

export default function QueueTab({ onQueueChange }: QueueTabProps) {
  const [status, setStatus] = useState<QueueStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [addType, setAddType] = useState('raw');
  const [addNode, setAddNode] = useState('');
  const [addToken, setAddToken] = useState('');
  const [addCommand, setAddCommand] = useState('');
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; cmdId: string; cmdStatus: string } | null>(null);
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/commandqueue/status');
      if (res.ok) {
        const data: QueueStatusResponse = await res.json();
        setStatus(data);
        onQueueChange?.(data);
      }
    } catch {
      // silent
    }
  }, [onQueueChange]);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(() => {
      const state = status?.state || 'idle';
      // Poll faster when running/paused, slower when idle/done
      if (state === 'running' || state === 'paused') {
        fetchStatus();
      }
    }, 1000);
    // Slower poll when idle
    const slowInterval = setInterval(() => {
      const state = status?.state || 'idle';
      if (state === 'idle' || state === 'done') {
        fetchStatus();
      }
    }, 3000);
    return () => {
      clearInterval(interval);
      clearInterval(slowInterval);
    };
  }, [fetchStatus, status?.state]);

  const handleStart = async () => {
    setLoading(true);
    try {
      await fetch('/api/v1/commandqueue/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
      setTimeout(fetchStatus, 200);
    } finally { setLoading(false); }
  };

  const handlePause = async () => {
    setLoading(true);
    try {
      await fetch('/api/v1/commandqueue/pause', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
      setTimeout(fetchStatus, 200);
    } finally { setLoading(false); }
  };

  const handleResume = async () => {
    setLoading(true);
    try {
      await fetch('/api/v1/commandqueue/resume', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
      setTimeout(fetchStatus, 200);
    } finally { setLoading(false); }
  };

  const handleCancel = async () => {
    setLoading(true);
    try {
      await fetch('/api/v1/commandqueue/cancel', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
      setTimeout(fetchStatus, 200);
    } finally { setLoading(false); }
  };

  const handleRemove = async (id: string) => {
    try {
      await fetch('/api/v1/commandqueue/remove', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) });
      setTimeout(fetchStatus, 200);
    } catch { /* ignore */ }
  };

  const handleReorder = async (from: number, to: number) => {
    try {
      await fetch('/api/v1/commandqueue/reorder', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ from, to }) });
      setTimeout(fetchStatus, 200);
    } catch { /* ignore */ }
  };

  const handleClear = async () => {
    try {
      await fetch('/api/v1/commandqueue/clear', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
      setTimeout(fetchStatus, 200);
    } catch { /* ignore */ }
  };

  const handleRestart = async () => {
    try {
      await fetch('/api/v1/commandqueue/restart', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
      setTimeout(fetchStatus, 200);
    } catch { /* ignore */ }
  };

  const handleRetryFailed = async () => {
    try {
      await fetch('/api/v1/commandqueue/retry-failed', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
      setTimeout(fetchStatus, 200);
    } catch { /* ignore */ }
  };

  // Close context menu on outside click
  useEffect(() => {
    if (!contextMenu) return;
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setContextMenu(null);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [contextMenu]);

  // Drag-and-drop reorder
  const handleDragStart = (idx: number) => {
    if (commands[idx]?.status === 'pending') {
      setDragIndex(idx);
    }
  };
  const handleDragOver = (e: React.DragEvent, idx: number) => {
    if (dragIndex !== null && commands[idx]?.status === 'pending') {
      e.preventDefault();
      setDragOverIndex(idx);
    }
  };
  const handleDrop = (e: React.DragEvent, idx: number) => {
    e.preventDefault();
    if (dragIndex !== null && dragIndex !== idx && commands[idx]?.status === 'pending') {
      handleReorder(dragIndex, idx);
    }
    setDragIndex(null);
    setDragOverIndex(null);
  };
  const handleDragEnd = () => {
    setDragIndex(null);
    setDragOverIndex(null);
  };

  const handleAddCommand = async () => {
    if (!addCommand.trim()) return;
    setLoading(true);
    try {
      await fetch('/api/v1/commandqueue/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: addType, node_name: addNode, token_id: addToken, command: addCommand }),
      });
      setAddCommand('');
      setAddNode('');
      setAddToken('');
      setShowAddForm(false);
      setTimeout(fetchStatus, 200);
    } finally { setLoading(false); }
  };

  const state = status?.state || 'idle';
  const commands = status?.commands || [];
  const pendingCmds = commands.filter(c => c.status === 'pending');
  const failedCmds = commands.filter(c => c.status === 'failed');
  const currentIdx = status?.current || 0;
  const remaining = status?.remaining ?? (status ? status.total - currentIdx - 1 : 0);
  const percentage = status?.percentage ?? (status && status.total > 0 ? Math.round((currentIdx / status.total) * 100) : 0);

  // Calculate pending-only indices for reorder
  const getPendingIndex = (cmdIndex: number): number => {
    let pendingIdx = 0;
    for (let i = 0; i < cmdIndex; i++) {
      if (commands[i]?.status === 'pending') pendingIdx++;
    }
    return pendingIdx;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', backgroundColor: 'var(--bg-primary)' }}>
      {/* Toolbar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        <ListChecks size={16} color="var(--accent)" />
        <span style={{ fontSize: '13px', fontWeight: 600 }}>Command Queue</span>
        {/* State badge */}
        <span style={{
          fontSize: '10px',
          fontWeight: 600,
          padding: '2px 8px',
          borderRadius: '10px',
          backgroundColor: stateColors[state] + '22',
          color: stateColors[state],
          textTransform: 'uppercase',
        }}>
          {state}
        </span>
        {status && status.total > 0 && (
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            {currentIdx}/{status.total} • {remaining} remaining • {percentage}%
          </span>
        )}
        <div style={{ flex: 1 }} />
        {/* Controls */}
        {(state === 'idle' || state === 'done') && commands.length > 0 && (
          <button className="btn btn-primary" style={{ fontSize: '11px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '4px' }} onClick={handleStart} disabled={loading || pendingCmds.length === 0}>
            <Play size={12} /> Start
          </button>
        )}
        {state === 'running' && (
          <button className="btn btn-secondary" style={{ fontSize: '11px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '4px' }} onClick={handlePause} disabled={loading}>
            <Pause size={12} /> Pause after current
          </button>
        )}
        {state === 'paused' && (
          <button className="btn btn-primary" style={{ fontSize: '11px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '4px' }} onClick={handleResume} disabled={loading}>
            <Play size={12} /> Resume
          </button>
        )}
        {(state === 'running' || state === 'paused') && (
          <button className="btn btn-secondary" style={{ fontSize: '11px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '4px', color: '#ef4444' }} onClick={handleCancel} disabled={loading}>
            <Square size={12} /> Stop
          </button>
        )}
        {pendingCmds.length > 0 && state !== 'running' && (
          <button className="btn btn-ghost" style={{ fontSize: '11px', padding: '4px 8px', display: 'flex', alignItems: 'center', gap: '4px' }} onClick={handleClear} title="Clear all pending commands">
            <Trash2 size={12} /> Clear
          </button>
        )}
        {commands.length > 0 && (state === 'idle' || state === 'done') && (
          <button className="btn btn-ghost" style={{ fontSize: '11px', padding: '4px 8px', display: 'flex', alignItems: 'center', gap: '4px' }} onClick={handleRestart} title="Restart — reset all commands to pending">
            <RotateCcw size={12} /> Restart
          </button>
        )}
        {failedCmds.length > 0 && (state === 'idle' || state === 'done') && (
          <button className="btn btn-ghost" style={{ fontSize: '11px', padding: '4px 8px', display: 'flex', alignItems: 'center', gap: '4px', color: '#f59e0b', borderColor: '#f59e0b' }} onClick={handleRetryFailed} title={`Retry ${failedCmds.length} failed command${failedCmds.length !== 1 ? 's' : ''}`}>
            <AlertCircle size={12} /> Retry Failed ({failedCmds.length})
          </button>
        )}
        <button className="btn btn-ghost" style={{ fontSize: '11px', padding: '4px 8px', display: 'flex', alignItems: 'center', gap: '4px' }} onClick={() => setShowAddForm(!showAddForm)}>
          <Plus size={12} /> Add
        </button>
      </div>

      {/* Progress bar */}
      {state === 'running' && (
        <div style={{ height: '3px', backgroundColor: 'var(--bg-secondary)', position: 'relative' }}>
          <div style={{
            height: '100%',
            width: `${percentage}%`,
            backgroundColor: '#008a00',
            transition: 'width 0.3s ease',
          }} />
        </div>
      )}

      {/* Add form */}
      {showAddForm && (
        <div style={{ padding: '12px', borderBottom: '1px solid var(--border)', backgroundColor: 'var(--bg-secondary)', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <select
            value={addType}
            onChange={(e) => setAddType(e.target.value)}
            style={{ fontSize: '11px', padding: '4px 8px', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: '4px', color: 'var(--text-primary)' }}
          >
            <option value="raw">RAW (telnet)</option>
            <option value="fbc">FBC</option>
            <option value="rpc">RPC</option>
            <option value="log">LOG</option>
            <option value="lis">LIS</option>
            <option value="bstool">BsTool</option>
          </select>
          <input type="text" placeholder="Node name (e.g. AP01m)" value={addNode} onChange={(e) => setAddNode(e.target.value)} style={{ fontSize: '11px', padding: '4px 8px', width: '120px', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: '4px', color: 'var(--text-primary)' }} />
          <input type="text" placeholder="Token ID" value={addToken} onChange={(e) => setAddToken(e.target.value)} style={{ fontSize: '11px', padding: '4px 8px', width: '80px', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: '4px', color: 'var(--text-primary)' }} />
          <input type="text" placeholder="Command (e.g. print from fbc io structure 1620000)" value={addCommand} onChange={(e) => setAddCommand(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleAddCommand()} style={{ fontSize: '11px', padding: '4px 8px', flex: 1, minWidth: '200px', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: '4px', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }} />
          <button className="btn btn-primary" style={{ fontSize: '11px', padding: '4px 10px' }} onClick={handleAddCommand} disabled={loading || !addCommand.trim()}>Queue</button>
          <button className="btn btn-ghost" style={{ fontSize: '11px', padding: '4px 8px' }} onClick={() => setShowAddForm(false)}>Cancel</button>
        </div>
      )}

      {/* Queue list */}
      <div style={{ flex: 1, overflow: 'auto', padding: '4px 0' }}>
        {commands.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)', fontSize: '13px' }}>
            <ListChecks size={32} color="var(--text-muted)" style={{ margin: '0 auto 12px', opacity: 0.5 }} />
            <p>No commands queued.</p>
            <p style={{ fontSize: '11px', marginTop: '4px' }}>Right-click a node/token/file in the tree, or use Add to queue a command manually.</p>
          </div>
        ) : (
          commands.map((cmd, idx) => {
            const isPending = cmd.status === 'pending';
            const isRunning = cmd.status === 'running';
            const pendingIdx = getPendingIndex(idx);
            const totalPending = pendingCmds.length;

            return (
              <div
                key={cmd.id}
                draggable={isPending}
                onDragStart={() => handleDragStart(idx)}
                onDragOver={(e) => handleDragOver(e, idx)}
                onDrop={(e) => handleDrop(e, idx)}
                onDragEnd={handleDragEnd}
                onContextMenu={(e) => {
                  e.preventDefault();
                  setContextMenu({ x: e.clientX, y: e.clientY, cmdId: cmd.id, cmdStatus: cmd.status });
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '6px 12px',
                  borderBottom: '1px solid var(--border)',
                  backgroundColor: isRunning ? 'rgba(0, 138, 0, 0.08)' : dragOverIndex === idx ? 'rgba(99,102,241,0.12)' : 'transparent',
                  borderLeft: isRunning ? '3px solid #008a00' : dragOverIndex === idx ? '3px solid var(--accent)' : '3px solid transparent',
                  transition: 'all 0.2s ease',
                  cursor: isPending ? 'grab' : 'default',
                  opacity: dragIndex === idx ? 0.5 : 1,
                }}
              >
                {/* Status icon */}
                <div style={{ width: '16px', flexShrink: 0, display: 'flex', justifyContent: 'center' }}>
                  {statusIcons[cmd.status] || <Circle size={12} color="#6b7280" />}
                </div>

                {/* Type badge */}
                <span style={{
                  fontSize: '9px',
                  fontWeight: 700,
                  padding: '2px 5px',
                  borderRadius: '3px',
                  backgroundColor: (typeColors[cmd.type] || '#6b7280') + '22',
                  color: typeColors[cmd.type] || '#6b7280',
                  minWidth: '48px',
                  textAlign: 'center',
                  flexShrink: 0,
                }}>
                  {typeLabels[cmd.type] || cmd.type.toUpperCase()}
                </span>

                {/* Command info */}
                <div style={{ flex: 1, minWidth: 0, overflow: 'hidden' }}>
                  <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {cmd.command}
                  </div>
                  <div style={{ fontSize: '9px', color: 'var(--text-muted)', display: 'flex', gap: '8px' }}>
                    <span>{cmd.node_name}</span>
                    {cmd.token_id && <span>• {cmd.token_id}</span>}
                    {cmd.error && <span style={{ color: '#ef4444' }}>• {cmd.error}</span>}
                  </div>
                </div>

                {/* Elapsed time for running/completed */}
                {cmd.started_at && (
                  <span style={{ fontSize: '9px', color: 'var(--text-muted)', flexShrink: 0 }}>
                    {cmd.finished_at
                      ? `${new Date(cmd.finished_at).getTime() - new Date(cmd.started_at).getTime() > 0 ? Math.round((new Date(cmd.finished_at).getTime() - new Date(cmd.started_at).getTime()) / 100) / 10 + 's' : ''}`
                      : '...'}
                  </span>
                )}

                {/* Reorder controls (only for pending) */}
                {isPending && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1px', flexShrink: 0 }}>
                    <button
                      style={{ border: 'none', background: 'none', cursor: pendingIdx > 0 ? 'pointer' : 'default', padding: '0', opacity: pendingIdx > 0 ? 1 : 0.3 }}
                      onClick={() => {
                        // Find the actual command index of the previous pending
                        let prevPendingIdx = -1;
                        for (let i = idx - 1; i >= 0; i--) {
                          if (commands[i]?.status === 'pending') { prevPendingIdx = i; break; }
                        }
                        if (prevPendingIdx >= 0) handleReorder(idx, prevPendingIdx);
                      }}
                      disabled={pendingIdx === 0}
                    >
                      <ArrowUp size={10} color="var(--text-secondary)" />
                    </button>
                    <button
                      style={{ border: 'none', background: 'none', cursor: pendingIdx < totalPending - 1 ? 'pointer' : 'default', padding: '0', opacity: pendingIdx < totalPending - 1 ? 1 : 0.3 }}
                      onClick={() => {
                        let nextPendingIdx = -1;
                        for (let i = idx + 1; i < commands.length; i++) {
                          if (commands[i]?.status === 'pending') { nextPendingIdx = i; break; }
                        }
                        if (nextPendingIdx >= 0) handleReorder(idx, nextPendingIdx);
                      }}
                      disabled={pendingIdx === totalPending - 1}
                    >
                      <ArrowDown size={10} color="var(--text-secondary)" />
                    </button>
                  </div>
                )}

                {/* Remove button (only for pending) */}
                {isPending && (
                  <button
                    style={{ border: 'none', background: 'none', cursor: 'pointer', padding: '0', flexShrink: 0 }}
                    onClick={() => handleRemove(cmd.id)}
                    title="Remove from queue"
                  >
                    <X size={12} color="#ef4444" />
                  </button>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Bottom summary */}
      {commands.length > 0 && (
        <div style={{ padding: '6px 12px', borderTop: '1px solid var(--border)', fontSize: '10px', color: 'var(--text-muted)', display: 'flex', gap: '12px', flexShrink: 0 }}>
          <span>Total: {commands.length}</span>
          <span style={{ color: '#6b7280' }}>Pending: {pendingCmds.length}</span>
          <span style={{ color: '#10b981' }}>Completed: {commands.filter(c => c.status === 'completed').length}</span>
          <span style={{ color: '#ef4444' }}>Failed: {commands.filter(c => c.status === 'failed').length}</span>
        </div>
      )}

      {/* Context menu for queue items */}
      {contextMenu && (
        <div
          ref={menuRef}
          style={{
            position: 'fixed',
            top: contextMenu.y,
            left: contextMenu.x,
            backgroundColor: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            borderRadius: '6px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            padding: '4px',
            zIndex: 1000,
            minWidth: '160px',
          }}
        >
          {contextMenu.cmdStatus === 'pending' && (
            <button
              style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', fontSize: '11px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)', width: '100%', textAlign: 'left' }}
              onClick={() => { handleRemove(contextMenu.cmdId); setContextMenu(null); }}
            >
              <X size={12} color="#ef4444" /> Remove
            </button>
          )}
          <button
            style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', fontSize: '11px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)', width: '100%', textAlign: 'left' }}
            onClick={() => { handleClear(); setContextMenu(null); }}
          >
            <Trash2 size={12} /> Clear pending
          </button>
          <button
            style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', fontSize: '11px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)', width: '100%', textAlign: 'left' }}
            onClick={() => { handleRestart(); setContextMenu(null); }}
          >
            <RotateCcw size={12} /> Restart all
          </button>
        </div>
      )}
    </div>
  );
}