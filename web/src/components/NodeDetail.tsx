import { useParams, Link } from 'react-router-dom';
import { Cpu } from 'lucide-react';

export default function NodeDetail() {
  const { addr } = useParams<{ addr: string }>();

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <Cpu size={24} color="var(--accent)" />
        <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Node Detail: {addr}</h1>
      </div>
      <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
          Node detail view coming soon. This page will show I/O points, system
          files, and report history for node {addr}.
        </p>
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <Link to="/nodes" className="btn btn-secondary">
            Back to Nodes
          </Link>
          <Link to="/" className="btn btn-ghost">
            Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
