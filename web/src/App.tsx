import { Routes, Route } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import StatusBar from './components/StatusBar';
import NodeBrowser from './components/NodeBrowser';
import NodeDetail from './components/NodeDetail';
import ReportList from './components/ReportList';
import ReportDetail from './components/ReportDetail';
import SysFileUpload from './components/SysFileUpload';
import CommanderLayout from './components/CommanderLayout';

function Dashboard() {
  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '16px' }}>
        LOGReport Dashboard
      </h1>
      <p style={{ color: 'var(--text-secondary)' }}>
        Welcome to LOGReport. Select a section from the navigation or use the
        sidebar to browse nodes and reports.
      </p>
    </div>
  );
}

function NotFound() {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        padding: '48px',
        textAlign: 'center',
      }}
    >
      <h1
        style={{
          fontSize: '64px',
          fontWeight: 700,
          color: 'var(--accent)',
          fontFamily: 'var(--font-mono)',
          marginBottom: '8px',
        }}
      >
        404
      </h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: '16px', marginBottom: '24px' }}>
        The page you're looking for doesn't exist.
      </p>
      <a href="/" className="btn btn-primary">
        Back to Dashboard
      </a>
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          backgroundColor: 'var(--bg-primary)',
          color: 'var(--text-primary)',
        }}
      >
        <div style={{ flex: 1, overflow: 'auto' }}>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/nodes" element={<NodeBrowser />} />
              <Route path="/nodes/:addr" element={<NodeDetail />} />
              <Route path="/reports" element={<ReportList />} />
              <Route path="/reports/:id" element={<ReportDetail />} />
              <Route path="/sysfile" element={<SysFileUpload />} />
              <Route path="/commander" element={<CommanderLayout />} />
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
        </div>
        <StatusBar />
      </div>
    </ErrorBoundary>
  );
}
