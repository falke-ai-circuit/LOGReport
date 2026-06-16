import { Routes, Route } from 'react-router-dom';
import StatusBar from './components/StatusBar';
import NodeBrowser from './components/NodeBrowser';
import NodeDetail from './components/NodeDetail';
import ReportList from './components/ReportList';
import ReportDetail from './components/ReportDetail';

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

export default function App() {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      backgroundColor: 'var(--bg-primary)',
      color: 'var(--text-primary)',
    }}>
      <div style={{ flex: 1, overflow: 'auto' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/nodes" element={<NodeBrowser />} />
          <Route path="/nodes/:addr" element={<NodeDetail />} />
          <Route path="/reports" element={<ReportList />} />
          <Route path="/reports/:id" element={<ReportDetail />} />
        </Routes>
      </div>
      <StatusBar />
    </div>
  );
}
