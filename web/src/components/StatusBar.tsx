import { useEffect, useState } from 'react';
import { Activity, Server, Database, Cpu, FolderOpen } from 'lucide-react';
import { useActiveProject, useProjects } from '../hooks/useActiveProject';

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
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {activeProject ? (
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--accent)' }} title={activeLogRoot || 'No log root set'}>
            <FolderOpen size={12} />
            {activeProject.project_number} — {activeProject.ship_name}
          </span>
        ) : (
          <span style={{ color: 'var(--text-muted)' }}>
            No project
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