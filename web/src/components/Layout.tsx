import { NavLink, Outlet } from 'react-router-dom';
import { Server, FileText, LayoutDashboard, Terminal, Settings } from 'lucide-react';

export default function Layout() {
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
          <img src="/valmet-logo.png" alt="Valmet" style={{ height: 18, width: 'auto' }} />
          <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--accent)' }}>LOGReport</span>
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