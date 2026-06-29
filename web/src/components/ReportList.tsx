import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Plus, Loader2, AlertTriangle, FileJson, FileArchive } from 'lucide-react';
import type { ApiReport, ReportListResponse } from '../types/api';
import ReportConfig from './ReportConfig';

const STATUS_COLORS: Record<string, string> = {
  completed: 'var(--success)',
  generating: 'var(--warning)',
  pending: 'var(--info)',
  failed: 'var(--error)',
};

const STATUS_LABELS: Record<string, string> = {
  completed: 'Completed',
  generating: 'Generating',
  pending: 'Pending',
  failed: 'Failed',
};

const FORMAT_ICONS: Record<string, React.ReactNode> = {
  json: <FileJson size={14} />,
  docx: <FileArchive size={14} />,
  pdf: <FileText size={14} />,
};

export default function ReportList() {
  const navigate = useNavigate();

  // Report list state
  const [reports, setReports] = useState<ApiReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Config modal
  const [showConfig, setShowConfig] = useState(false);

  // Fetch reports
  useEffect(() => {
    let cancelled = false;

    async function fetchReports() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch('/api/v1/reports');
        if (!res.ok) {
          const text = await res.text().catch(() => 'Unknown error');
          throw new Error(`HTTP ${res.status}: ${text}`);
        }
        const data: ReportListResponse = await res.json();
        if (!cancelled) {
          setReports(data.reports ?? []);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load reports');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchReports();
    return () => { cancelled = true; };
  }, []);

  // Refresh after generating
  function handleGenerated(reportId: string) {
    setShowConfig(false);
    // Refresh list
    fetch('/api/v1/reports')
      .then((res) => res.json())
      .then((data: ReportListResponse) => setReports(data.reports ?? []))
      .catch(() => {});
    // Navigate to new report
    navigate(`/reports/${encodeURIComponent(reportId)}`);
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '24px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <FileText size={24} color="var(--accent)" />
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Reports</h1>
        </div>
        <button className="btn btn-primary" onClick={() => setShowConfig(true)}>
          <Plus size={16} />
          Generate New Report
        </button>
      </div>

      {/* Config modal */}
      {showConfig && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowConfig(false);
          }}
        >
          <div
            className="card-elevated"
            style={{ width: '480px', maxWidth: '90vw', maxHeight: '90vh', overflow: 'auto' }}
          >
            <ReportConfig
              onSuccess={handleGenerated}
              onCancel={() => setShowConfig(false)}
            />
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
          <Loader2
            size={24}
            color="var(--accent)"
            style={{ animation: 'spin 1s linear infinite', marginBottom: '12px' }}
          />
          <p style={{ color: 'var(--text-secondary)' }}>Loading reports...</p>
        </div>
      )}

      {/* Error state */}
      {!loading && error && (
        <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
          <AlertTriangle size={32} color="var(--error)" style={{ marginBottom: '12px' }} />
          <p style={{ color: 'var(--error)', marginBottom: '12px' }}>{error}</p>
          <button className="btn btn-secondary" onClick={() => window.location.reload()}>
            Retry
          </button>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && reports.length === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
          <FileText size={32} color="var(--text-muted)" style={{ marginBottom: '12px' }} />
          <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
            No reports generated. Create your first report to get started.
          </p>
          <button className="btn btn-primary" onClick={() => setShowConfig(true)}>
            <Plus size={16} />
            Generate New Report
          </button>
        </div>
      )}

      {/* Report list */}
      {!loading && !error && reports.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {reports.map((report) => {
            const statusColor = STATUS_COLORS[report.status] || 'var(--text-muted)';
            const statusLabel = STATUS_LABELS[report.status] || report.status;
            const formatIcon = FORMAT_ICONS[report.format] || null;

            return (
              <div
                key={report.report_id}
                className="card"
                onClick={() => navigate(`/reports/${encodeURIComponent(report.report_id)}`)}
                style={{
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 16px',
                  transition: 'border-color 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.borderColor = 'var(--accent)';
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)';
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {/* Format icon */}
                  <span style={{ color: 'var(--accent)', display: 'flex' }}>
                    {formatIcon}
                  </span>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '14px' }}>
                      {report.report_id}
                    </div>
                    <div
                      style={{
                        fontSize: '12px',
                        color: 'var(--text-secondary)',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      {report.node_addresses?.join(', ') || '—'}
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {/* Format badge */}
                  <span
                    style={{
                      fontSize: '11px',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 500,
                      color: 'var(--accent)',
                      backgroundColor: 'var(--accent-dim)',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      textTransform: 'uppercase',
                    }}
                  >
                    {report.format}
                  </span>
                  {/* Status badge */}
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '5px',
                      fontSize: '11px',
                      fontWeight: 500,
                      color: statusColor,
                      backgroundColor: `${statusColor}18`,
                      padding: '2px 8px',
                      borderRadius: '4px',
                      border: `1px solid ${statusColor}44`,
                    }}
                  >
                    <span
                      style={{
                        width: '6px',
                        height: '6px',
                        borderRadius: '50%',
                        backgroundColor: statusColor,
                      }}
                    />
                    {statusLabel}
                  </span>
                  {/* Created date */}
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {report.created_at
                      ? new Date(report.created_at).toLocaleDateString()
                      : '—'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
