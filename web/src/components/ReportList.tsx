import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Plus, Loader2, AlertTriangle, FileJson, FileArchive, Trash2, RefreshCw } from 'lucide-react';
import { useActiveProject, useProjects } from '../hooks/useActiveProject';
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
  const { activeProjectId } = useActiveProject();
  const { projects } = useProjects();
  const navigate = useNavigate();
  const activeProject = projects.find((p) => p.id === activeProjectId) || null;

  // Report list state
  const [reports, setReports] = useState<ApiReport[]>([]);
  const [allReports, setAllReports] = useState<ApiReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected report for preview
  const [selectedReport, setSelectedReport] = useState<ApiReport | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  // Config modal
  const [showConfig, setShowConfig] = useState(false);

  // Right-click context menu
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; report: ApiReport } | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [deleting, setDeleting] = useState(false);

  // Close context menu on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setContextMenu(null);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  async function handleDeleteReport(reportId: string) {
    if (!window.confirm('Delete this report? The file will be removed from disk.')) return;
    setDeleting(true);
    try {
      await fetch(`/api/v1/reports/${encodeURIComponent(reportId)}`, { method: 'DELETE' });
      // Refresh list
      const res = await fetch('/api/v1/reports');
      if (res.ok) {
        const data: ReportListResponse = await res.json();
        const all = data.reports ?? [];
        setAllReports(all);
        // Filter by active project
        if (!activeProjectId) {
          setReports([]);
        } else {
          setReports(all.filter(r => (r as any).project_id === activeProjectId || !(r as any).project_id));
        }
        if (selectedReport?.report_id === reportId) {
          setSelectedReport(null);
        }
      }
    } catch { /* ignore */ } finally {
      setDeleting(false);
      setContextMenu(null);
    }
  }

  function handleRegenerateReport(report: ApiReport) {
    // Open the config modal pre-filled with the report's parameters
    setSelectedReport(report);
    setShowConfig(true);
    setContextMenu(null);
  }

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
          const all = data.reports ?? [];
          setAllReports(all);
          // Auto-select first report for preview (only if nothing selected)
          if (all.length > 0 && !selectedReport) {
            setSelectedReport(all[0]);
          }
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
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run once on mount; selectedReport checked via ref below

  // Filter reports by active project
  useEffect(() => {
    if (!activeProjectId) {
      setReports([]);
    } else {
      // Filter by project_id if available; legacy reports without project_id are included
      const filtered = allReports.filter(r => (r as any).project_id === activeProjectId || !(r as any).project_id);
      setReports(filtered);
    }
  }, [activeProjectId, allReports]);

  // Load preview when selected report changes
  useEffect(() => {
    if (!selectedReport) {
      setPreviewUrl(null);
      return;
    }
    // Only load preview for completed reports with a file path
    if (selectedReport.status === 'completed' && selectedReport.report_id) {
      setPreviewLoading(true);
      // The report file is served at /api/v1/reports/{id}
      // For PDF, we can show inline in an iframe
      // For JSON/DOCX, we show metadata or download link
      const url = `/api/v1/reports/${encodeURIComponent(selectedReport.report_id)}`;
      setPreviewUrl(url);
      setPreviewLoading(false);
    } else {
      setPreviewUrl(null);
    }
  }, [selectedReport]);

  // Refresh after generating
  const handleGenerated = useCallback((reportId: string) => {
    setShowConfig(false);
    fetch('/api/v1/reports')
      .then((res) => res.json())
      .then((data: ReportListResponse) => {
        const all = data.reports ?? [];
        setAllReports(all);
        // Filter by active project immediately to avoid flashing all reports
        if (!activeProjectId) {
          setReports([]);
        } else {
          const filtered = all.filter(r => (r as any).project_id === activeProjectId || !(r as any).project_id);
          setReports(filtered);
        }
        // Auto-select the new report
        const newReport = all.find(r => r.report_id === reportId);
        if (newReport) setSelectedReport(newReport);
      })
      .catch(() => {});
  }, [activeProjectId]);

  // Handle clicking a report in the sidebar
  function handleReportClick(report: ApiReport) {
    setSelectedReport(report);
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '8px 16px',
          borderBottom: '1px solid var(--border)',
          backgroundColor: 'var(--bg-secondary)',
          flexShrink: 0,
        }}
      >
        <FileText size={20} color="var(--accent)" />
        <h1 style={{ fontSize: '16px', fontWeight: 700 }}>Reports</h1>
        {activeProject ? (
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: '4px' }}>
            {activeProject.project_number} — {activeProject.ship_name}
          </span>
        ) : (
          <span style={{ fontSize: '11px', color: 'var(--warning)', marginLeft: '4px' }}>
            No project selected
          </span>
        )}
        <div style={{ flex: 1 }} />
        <button
          className="btn btn-primary"
          style={{ fontSize: '12px', padding: '4px 12px' }}
          onClick={() => setShowConfig(true)}
          disabled={!activeProjectId}
        >
          <Plus size={14} />
          Generate New Report
        </button>
      </div>

      {/* No project state */}
      {!activeProjectId && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: '48px', textAlign: 'center' }}>
          <FileText size={48} color="var(--text-muted)" style={{ marginBottom: '16px' }} />
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '16px' }}>
            No project selected. Select a project from the Dashboard to view and generate reports.
          </p>
          <button className="btn btn-primary" onClick={() => navigate('/')}>
            Go to Dashboard
          </button>
        </div>
      )}

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
              projectId={activeProjectId || undefined}
              logRoot={activeProject?.log_root}
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

      {/* Empty state — only show when a project IS selected but has no reports */}
      {!loading && !error && activeProjectId && reports.length === 0 && (
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

      {/* Main layout: left sidebar (30%) + right preview (70%) */}
      {!loading && !error && reports.length > 0 && (
        <div style={{ display: 'flex', flex: 1, overflow: 'auto' }}>
          {/* Left sidebar: report list */}
          <div
            style={{
              width: '30%',
              minWidth: '220px',
              maxWidth: '400px',
              borderRight: '1px solid var(--border)',
              overflow: 'auto',
              backgroundColor: 'var(--bg-secondary)',
            }}
          >
            {reports.map((report) => {
              const statusColor = STATUS_COLORS[report.status] || 'var(--text-muted)';
              const statusLabel = STATUS_LABELS[report.status] || report.status;
              const formatIcon = FORMAT_ICONS[report.format] || null;
              const isSelected = selectedReport?.report_id === report.report_id;

              return (
                <div
                  key={report.report_id}
                  onClick={() => handleReportClick(report)}
                  onContextMenu={(e) => { e.preventDefault(); setContextMenu({ x: e.clientX, y: e.clientY, report }); }}
                  style={{
                    cursor: 'pointer',
                    padding: '10px 12px',
                    borderBottom: '1px solid var(--border)',
                    backgroundColor: isSelected ? 'rgba(99,102,241,0.1)' : 'transparent',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                    transition: 'background-color 0.1s ease',
                    borderLeft: isSelected ? '3px solid var(--accent)' : '3px solid transparent',
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-elevated)';
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ color: 'var(--accent)', display: 'flex' }}>{formatIcon}</span>
                    <span style={{ fontSize: '12px', fontWeight: 600, fontFamily: 'var(--font-mono)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {report.report_id}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', paddingLeft: '22px' }}>
                    <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--accent)', backgroundColor: 'var(--accent-dim)', padding: '1px 5px', borderRadius: '3px', textTransform: 'uppercase' }}>
                      {report.format}
                    </span>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', fontSize: '10px', color: statusColor }}>
                      <span style={{ width: '5px', height: '5px', borderRadius: '50%', backgroundColor: statusColor }} />
                      {statusLabel}
                    </span>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: 'auto' }}>
                      {report.created_at ? new Date(report.created_at).toLocaleDateString() : '—'}
                    </span>
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', paddingLeft: '22px' }}>
                    {report.node_addresses?.join(', ') || '—'}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right: report preview area */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'auto', backgroundColor: 'var(--bg-primary)' }}>
            {selectedReport ? (
              <>
                {/* Preview header */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
                  <FileText size={14} color="var(--accent)" />
                  <span style={{ fontSize: '13px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{selectedReport.report_id}</span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>( {selectedReport.format?.toUpperCase()} )</span>
                  <div style={{ flex: 1 }} />
                  <span style={{ fontSize: '11px', color: STATUS_COLORS[selectedReport.status] || 'var(--text-muted)' }}>
                    {STATUS_LABELS[selectedReport.status] || selectedReport.status}
                  </span>
                </div>

                {/* Preview content */}
                <div style={{ flex: 1, overflow: 'auto' }}>
                  {previewLoading ? (
                    <div style={{ textAlign: 'center', padding: '48px' }}>
                      <Loader2 size={24} color="var(--accent)" style={{ animation: 'spin 1s linear infinite', marginBottom: '12px' }} />
                      <p style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>Loading preview...</p>
                    </div>
                  ) : selectedReport.status === 'completed' && previewUrl ? (
                    selectedReport.format === 'pdf' ? (
                      <iframe
                        src={previewUrl}
                        style={{ width: '100%', height: '100%', border: 'none', minHeight: '500px' }}
                        title={`Preview: ${selectedReport.report_id}`}
                      />
                    ) : selectedReport.format === 'json' ? (
                      <div style={{ padding: '16px' }}>
                        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                          JSON report — click to download or open in new tab:
                        </p>
                        <a href={previewUrl} target="_blank" rel="noopener noreferrer" style={{ fontSize: '13px', color: 'var(--accent)', textDecoration: 'underline' }}>
                          Open {selectedReport.report_id}.json
                        </a>
                      </div>
                    ) : selectedReport.format === 'docx' ? (
                      <div style={{ padding: '16px', textAlign: 'center' }}>
                        <FileArchive size={48} color="var(--text-muted)" style={{ marginBottom: '12px' }} />
                        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                          DOCX report — download to view:
                        </p>
                        <a href={previewUrl} target="_blank" rel="noopener noreferrer" style={{ fontSize: '13px', color: 'var(--accent)', textDecoration: 'underline' }}>
                          Download {selectedReport.report_id}.docx
                        </a>
                      </div>
                    ) : (
                      <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                        Preview not available for format: {selectedReport.format}
                      </div>
                    )
                  ) : (
                    <div style={{ padding: '48px', textAlign: 'center' }}>
                      <AlertTriangle size={32} color="var(--warning)" style={{ marginBottom: '12px' }} />
                      <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                        Report is {STATUS_LABELS[selectedReport.status] || selectedReport.status}. Preview will be available when completed.
                      </p>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                Select a report from the sidebar to preview.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Context menu for report cards */}
      {contextMenu && (
        <div
          ref={menuRef}
          style={{
            position: 'fixed',
            top: contextMenu.y,
            left: contextMenu.x,
            backgroundColor: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            borderRadius: '6px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            padding: '4px',
            zIndex: 1000,
            minWidth: '180px',
          }}
        >
          <div
            onClick={() => handleRegenerateReport(contextMenu.report)}
            style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 10px', cursor: 'pointer', borderRadius: '4px', fontSize: '12px', color: 'var(--text-primary)' }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-secondary)'; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent'; }}
          >
            <RefreshCw size={14} /> Regenerate Report
          </div>
          <div
            onClick={() => handleDeleteReport(contextMenu.report.report_id)}
            style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 10px', cursor: 'pointer', borderRadius: '4px', fontSize: '12px', color: 'var(--error)' }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-secondary)'; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent'; }}
          >
            {deleting ? <Loader2 size={14} className="spin" /> : <Trash2 size={14} />} Delete Report
          </div>
        </div>
      )}
    </div>
  );
}
