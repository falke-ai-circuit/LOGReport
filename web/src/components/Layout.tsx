import { NavLink, Outlet } from 'react-router-dom';
import { Server, FileText, LayoutDashboard, Terminal, Settings } from 'lucide-react';
import { useEffect, useState } from 'react';

interface HealthStatus {
  status: string;
  version: string;
  uptime: string;
  db_status: string;
  node_count: number;
}

export default function Layout() {
  const [version, setVersion] = useState<string>('');

  useEffect(() => {
    async function fetchVersion() {
      try {
        const res = await fetch('/health');
        if (res.ok) {
          const data = await res.json();
          setVersion(data.version || '');
        }
      } catch { /* ignore */ }
    }
    fetchVersion();
    const interval = setInterval(fetchVersion, 30000);
    return () => clearInterval(interval);
  }, []);

  const tabStyle = (isActive: boolean): React.CSSProperties => ({
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '10px 16px',
    fontSize: '13px',
    fontWeight: isActive ? 700 : 500,
    color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
    backgroundColor: isActive ? 'rgba(99,102,241,0.08)' : 'transparent',
    textDecoration: 'none',
    borderBottom: isActive ? '2px solid var(--accent)' : '2px solid transparent',
    transition: 'all 0.15s ease',
    cursor: 'pointer',
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <nav
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0',
          backgroundColor: 'var(--bg-secondary)',
          borderBottom: '1px solid var(--border)',
          padding: '0 12px',
          height: '44px',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            fontSize: '14px',
            fontWeight: 700,
            color: 'var(--accent)',
            padding: '0 12px',
            fontFamily: 'var(--font-mono)',
            marginRight: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <span style={{ fontSize: 16 }}>📋</span>
          LOGReport
          {version && (
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 400, marginLeft: '4px' }}>
              {version}
            </span>
          )}
        </div>

        <NavLink to="/" end style={({ isActive }) => tabStyle(isActive)}>
          <LayoutDashboard size={14} />
          Dashboard
        </NavLink>

        <NavLink to="/nodes" style={({ isActive }) => tabStyle(isActive)}>
          <Server size={14} />
          Nodes
        </NavLink>

        <NavLink to="/commander" style={({ isActive }) => tabStyle(isActive)}>
          <Terminal size={14} />
          Commander
        </NavLink>

        <NavLink to="/reports" style={({ isActive }) => tabStyle(isActive)}>
          <FileText size={14} />
          Reports
        </NavLink>

        <NavLink to="/settings" style={({ isActive }) => tabStyle(isActive)}>
          <Settings size={14} />
          Settings
        </NavLink>
      </nav>

      <main
        style={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
          backgroundColor: 'var(--bg-primary)',
        }}
      >
        <Outlet />
      </main>
    </div>
  );
}