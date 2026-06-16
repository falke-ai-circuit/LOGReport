import { useParams, Link } from 'react-router-dom';
import { FileText } from 'lucide-react';

export default function ReportDetail() {
  const { id } = useParams<{ id: string }>();

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <FileText size={24} color="var(--accent)" />
        <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Report Detail: {id}</h1>
      </div>
      <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
          Report detail view coming soon. This page will display the full report
          content, charts, and export options for report {id}.
        </p>
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <Link to="/reports" className="btn btn-secondary">
            Back to Reports
          </Link>
          <Link to="/" className="btn btn-ghost">
            Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
