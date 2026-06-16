import { Link } from 'react-router-dom';
import { FileText } from 'lucide-react';

export default function ReportList() {
  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <FileText size={24} color="var(--accent)" />
        <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Reports</h1>
      </div>
      <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
          Report list coming soon. This page will display all generated reports
          with filtering by node, date range, and report type.
        </p>
        <Link to="/" className="btn btn-secondary">
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
