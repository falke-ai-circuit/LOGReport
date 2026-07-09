import { useEffect, useState } from 'react';
import { Activity, Server, Database, Cpu, FolderOpen, Loader2 } from 'lucide-react';
import { useActiveProject, useProjects } from '../hooks/useActiveProject';
import type { QueueStatusResponse } from '../types/api';

interface HealthStatus {
  status: string;
  version: string;
  uptime: string;
  db_status: string;
  node_count: number;
}

export default function StatusBar() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [queueStatus, setQueueStatus] = useState<QueueStatusResponse | null>(null);
  const { activeProjectId, activeLogRoot } = useActiveProject();
  const { projects } = useProjects();
  const activeProject = projects.find((p) => p.id === activeProjectId) || null;

  useEffect(() => {
    let mounted = true;

    async function check() {
      try {
        const res = await fetch('/health');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (mounted) {
          setHealth(data);
          setConnected(true);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setConnected(false);
          setError(err instanceof Error ? err.message : 'Connection failed');
        }
      }
    }

    check();
    const interval = setInterval(check, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  // Poll queue status to show currently running command in the status bar
  // Faster when active (1s), slower when idle (5s) to reduce requests
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;

    async function pollQueue() {
      try {
        const res = await fetch('/api/v1/commandqueue/status');
        if (!res.ok) return;
        const data: QueueStatusResponse = await res.json();
        setQueueStatus(data);
      } catch {
        // ignore
      }
    }

    const isActive = queueStatus && (queueStatus.total > 0 || queueStatus.state === 'running' || queueStatus.state === 'paused');
    interval = setInterval(pollQueue, isActive ? 1000 : 5000);
    pollQueue();

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [queueStatus?.state, queueStatus?.total]);

  // Build current command label
  const currentCmd = queueStatus?.commands?.[queueStatus.current];
  const cmdLabel = currentCmd
    ? (() => {
        const parts: string[] = [];
        parts.push(`${(currentCmd.type || '').toUpperCase()}`);
        if (currentCmd.node_name) parts.push(currentCmd.node_name);
        if (currentCmd.token_id) parts.push(`token ${currentCmd.token_id}`);
        return parts.join(' ');
      })()
    : '';

  const isRunning = queueStatus?.state === 'running';
  const isPaused = queueStatus?.state === 'paused';
  const hasQueue = queueStatus && queueStatus.total > 0;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '6px 16px',
      backgroundColor: 'var(--bg-secondary)',
      borderTop: '1px solid var(--border)',
      fontSize: '12px',
      fontFamily: 'var(--font-mono)',
      color: 'var(--text-secondary)',
      minHeight: '32px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <span style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          color: connected ? 'var(--success)' : 'var(--error)',
        }}>
          <Activity size={12} />
          {connected ? 'Connected' : error ? `Offline: ${error}` : 'Connecting...'}
        </span>
        {health && (
          <>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Server size={12} />
              v{health.version}
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Cpu size={12} />
              {health.uptime}
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Database size={12} />
              {health.db_status}
            </span>
          </>
        )}
        {/* Current queue command — always visible when queue is active */}
        {hasQueue && (isRunning || isPaused) && (
          <span style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            color: isRunning ? 'var(--accent)' : '#f59e0b',
            fontWeight: 500,
          }}>
            {isRunning && <Loader2 size={11} className="spin" />}
            {isPaused && <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#f59e0b', display: 'inline-block' }} />}
            {queueStatus.current + 1}/{queueStatus.total}: {cmdLabel} — {queueStatus.remaining} remaining
          </span>
        )}
        {hasQueue && queueStatus?.state === 'done' && (
          <span style={{ color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            ✓ Queue complete — {queueStatus.total} commands
          </span>
        )}
        {hasQueue && queueStatus?.state === 'idle' && (
          <span style={{ color: 'var(--text-muted)' }}>
            Queue: {queueStatus.total} commands ready
          </span>
        )}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {activeProject ? (
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--accent)' }} title={activeLogRoot || 'No log root set'}>
            <FolderOpen size={12} />
            {activeProject.project_number} — {activeProject.ship_name}
            {activeLogRoot && <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: '4px', fontFamily: 'var(--font-mono)' }}>{activeLogRoot}</span>}
          </span>
        ) : (
          <span style={{ color: 'var(--text-muted)' }}>
            No project selected
          </span>
        )}
        {health && (
          <span>
            Nodes: {health.node_count}
          </span>
        )}
        <span style={{ color: 'var(--accent)' }}>LOGReport</span>
      </div>
    </div>
  );
}