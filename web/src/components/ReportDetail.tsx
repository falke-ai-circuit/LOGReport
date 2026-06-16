import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FileText,
  Download,
  Loader2,
  AlertTriangle,
  ArrowLeft,
  FileJson,
  FileArchive,
  CheckCircle,
  XCircle,
  Clock,
} from 'lucide-react';
import type { ApiReport } from '../types/api';

const STATUS_COLORS: Record<string, string> = {
  completed: 'var(--success)',
  generating: 'var(--warning)',
  pending: 'var(--info)',
  failed: 'var(--error)',
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  completed: <CheckCircle size={16} />,
  generating: <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />,
  pending: <Clock size={16} />,
  failed: <XCircle size={16} />,
};

export default function ReportDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [report, setReport] = useState<ApiReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // JSON preview content
  const [jsonContent, setJsonContent] = useState<string | null>(null);
  const [jsonLoading, setJsonLoading] = useState(false);

  // Fetch report
  useEffect(() => {
    if (!id) return;
    const reportId = id;
    let cancelled = false;

    async function fetchReport() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`/api/v1/reports/${encodeURIComponent(reportId)}`);
        if (!res.ok) {
          const data = await res.json().catch(() => ({ message: 'Report not found' }));
          throw new Error(data.message || `HTTP ${res.status}`);
        }
        const data: ApiReport = await res.json();
        if (!cancelled) {
          setReport(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load report');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchReport();
    return () => { cancelled = true; };
  }, [id]);

  // Fetch JSON preview if format is json and report is completed
  useEffect(() => {
    if (!report || report.format !== 'json' || report.status !== 'completed' || !report.file_path) {
      return;
    }
    let cancelled = false;

    async function fetchJson() {
      setJsonLoading(true);
      try {
        // The GET /api/v1/reports/{id} endpoint serves the file directly
        // when the report is completed. We need to fetch it as text.
        const res = await fetch(`/api/v1/reports/${encodeURIComponent(report!.report_id)}`);
        if (!res.ok) return;
        const contentType = res.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
          const text = await res.text();
          if (!cancelled) {
            setJsonContent(text);
          }
        }
      } catch {
        // Silently fail — preview is optional
      } finally {
        if (!cancelled) setJsonLoading(false);
      }
    }

    fetchJson();
    return () => { cancelled = true; };
  }, [report]);

  // Download handler
  function handleDownload() {
    if (!report?.report_id) return;
    // Open download in new tab
    window.open(`/api/v1/reports/${encodeURIComponent(report.report_id)}`, '_blank');
  }

  // Loading state
  if (loading) {
    return (
      <div style={{ padding: '24px' }}>
        <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
          <Loader2
            size={24}
            color="var(--accent)"
            style={{ animation: 'spin 1s linear infinite', marginBottom: '12px' }}
          />
          <p style={{ color: 'var(--text-secondary)' }}>Loading report...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div style={{ padding: '24px' }}>
        <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
          <AlertTriangle size={32} color="var(--error)" style={{ marginBottom: '12px' }} />
          <p style={{ color: 'var(--error)', marginBottom: '12px' }}>{error}</p>
          <button className="btn btn-secondary" onClick={() => navigate('/reports')}>
            <ArrowLeft size={16} />
            Back to Reports
          </button>
        </div>
      </div>
    );
  }

  if (!report) return null;

  const statusColor = STATUS_COLORS[report.status] || 'var(--text-muted)';
  const statusIcon = STATUS_ICONS[report.status] || null;
  const isCompleted = report.status === 'completed';
  const isFailed = report.status === 'failed';
  const isJson = report.format === 'json';
  const isDocx = report.format === 'docx';

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
          <button
            className="btn btn-ghost"
            onClick={() => navigate('/reports')}
            style={{ padding: '4px 8px' }}
          >
            <ArrowLeft size={18} />
          </button>
          <FileText size={24} color="var(--accent)" />
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Report Detail</h1>
        </div>
        {isCompleted && (
          <button className="btn btn-primary" onClick={handleDownload}>
            <Download size={16} />
            Download
          </button>
        )}
      </div>

      {/* Report info card */}
      <div className="card" style={{ padding: '20px', marginBottom: '16px' }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
            gap: '16px',
          }}
        >
          <InfoField label="Report ID" value={report.report_id} mono />
          <InfoField
            label="Node"
            value={report.node_addresses?.join(', ') || '—'}
            mono
          />
          <InfoField
            label="Format"
            value={
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                {isJson ? <FileJson size={14} /> : <FileArchive size={14} />}
                <span style={{ fontFamily: 'var(--font-mono)', textTransform: 'uppercase' }}>
                  {report.format}
                </span>
              </span>
            }
          />
          <InfoField
            label="Status"
            value={
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  color: statusColor,
                  backgroundColor: `${statusColor}18`,
                  padding: '2px 10px',
                  borderRadius: '4px',
                  border: `1px solid ${statusColor}44`,
                  fontSize: '13px',
                  fontWeight: 500,
                }}
              >
                {statusIcon}
                {report.status}
              </span>
            }
          />
          <InfoField
            label="Created"
            value={report.created_at ? new Date(report.created_at).toLocaleString() : '—'}
          />
          <InfoField
            label="Completed"
            value={report.completed_at ? new Date(report.completed_at).toLocaleString() : '—'}
          />
          {report.file_size != null && (
            <InfoField
              label="File Size"
              value={formatFileSize(report.file_size)}
            />
          )}
          {report.template && (
            <InfoField label="Template" value={report.template} mono />
          )}
        </div>

        {/* Error message for failed reports */}
        {isFailed && report.error_message && (
          <div
            style={{
              marginTop: '16px',
              padding: '12px',
              backgroundColor: 'rgba(239,68,68,0.1)',
              border: '1px solid var(--error)',
              borderRadius: '6px',
              color: 'var(--error)',
              fontSize: '13px',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {report.error_message}
          </div>
        )}
      </div>

      {/* Report preview */}
      {isCompleted && (
        <div className="card" style={{ padding: '20px' }}>
          <h3
            style={{
              fontSize: '14px',
              fontWeight: 600,
              color: 'var(--accent)',
              marginBottom: '12px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            Preview
          </h3>

          {/* JSON preview */}
          {isJson && (
            <>
              {jsonLoading && (
                <div style={{ textAlign: 'center', padding: '24px' }}>
                  <Loader2
                    size={20}
                    color="var(--accent)"
                    style={{ animation: 'spin 1s linear infinite', marginBottom: '8px' }}
                  />
                  <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                    Loading preview...
                  </p>
                </div>
              )}
              {!jsonLoading && jsonContent && (
                <pre
                  style={{
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    padding: '16px',
                    fontSize: '12px',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-primary)',
                    overflow: 'auto',
                    maxHeight: '500px',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    lineHeight: 1.6,
                  }}
                >
                  {formatJson(jsonContent)}
                </pre>
              )}
              {!jsonLoading && !jsonContent && (
                <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-secondary)' }}>
                  <p style={{ fontSize: '13px', marginBottom: '12px' }}>
                    JSON preview not available. Download the file to view contents.
                  </p>
                  <button className="btn btn-primary" onClick={handleDownload}>
                    <Download size={14} />
                    Download JSON
                  </button>
                </div>
              )}
            </>
          )}

          {/* DOCX preview — download link */}
          {isDocx && (
            <div style={{ textAlign: 'center', padding: '24px' }}>
              <FileArchive size={32} color="var(--accent)" style={{ marginBottom: '12px' }} />
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '16px' }}>
                DOCX reports cannot be previewed in the browser. Download the file to view in
                Microsoft Word or a compatible editor.
              </p>
              <button className="btn btn-primary" onClick={handleDownload}>
                <Download size={14} />
                Download DOCX
              </button>
            </div>
          )}
        </div>
      )}

      {/* Pending/generating notice */}
      {!isCompleted && !isFailed && (
        <div className="card" style={{ textAlign: 'center', padding: '32px' }}>
          <Loader2
            size={24}
            color="var(--warning)"
            style={{ animation: 'spin 1s linear infinite', marginBottom: '12px' }}
          />
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
            Report is still being generated. Check back shortly.
          </p>
        </div>
      )}
    </div>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────

function InfoField({
  label,
  value,
  mono,
}: {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <div>
      <div
        style={{
          fontSize: '11px',
          fontWeight: 500,
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          marginBottom: '4px',
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: '14px',
          fontWeight: 500,
          color: 'var(--text-primary)',
          fontFamily: mono ? 'var(--font-mono)' : 'var(--font-sans)',
        }}
      >
        {value}
      </div>
    </div>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatJson(raw: string): string {
  try {
    const parsed = JSON.parse(raw);
    return JSON.stringify(parsed, null, 2);
  } catch {
    return raw;
  }
}
