import { Link } from 'react-router-dom';
import { Server } from 'lucide-react';

export default function NodeBrowser() {
  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <Server size={24} color="var(--accent)" />
        <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Node Browser</h1>
      </div>
      <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
          Node browser coming soon. This component will display all discovered
          Valmet DNA nodes with filtering and search capabilities.
        </p>
        <Link to="/" className="btn btn-secondary">
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
