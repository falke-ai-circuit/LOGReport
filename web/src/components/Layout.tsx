import { NavLink, Outlet } from 'react-router-dom';
import { Server, FileText, LayoutDashboard } from 'lucide-react';

export default function Layout() {
  const linkStyle = (isActive: boolean): React.CSSProperties => ({
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 12px',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: isActive ? 600 : 400,
    color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
    backgroundColor: isActive ? 'var(--bg-elevated)' : 'transparent',
    textDecoration: 'none',
    transition: 'all 0.15s ease',
  });

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* Sidebar */}
      <nav
        style={{
          width: '220px',
          minWidth: '220px',
          backgroundColor: 'var(--bg-secondary)',
          borderRight: '1px solid var(--border)',
          display: 'flex',
          flexDirection: 'column',
          padding: '16px 12px',
          gap: '4px',
        }}
      >
        <div
          style={{
            fontSize: '16px',
            fontWeight: 700,
            color: 'var(--accent)',
            padding: '8px 12px',
            marginBottom: '12px',
            fontFamily: 'var(--font-mono)',
          }}
        >
          LOGReport
        </div>

        <NavLink
          to="/"
          end
          style={({ isActive }) => linkStyle(isActive)}
        >
          <LayoutDashboard size={16} />
          Dashboard
        </NavLink>

        <NavLink
          to="/nodes"
          style={({ isActive }) => linkStyle(isActive)}
        >
          <Server size={16} />
          Nodes
        </NavLink>

        <NavLink
          to="/reports"
          style={({ isActive }) => linkStyle(isActive)}
        >
          <FileText size={16} />
          Reports
        </NavLink>
      </nav>

      {/* Content area */}
      <main
        style={{
          flex: 1,
          overflow: 'auto',
          backgroundColor: 'var(--bg-primary)',
        }}
      >
        <Outlet />
      </main>
    </div>
  );
}
