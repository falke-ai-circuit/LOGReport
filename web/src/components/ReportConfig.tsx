import { useState, useEffect } from 'react';
import { X, Loader2, AlertTriangle } from 'lucide-react';
import type { ApiNode, NodeListResponse, ApiReport } from '../types/api';

interface ReportConfigProps {
  onSuccess: (reportId: string) => void;
  onCancel: () => void;
}

export default function ReportConfig({ onSuccess, onCancel }: ReportConfigProps) {
  // Node list for dropdown
  const [nodes, setNodes] = useState<ApiNode[]>([]);
  const [nodesLoading, setNodesLoading] = useState(true);
  const [nodesError, setNodesError] = useState<string | null>(null);

  // Form state
  const [nodeAddress, setNodeAddress] = useState('');
  const [format, setFormat] = useState<'docx' | 'json' | 'pdf'>('docx');
  const [template, setTemplate] = useState('');
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [logRoot, setLogRoot] = useState('');

  // Project + report type
  const [projectId, setProjectId] = useState<number | ''>('');
  const [reportType, setReportType] = useState<'survey' | 'drydock'>('survey');
  const [projects, setProjects] = useState<Array<{ id: number; project_number: string; ship_name: string }>>([]);

  // Submission state
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Validation
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Fetch nodes for dropdown
  useEffect(() => {
    let cancelled = false;

    async function fetchNodes() {
      setNodesLoading(true);
      setNodesError(null);
      try {
        const res = await fetch('/api/v1/nodes');
        if (!res.ok) {
          const text = await res.text().catch(() => 'Unknown error');
          throw new Error(`HTTP ${res.status}: ${text}`);
        }
        const data: NodeListResponse = await res.json();
        if (!cancelled) {
          setNodes(data.nodes ?? []);
        }
      } catch (err) {
        if (!cancelled) {
          setNodesError(err instanceof Error ? err.message : 'Failed to load nodes');
        }
      } finally {
        if (!cancelled) setNodesLoading(false);
      }
    }

    fetchNodes();
    return () => { cancelled = true; };
  }, []);

  // Fetch projects for dropdown
  useEffect(() => {
    async function fetchProjects() {
      try {
        const res = await fetch('/api/v1/projects');
        if (!res.ok) return;
        const data = await res.json();
        setProjects(data.projects || []);
      } catch {
        // ignore
      }
    }
    fetchProjects();
  }, []);

  // Validate form
  function validate(): boolean {
    const newErrors: Record<string, string> = {};
    if (!nodeAddress) {
      newErrors.nodeAddress = 'Node is required';
    }
    if (!format) {
      newErrors.format = 'Format is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  // Submit handler
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    setSubmitError(null);

    try {
      const body: Record<string, unknown> = {
        node_addresses: [nodeAddress],
        format,
        report_type: reportType,
      };
      if (projectId) body.project_id = projectId;
      if (template) body.template = template;
      if (logRoot) body.log_root = logRoot;
      if (title || author) {
        body.options = {};
        if (title) (body.options as Record<string, unknown>).title = title;
        if (author) (body.options as Record<string, unknown>).author = author;
      }

      const res = await fetch('/api/v1/reports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Generation failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }

      const data: ApiReport = await res.json();
      onSuccess(data.report_id);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Report generation failed');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
        }}
      >
        <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Generate Report</h2>
        <button
          className="btn btn-ghost"
          onClick={onCancel}
          style={{ padding: '4px' }}
          disabled={submitting}
        >
          <X size={18} />
        </button>
      </div>

      {/* Nodes loading */}
      {nodesLoading && (
        <div style={{ textAlign: 'center', padding: '24px' }}>
          <Loader2
            size={20}
            color="var(--accent)"
            style={{ animation: 'spin 1s linear infinite', marginBottom: '8px' }}
          />
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Loading nodes...</p>
        </div>
      )}

      {/* Nodes error */}
      {!nodesLoading && nodesError && (
        <div style={{ textAlign: 'center', padding: '24px' }}>
          <AlertTriangle size={20} color="var(--error)" style={{ marginBottom: '8px' }} />
          <p style={{ color: 'var(--error)', fontSize: '13px' }}>{nodesError}</p>
        </div>
      )}

      {/* Form */}
      {!nodesLoading && !nodesError && (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Project dropdown */}
          <div>
            <label style={labelStyle}>Project</label>
            <select
              value={projectId}
              onChange={(e) => setProjectId(e.target.value === '' ? '' : Number(e.target.value))}
              style={inputStyle}
            >
              <option value="">Select a project (optional)...</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.project_number} — {p.ship_name}
                </option>
              ))}
            </select>
          </div>

          {/* Report type dropdown */}
          <div>
            <label style={labelStyle}>Report Type *</label>
            <div style={{ display: 'flex', gap: '12px', marginTop: '4px' }}>
              {(['survey', 'drydock'] as const).map((rt) => (
                <label
                  key={rt}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 14px',
                    borderRadius: '6px',
                    border: `1.5px solid ${reportType === rt ? 'var(--accent)' : 'var(--border)'}`,
                    backgroundColor: reportType === rt ? 'var(--accent-dim)' : 'var(--bg-secondary)',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: reportType === rt ? 600 : 400,
                    color: reportType === rt ? 'var(--accent)' : 'var(--text-secondary)',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <input
                    type="radio"
                    name="reportType"
                    value={rt}
                    checked={reportType === rt}
                    onChange={() => setReportType(rt)}
                    style={{ display: 'none' }}
                  />
                  {rt === 'survey' ? 'Survey Report' : 'Drydock Report'}
                </label>
              ))}
            </div>
          </div>

          {/* Node address dropdown */}
          <div>
            <label style={labelStyle}>Node *</label>
            <select
              value={nodeAddress}
              onChange={(e) => {
                setNodeAddress(e.target.value);
                if (errors.nodeAddress) setErrors({ ...errors, nodeAddress: '' });
              }}
              style={{
                ...inputStyle,
                appearance: 'none',
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23a0a0b0' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E")`,
                backgroundRepeat: 'no-repeat',
                backgroundPosition: 'right 10px center',
                paddingRight: '32px',
              }}
            >
              <option value="">Select a node...</option>
              {nodes.map((n) => (
                <option key={n.address} value={n.address}>
                  {n.name} ({n.address}:{n.port})
                </option>
              ))}
            </select>
            {errors.nodeAddress && (
              <div style={{ color: 'var(--error)', fontSize: '12px', marginTop: '4px' }}>
                {errors.nodeAddress}
              </div>
            )}
          </div>

          {/* Format radio */}
          <div>
            <label style={labelStyle}>Format *</label>
            <div style={{ display: 'flex', gap: '12px', marginTop: '4px' }}>
              {(['docx', 'json', 'pdf'] as const).map((fmt) => (
                <label
                  key={fmt}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 14px',
                    borderRadius: '6px',
                    border: `1.5px solid ${format === fmt ? 'var(--accent)' : 'var(--border)'}`,
                    backgroundColor:
                      format === fmt ? 'var(--accent-dim)' : 'var(--bg-secondary)',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: format === fmt ? 600 : 400,
                    color: format === fmt ? 'var(--accent)' : 'var(--text-secondary)',
                    fontFamily: 'var(--font-mono)',
                    textTransform: 'uppercase',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <input
                    type="radio"
                    name="format"
                    value={fmt}
                    checked={format === fmt}
                    onChange={() => {
                      setFormat(fmt);
                      if (errors.format) setErrors({ ...errors, format: '' });
                    }}
                    style={{ display: 'none' }}
                  />
                  {fmt}
                </label>
              ))}
            </div>
            {errors.format && (
              <div style={{ color: 'var(--error)', fontSize: '12px', marginTop: '4px' }}>
                {errors.format}
              </div>
            )}
          </div>

          {/* Log Root (optional, for PDF from log files) */}
          <div>
            <label style={labelStyle}>Log Root (optional — for PDF from log files)</label>
            <input
              type="text"
              value={logRoot}
              onChange={(e) => setLogRoot(e.target.value)}
              style={inputStyle}
              placeholder="/path/to/log/files"
            />
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
              When set with PDF format, reports are generated from .fbc/.rpc/.log/.lis files in this directory.
            </div>
          </div>

          {/* Template (optional) */}
          <div>
            <label style={labelStyle}>Template (optional)</label>
            <input
              type="text"
              value={template}
              onChange={(e) => setTemplate(e.target.value)}
              style={inputStyle}
              placeholder="default"
            />
          </div>

          {/* Title (optional) */}
          <div>
            <label style={labelStyle}>Title (optional)</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={inputStyle}
              placeholder="Report title"
            />
          </div>

          {/* Author (optional) */}
          <div>
            <label style={labelStyle}>Author (optional)</label>
            <input
              type="text"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              style={inputStyle}
              placeholder="Author name"
            />
          </div>

          {/* Submit error */}
          {submitError && (
            <div
              style={{
                color: 'var(--error)',
                fontSize: '13px',
                padding: '8px 12px',
                backgroundColor: 'rgba(239,68,68,0.1)',
                borderRadius: '6px',
              }}
            >
              {submitError}
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '4px' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onCancel}
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting || nodes.length === 0}
            >
              {submitting ? (
                <>
                  <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                  Generating...
                </>
              ) : (
                'Generate Report'
              )}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: '12px',
  fontWeight: 500,
  color: 'var(--text-secondary)',
  marginBottom: '4px',
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '8px 10px',
  backgroundColor: 'var(--bg-secondary)',
  border: '1px solid var(--border)',
  borderRadius: '6px',
  color: 'var(--text-primary)',
  fontSize: '14px',
  fontFamily: 'var(--font-sans)',
  outline: 'none',
};
