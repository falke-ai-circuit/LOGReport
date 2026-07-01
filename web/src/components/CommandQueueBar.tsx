import { useState, useEffect } from 'react';
import { Play, Pause, Square, Loader2 } from 'lucide-react';
import type { QueueStatusResponse } from '../types/api';

export interface CommandQueueBarProps {
  status?: QueueStatusResponse | null;
}

export default function CommandQueueBar({ status: externalStatus }: CommandQueueBarProps) {
  const [status, setStatus] = useState<QueueStatusResponse | null>(externalStatus || null);
  const [actionLoading, setActionLoading] = useState(false);

  // Use external status if provided, otherwise poll
  useEffect(() => {
    if (externalStatus !== undefined) {
      setStatus(externalStatus);
    }
  }, [externalStatus]);

  // Always poll at 1s — bar is lightweight and should work independently
  // of whether external status is provided or not
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;

    async function pollStatus() {
      try {
        const res = await fetch('/api/v1/commandqueue/status');
        if (!res.ok) return;
        const data: QueueStatusResponse = await res.json();
        setStatus(data);
      } catch {
        // ignore
      }
    }

    interval = setInterval(pollStatus, 1000);
    pollStatus();

    return () => {
      if (interval) clearInterval(interval);
    };
  }, []); // always poll, independent of external status

  async function handleAction(action: 'start' | 'pause' | 'resume' | 'cancel') {
    setActionLoading(true);
    try {
      await fetch(`/api/v1/commandqueue/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      // Refresh
      const res = await fetch('/api/v1/commandqueue/status');
      if (res.ok) {
        const data: QueueStatusResponse = await res.json();
        setStatus(data);
      }
    } catch {
      // ignore
    } finally {
      setActionLoading(false);
    }
  }

  // Don't render if no queue activity
  if (!status || (status.total === 0 && status.state === 'idle')) {
    return null;
  }

  const stateColor =
    status.state === 'running'
      ? 'var(--success)'
      : status.state === 'paused'
        ? '#f59e0b'
        : status.state === 'done'
          ? 'var(--text-muted)'
          : 'var(--text-muted)';

  const progress = status.total > 0 ? Math.round((status.current / status.total) * 100) : 0;

  // Find current command
  const currentCmd = status.commands?.[status.current];
  // Build a descriptive label showing which file is being worked on
  const cmdLabel = currentCmd
    ? (() => {
        const parts: string[] = [];
        parts.push(`${currentCmd.type?.toUpperCase()}`);
        parts.push(currentCmd.node_name || '');
        if (currentCmd.token_id) parts.push(`token ${currentCmd.token_id}`);
        // Show the target filename for this command
        if (currentCmd.node_name && currentCmd.type && currentCmd.token_id) {
          const ext = currentCmd.type === 'fbc' ? '.fbc' : currentCmd.type === 'rpc' ? '.rpc' : '.log';
          const stationName = currentCmd.node_name.split('_')[0];
          parts.push(`→ ${stationName}_${currentCmd.token_id}${ext}`);
        }
        return parts.join(' ');
      })()
    : '';

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '6px 12px',
        backgroundColor: 'var(--bg-elevated)',
        borderTop: '1px solid var(--border)',
        fontSize: '12px',
        minHeight: '36px',
      }}
    >
      {/* Status dot */}
      <span
        style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: stateColor,
          flexShrink: 0,
        }}
      />

      {/* Progress text */}
      <span style={{ color: 'var(--text-secondary)' }}>
        {status.state === 'idle' && status.total > 0
          ? `Queue: ${status.total} command${status.total !== 1 ? 's' : ''} ready`
          : status.state === 'done'
            ? `Queue complete — ${status.total} command${status.total !== 1 ? 's' : ''}`
            : `Command ${status.current + 1}/${status.total}: ${cmdLabel} — ${status.total - status.current - 1} remaining`}
      </span>

      {/* Progress bar */}
      {status.total > 0 && (
        <div
          style={{
            flex: 1,
            maxWidth: '200px',
            height: '4px',
            backgroundColor: 'var(--bg-secondary)',
            borderRadius: '2px',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${progress}%`,
              height: '100%',
              backgroundColor: stateColor,
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      )}

      {/* Controls */}
      <div style={{ display: 'flex', gap: '4px', marginLeft: 'auto' }}>
        {actionLoading && (
          <Loader2 size={14} style={{ animation: 'spin 1s linear infinite', color: 'var(--accent)' }} />
        )}
        {status.state === 'idle' && status.total > 0 && (
          <button
            className="btn btn-ghost"
            style={{ padding: '2px 6px', fontSize: '11px' }}
            onClick={() => handleAction('start')}
            disabled={actionLoading}
            title="Start queue"
          >
            <Play size={12} />
          </button>
        )}
        {status.state === 'running' && (
          <button
            className="btn btn-ghost"
            style={{ padding: '2px 6px', fontSize: '11px' }}
            onClick={() => handleAction('pause')}
            disabled={actionLoading}
            title="Pause"
          >
            <Pause size={12} />
          </button>
        )}
        {status.state === 'paused' && (
          <button
            className="btn btn-ghost"
            style={{ padding: '2px 6px', fontSize: '11px' }}
            onClick={() => handleAction('resume')}
            disabled={actionLoading}
            title="Resume"
          >
            <Play size={12} />
          </button>
        )}
        {(status.state === 'running' || status.state === 'paused') && (
          <button
            className="btn btn-ghost"
            style={{ padding: '2px 6px', fontSize: '11px', color: 'var(--error)' }}
            onClick={() => handleAction('cancel')}
            disabled={actionLoading}
            title="Cancel"
          >
            <Square size={12} />
          </button>
        )}
      </div>
    </div>
  );
}