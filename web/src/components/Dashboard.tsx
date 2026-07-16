import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Ship, FolderPlus, FileText, Server, Loader2, Plus, ArrowRight, Trash2, CheckCircle, Settings, Activity, Zap, FileCheck, AlertCircle, Clock, Download, Upload } from 'lucide-react';
import { useActiveProject, type Project } from '../hooks/useActiveProject';

interface ProjectsResponse {
  projects: Project[];
  total: number;
}

interface HealthStatus {
  status: string;
  version: string;
  uptime: string;
  db_status: string;
  node_count: number;
}

interface ReportItem {
  id: string;
  node_address: string;
  title: string;
  status: string;
  format: string;
  created_at: string;
  completed_at: string;
  file_path: string;
  project_id: number;
}

interface ReportsResponse {
  reports: ReportItem[];
  total: number;
}

interface SettingsData {
  dia_host: string;
  dia_port: number;
  bstool_host: string;
  bstool_port: number;
  communication_line: string;
  lis_mode: string;
  lisdiag_password: string;
}

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newProject, setNewProject] = useState({
    project_number: '',
    ship_name: '',
    log_root: '',
    dia_host: 'AB01',
    dia_port: 1234,
    bu_host: 'AB01',
    bu_port: 1516,
    lis_mode: 'rsu',
    lisdiag_port: 4321,
    lisdiag_password: '',
  });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const { activeProjectId, selectProject } = useActiveProject();
  const navigate = useNavigate();
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [editLogRoot, setEditLogRoot] = useState('');
  const [editMoving, setEditMoving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  const fetchProjects = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/projects');
      if (!res.ok) return;
      const data: ProjectsResponse = await res.json();
      setProjects(data.projects || []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchHealth = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/health');
      if (!res.ok) {
        const r2 = await fetch('/health');
        if (r2.ok) setHealth(await r2.json());
        return;
      }
      setHealth(await res.json());
    } catch {
      // ignore
    }
  }, []);

  const fetchReports = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/reports');
      if (!res.ok) return;
      const data: ReportsResponse = await res.json();
      setReports(data.reports || []);
    } catch {
      // ignore
    }
  }, []);

  const fetchSettings = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/settings');
      if (!res.ok) return;
      const data = await res.json();
      setSettings(data.settings);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    fetchProjects();
    fetchHealth();
    fetchReports();
    fetchSettings();
  }, [fetchProjects, fetchHealth, fetchReports, fetchSettings]);

  async function handleCreateProject() {
    if (!newProject.project_number || !newProject.ship_name) {
      setError('Project number and ship name are required');
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_number: newProject.project_number,
          ship_name: newProject.ship_name,
          log_root: newProject.log_root,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      const created: { id?: number; log_root?: string } = await res.json().catch(() => ({}));

      // Save settings with the project configuration values
      await fetch('/api/v1/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dia_host: newProject.dia_host,
          dia_port: newProject.dia_port,
          bstool_host: newProject.bu_host,
          bstool_port: newProject.bu_port,
          communication_line: newProject.bu_host,
          lis_mode: newProject.lis_mode,
          lisdiag_password: newProject.lisdiag_password,
        }),
      }).catch(() => {});

      setShowCreate(false);
      setNewProject({
        project_number: '', ship_name: '', log_root: '',
        dia_host: 'AB01', dia_port: 1234, bu_host: 'AB01', bu_port: 1516,
        lis_mode: 'rsu', lisdiag_port: 4321, lisdiag_password: '',
      });
      await fetchProjects();
      if (created && created.id) {
        selectProject(created.id, created.log_root || newProject.log_root || '');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project');
    } finally {
      setCreating(false);
    }
  }

  async function handleDeleteProject(id: number, name: string) {
    if (!window.confirm(`Delete project "${name}"? This will also delete all its nodes and reports. This cannot be undone.`)) {
      return;
    }
    try {
      const res = await fetch(`/api/v1/projects/${id}`, {
        method: 'DELETE',
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Delete failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      fetchProjects();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete project');
    }
  }

  async function handleExportProject(id: number, projectNumber: string, shipName: string) {
    try {
      const res = await fetch(`/api/v1/projects/${id}/export`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Export failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${projectNumber}_${shipName}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export project');
    }
  }

  async function handleImportProject(file: File) {
    setCreating(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/v1/projects/import', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Import failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      await fetchProjects();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import project');
    } finally {
      setCreating(false);
    }
  }

  function handleEditProject(project: Project) {
    setEditingProject(project);
    setEditLogRoot(project.log_root || '');
    setEditError(null);
  }

  async function handleSaveEdit() {
    if (!editingProject) return;
    setEditMoving(true);
    setEditError(null);
    try {
      const res = await fetch(`/api/v1/projects/${editingProject.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_number: editingProject.project_number,
          ship_name: editingProject.ship_name,
          log_root: editLogRoot,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Update failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      const data: { project?: { id: number; log_root: string } } = await res.json();
      // If log_root changed and project is active, update the active log root
      if (data.project && data.project.log_root && data.project.id === activeProjectId) {
        selectProject(data.project.id, data.project.log_root);
      }
      setEditingProject(null);
      fetchProjects();
    } catch (err) {
      setEditError(err instanceof Error ? err.message : 'Failed to update project');
    } finally {
      setEditMoving(false);
    }
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700 }}>
          LOGReport Dashboard
        </h1>
        {health && (
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: 'auto' }}>
            {health.status === 'ok' ? '🟢' : '🔴'} {health.version} · {health.uptime}
          </span>
        )}
      </div>

      {/* Stats row */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <StatCard
          icon={<Ship size={20} />}
          label="Projects"
          value={projects.length}
          color="var(--accent)"
        />
        <StatCard
          icon={<Server size={20} />}
          label="Nodes"
          value={health?.node_count || 0}
          color="var(--success)"
        />
        <StatCard
          icon={<FileText size={20} />}
          label="Reports"
          value={reports.length}
          color="#f59e0b"
        />
        <StatCard
          icon={<Activity size={20} />}
          label="DB Status"
          value={health?.db_status || 'unknown'}
          color="var(--text-secondary)"
        />
      </div>

      {/* Active Project Panel */}
      {activeProjectId && projects.find(p => p.id === activeProjectId) && (
        <ActiveProjectPanel
          project={projects.find(p => p.id === activeProjectId)!}
          nodeCount={health?.node_count || 0}
          reportCount={reports.filter(r => r.project_id === activeProjectId).length}
          settings={settings}
          onCommander={() => navigate('/commander')}
          onNodes={() => navigate('/nodes')}
          onReports={() => navigate('/reports')}
        />
      )}

      {/* Latest Ships & Projects */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <Ship size={18} color="var(--accent)" />
          <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Latest Ships & Projects</h2>
          <button
            className="btn btn-primary"
            style={{ fontSize: '12px', padding: '4px 10px', marginLeft: 'auto' }}
            onClick={() => setShowCreate(!showCreate)}
          >
            <Plus size={14} />
            New Project
          </button>
          <label
            className="btn btn-ghost"
            style={{ fontSize: '12px', padding: '4px 10px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--accent)' }}
            title="Import project from zip file"
          >
            <Upload size={14} />
            Import
            <input
              type="file"
              accept=".zip"
              style={{ display: 'none' }}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleImportProject(file);
                e.target.value = '';
              }}
            />
          </label>
        </div>

        {/* Create form */}
        {showCreate && (
          <div
            style={{
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '12px',
            }}
          >
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: '12px' }}>
              <FormField label="Project Number" required>
                <input
                  type="text"
                  value={newProject.project_number}
                  onChange={(e) => setNewProject({ ...newProject, project_number: e.target.value })}
                  placeholder="T6004"
                  style={inputStyle}
                />
              </FormField>
              <FormField label="Ship Name" required>
                <input
                  type="text"
                  value={newProject.ship_name}
                  onChange={(e) => setNewProject({ ...newProject, ship_name: e.target.value })}
                  placeholder="ADORA_MEDITERANNEA"
                  style={inputStyle}
                />
              </FormField>
              <FormField label="Log Root">
                <input
                  type="text"
                  value={newProject.log_root}
                  onChange={(e) => setNewProject({ ...newProject, log_root: e.target.value })}
                  placeholder="C:\dna\CA\bu"
                  style={inputStyle}
                />
              </FormField>
            </div>
            {/* Connection Settings */}
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: '12px', marginBottom: '12px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>Connection Settings (auto-saved to Settings)</div>
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
                <FormField label="DIA Host">
                  <input
                    type="text"
                    list="dia-host-options"
                    value={newProject.dia_host}
                    onChange={(e) => setNewProject({ ...newProject, dia_host: e.target.value })}
                    style={inputStyle}
                  />
                  <datalist id="dia-host-options">
                    <option value="AB01" />
                    <option value="AB02" />
                    <option value="AB03" />
                    <option value="127.0.0.1" />
                  </datalist>
                </FormField>
                <FormField label="DIA Port">
                  <input
                    type="number"
                    list="dia-port-options"
                    value={newProject.dia_port}
                    onChange={(e) => setNewProject({ ...newProject, dia_port: Number(e.target.value) || 1234 })}
                    style={inputStyle}
                  />
                  <datalist id="dia-port-options">
                    <option value={1234} />
                    <option value={1235} />
                  </datalist>
                </FormField>
                <FormField label="BU Host (BsTool)">
                  <input
                    type="text"
                    list="bu-host-options"
                    value={newProject.bu_host}
                    onChange={(e) => setNewProject({ ...newProject, bu_host: e.target.value })}
                    style={inputStyle}
                  />
                  <datalist id="bu-host-options">
                    <option value="AB01" />
                    <option value="AB02" />
                    <option value="AB03" />
                    <option value="127.0.0.1" />
                  </datalist>
                </FormField>
                <FormField label="BU Port">
                  <input
                    type="number"
                    list="bu-port-options"
                    value={newProject.bu_port}
                    onChange={(e) => setNewProject({ ...newProject, bu_port: Number(e.target.value) || 1516 })}
                    style={inputStyle}
                  />
                  <datalist id="bu-port-options">
                    <option value={1516} />
                    <option value={1517} />
                  </datalist>
                </FormField>
                <FormField label="LIS Mode">
                  <select
                    value={newProject.lis_mode}
                    onChange={(e) => setNewProject({ ...newProject, lis_mode: e.target.value })}
                    style={inputStyle}
                  >
                    <option value="rsu">RSU6 (via DIA)</option>
                    <option value="lisdiag">LisDiag (telnet)</option>
                    <option value="diaglis">DiagLis (manual)</option>
                  </select>
                </FormField>
                <FormField label="LISDiag Port">
                  <input
                    type="number"
                    list="lisdiag-port-options"
                    value={newProject.lisdiag_port}
                    onChange={(e) => setNewProject({ ...newProject, lisdiag_port: Number(e.target.value) || 4321 })}
                    style={inputStyle}
                  />
                  <datalist id="lisdiag-port-options">
                    <option value={4321} />
                    <option value={14321} />
                  </datalist>
                </FormField>
                <FormField label="LISDiag Password">
                  <input
                    type="password"
                    value={newProject.lisdiag_password}
                    onChange={(e) => setNewProject({ ...newProject, lisdiag_password: e.target.value })}
                    placeholder="(none = no auth)"
                    style={inputStyle}
                  />
                </FormField>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <button
                className="btn btn-primary"
                style={{ fontSize: '12px', padding: '6px 16px' }}
                onClick={handleCreateProject}
                disabled={creating}
              >
                {creating ? <Loader2 size={14} className="spin" /> : 'Create'}
              </button>
              {error && <span style={{ fontSize: '11px', color: 'var(--error)' }}>{error}</span>}
            </div>
          </div>
        )}

        {/* Projects list */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '24px' }}>
            <Loader2 size={20} color="var(--accent)" className="spin" />
          </div>
        ) : projects.length === 0 ? (
          <div
            style={{
              padding: '24px',
              textAlign: 'center',
              color: 'var(--text-muted)',
              fontSize: '13px',
              backgroundColor: 'var(--bg-secondary)',
              borderRadius: '8px',
              border: '1px solid var(--border)',
            }}
          >
            No projects yet. Create a project to get started.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {projects.map((p) => (
              <ProjectCard
                key={p.id}
                project={p}
                isActive={p.id === activeProjectId}
                onSelect={() => { selectProject(p.id, p.log_root || ''); navigate('/nodes'); }}
                onDelete={() => handleDeleteProject(p.id, `${p.project_number} — ${p.ship_name}`)}
                onEdit={() => handleEditProject(p)}
                onExport={() => handleExportProject(p.id, p.project_number, p.ship_name)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Quick actions */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '12px' }}>Quick Actions</h2>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <QuickAction
            icon={<FolderPlus size={18} />}
            label="Ingest Sys Files"
            description="Scan BU directory and load nodes"
            href="/nodes"
          />
          <QuickAction
            icon={<Server size={18} />}
            label="Commander"
            description="Interactive command center"
            href="/commander"
          />
          <QuickAction
            icon={<FileText size={18} />}
            label="Reports"
            description="View and generate reports"
            href="/reports"
          />
        </div>
      </div>

      {/* Recent Reports */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <FileCheck size={18} color="#f59e0b" />
          <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Recent Reports</h2>
          {reports.length > 0 && (
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: 'auto' }}>
              {reports.length} total
            </span>
          )}
        </div>
        {reports.length === 0 ? (
          <div
            style={{
              padding: '20px',
              textAlign: 'center',
              color: 'var(--text-muted)',
              fontSize: '12px',
              backgroundColor: 'var(--bg-secondary)',
              borderRadius: '8px',
              border: '1px solid var(--border)',
            }}
          >
            No reports generated yet.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {reports.slice(0, 5).map((r) => (
              <ReportRow key={r.id} report={r} projectName={projects.find(p => p.id === r.project_id)?.project_number} />
            ))}
          </div>
        )}
      </div>
      {/* Edit Project Dialog */}
      {editingProject && (
        <div
          style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200 }}
          onClick={(e) => { if (e.target === e.currentTarget) setEditingProject(null); }}
        >
          <div style={{ width: '500px', backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: '8px', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
              <Settings size={16} color="var(--accent)" />
              <span style={{ fontSize: '14px', fontWeight: 600 }}>Edit Project: {editingProject.project_number} — {editingProject.ship_name}</span>
              <button className="btn btn-ghost" style={{ fontSize: '14px', padding: '2px 8px', marginLeft: 'auto' }} onClick={() => setEditingProject(null)}>✕</button>
            </div>
            <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Project Number</label>
                <input
                  type="text"
                  value={editingProject.project_number}
                  readOnly
                  style={{ ...inputStyle, width: '100%', opacity: 0.6 }}
                />
              </div>
              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Ship Name</label>
                <input
                  type="text"
                  value={editingProject.ship_name}
                  readOnly
                  style={{ ...inputStyle, width: '100%', opacity: 0.6 }}
                />
              </div>
              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Log Root <span style={{ color: 'var(--accent)' }}>(change to move files)</span></label>
                <input
                  type="text"
                  value={editLogRoot}
                  onChange={(e) => setEditLogRoot(e.target.value)}
                  placeholder="C:\dna\CA\bu"
                  style={{ ...inputStyle, width: '100%' }}
                />
                <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Current: {editingProject.log_root || '(none)'}
                  {editLogRoot !== editingProject.log_root && editLogRoot && (
                    <span style={{ color: '#f59e0b', marginLeft: '8px' }}>⚠ Files will need to be moved manually or via Create Structure</span>
                  )}
                </div>
              </div>
              {editError && <div style={{ fontSize: '11px', color: 'var(--error)' }}>{editError}</div>}
            </div>
            <div style={{ display: 'flex', gap: '8px', padding: '12px 16px', borderTop: '1px solid var(--border)', justifyContent: 'flex-end' }}>
              <button className="btn btn-ghost" style={{ fontSize: '12px', padding: '6px 16px' }} onClick={() => setEditingProject(null)}>Cancel</button>
              <button className="btn btn-primary" style={{ fontSize: '12px', padding: '6px 16px' }} onClick={handleSaveEdit} disabled={editMoving}>
                {editMoving ? <Loader2 size={14} className="spin" /> : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: number | string; color: string }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '16px 20px',
        backgroundColor: 'var(--bg-secondary)',
        borderRadius: '8px',
        border: '1px solid var(--border)',
        minWidth: '160px',
      }}
    >
      <div style={{ color }}>{icon}</div>
      <div>
        <div style={{ fontSize: '20px', fontWeight: 700 }}>{value}</div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{label}</div>
      </div>
    </div>
  );
}

function ProjectCard({ project, isActive, onSelect, onDelete, onEdit, onExport }: { project: Project; isActive: boolean; onSelect: () => void; onDelete: () => void; onEdit: () => void; onExport: () => void }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '12px 16px',
        backgroundColor: isActive ? 'rgba(99,102,241,0.08)' : 'var(--bg-secondary)',
        borderRadius: '8px',
        border: isActive ? '1px solid var(--accent)' : '1px solid var(--border)',
        transition: 'border-color 0.15s ease',
        cursor: 'pointer',
      }}
      onClick={onSelect}
      onMouseEnter={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.borderColor = 'var(--accent)'; }}
      onMouseLeave={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'; }}
    >
      {isActive ? <CheckCircle size={18} color="var(--accent)" style={{ flexShrink: 0 }} /> : <Ship size={18} color="var(--accent)" style={{ flexShrink: 0 }} />}
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: '14px', fontWeight: 600 }}>
          {project.project_number} — {project.ship_name}
          {isActive && <span style={{ fontSize: '10px', color: 'var(--accent)', marginLeft: '8px' }}>ACTIVE</span>}
        </div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          {project.log_root || 'No log root set'} · {project.status}
          {project.updated_at && project.updated_at !== project.created_at && (
            <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
              · <Clock size={10} /> {new Date(project.updated_at).toLocaleDateString()}
            </span>
          )}
        </div>
      </div>
      <span
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          fontSize: '12px',
          color: 'var(--accent)',
        }}
      >
        Open <ArrowRight size={14} />
      </span>
      <button
        className="btn btn-ghost"
        style={{
          fontSize: '12px',
          padding: '4px 8px',
          color: 'var(--text-secondary)',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
        }}
        onClick={(e) => { e.stopPropagation(); onEdit(); }}
        title="Edit project (change log root, move files)"
      >
        <Settings size={14} />
        Edit
      </button>
      <button
        className="btn btn-ghost"
        style={{
          fontSize: '12px',
          padding: '4px 8px',
          color: 'var(--accent)',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
        }}
        onClick={(e) => { e.stopPropagation(); onExport(); }}
        title="Export project folder as zip"
      >
        <Download size={14} />
        Export
      </button>
      <button
        className="btn btn-ghost"
        style={{
          fontSize: '12px',
          padding: '4px 8px',
          color: 'var(--error)',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
        }}
        onClick={(e) => { e.stopPropagation(); onDelete(); }}
        title="Delete this project"
      >
        <Trash2 size={14} />
        Delete
      </button>
    </div>
  );
}

function QuickAction({ icon, label, description, href }: { icon: React.ReactNode; label: string; description: string; href: string }) {
  return (
    <a
      href={href}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '16px 20px',
        backgroundColor: 'var(--bg-secondary)',
        borderRadius: '8px',
        border: '1px solid var(--border)',
        textDecoration: 'none',
        color: 'var(--text-primary)',
        minWidth: '200px',
        transition: 'border-color 0.15s ease',
      }}
      onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--accent)'; }}
      onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'; }}
    >
      <div style={{ color: 'var(--accent)' }}>{icon}</div>
      <div>
        <div style={{ fontSize: '13px', fontWeight: 600 }}>{label}</div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{description}</div>
      </div>
    </a>
  );
}

function FormField({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      <label style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
        {label}{required && <span style={{ color: 'var(--error)' }}> *</span>}
      </label>
      {children}
    </div>
  );
}

// ─── Active Project Panel ────────────────────────────────────────────

function ActiveProjectPanel({ project, nodeCount, reportCount, settings, onCommander, onNodes, onReports }: {
  project: Project;
  nodeCount: number;
  reportCount: number;
  settings: SettingsData | null;
  onCommander: () => void;
  onNodes: () => void;
  onReports: () => void;
}) {
  const lisModeLabel = settings?.lis_mode === 'rsu' ? 'RSU6' : settings?.lis_mode === 'lisdiag' ? 'LisDiag' : settings?.lis_mode === 'diaglis' ? 'DiagLis' : '—';
  const diaConfigured = settings?.dia_host && settings.dia_host !== '';
  const buConfigured = settings?.bstool_host && settings.bstool_host !== '';
  const lisConfigured = settings?.lis_mode && settings.lis_mode !== '';

  return (
    <div
      style={{
        backgroundColor: 'rgba(99,102,241,0.06)',
        border: '1px solid var(--accent)',
        borderRadius: '8px',
        padding: '16px 20px',
        marginBottom: '24px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <CheckCircle size={18} color="var(--accent)" />
        <span style={{ fontSize: '16px', fontWeight: 700 }}>
          {project.project_number} — {project.ship_name}
        </span>
        <span style={{ fontSize: '10px', color: 'var(--accent)', backgroundColor: 'rgba(99,102,241,0.15)', padding: '2px 8px', borderRadius: '4px' }}>
          ACTIVE
        </span>
      </div>

      {/* Info row */}
      <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap', marginBottom: '12px' }}>
        <InfoItem label="Log Root" value={project.log_root || '—'} mono />
        <InfoItem label="Nodes" value={String(nodeCount)} />
        <InfoItem label="Reports" value={String(reportCount)} />
        <InfoItem label="Status" value={project.status} />
      </div>

      {/* Connection summary */}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '12px' }}>
        <ConnectionBadge label="DIA" host={settings?.dia_host || '—'} port={settings?.dia_port} configured={!!diaConfigured} />
        <ConnectionBadge label="BU" host={settings?.bstool_host || '—'} port={settings?.bstool_port} configured={!!buConfigured} />
        <ConnectionBadge label="LIS" host={lisModeLabel} port={undefined} configured={!!lisConfigured} />
      </div>

      {/* Quick jump buttons */}
      <div style={{ display: 'flex', gap: '8px' }}>
        <button className="btn btn-primary" style={{ fontSize: '12px', padding: '6px 14px', display: 'flex', alignItems: 'center', gap: '6px' }} onClick={onCommander}>
          <Zap size={14} /> Commander
        </button>
        <button className="btn btn-ghost" style={{ fontSize: '12px', padding: '6px 14px' }} onClick={onNodes}>
          Nodes
        </button>
        <button className="btn btn-ghost" style={{ fontSize: '12px', padding: '6px 14px' }} onClick={onReports}>
          Reports
        </button>
      </div>
    </div>
  );
}

function InfoItem({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '2px' }}>{label}</div>
      <div style={{ fontSize: '12px', fontWeight: 500, fontFamily: mono ? 'var(--font-mono)' : 'inherit' }}>{value}</div>
    </div>
  );
}

function ConnectionBadge({ label, host, port, configured }: { label: string; host: string; port?: number; configured: boolean }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '4px 10px',
        backgroundColor: configured ? 'rgba(0,138,0,0.1)' : 'rgba(120,120,120,0.1)',
        border: `1px solid ${configured ? '#008a00' : 'var(--border)'}`,
        borderRadius: '4px',
        fontSize: '11px',
      }}
    >
      <span
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: configured ? '#008a00' : 'var(--text-muted)',
        }}
      />
      <span style={{ fontWeight: 600, color: configured ? '#008a00' : 'var(--text-muted)' }}>{label}</span>
      <span style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
        {host}{port ? `:${port}` : ''}
      </span>
    </div>
  );
}

// ─── Report Row ──────────────────────────────────────────────────────

function ReportRow({ report, projectName }: { report: ReportItem; projectName?: string }) {
  const statusColor = report.status === 'completed' ? '#008a00' : report.status === 'generating' ? '#f59e0b' : report.status === 'failed' ? 'var(--error)' : 'var(--text-muted)';
  const statusIcon = report.status === 'completed' ? <FileCheck size={12} /> : report.status === 'generating' ? <Loader2 size={12} className="spin" /> : report.status === 'failed' ? <AlertCircle size={12} /> : <FileText size={12} />;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        padding: '10px 14px',
        backgroundColor: 'var(--bg-secondary)',
        borderRadius: '6px',
        border: '1px solid var(--border)',
        transition: 'border-color 0.15s ease',
        cursor: 'pointer',
      }}
      onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--accent)'; }}
      onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'; }}
      onClick={() => { /* navigate to reports page */ window.location.hash = '#/reports'; }}
    >
      <div style={{ color: statusColor, display: 'flex', alignItems: 'center' }}>{statusIcon}</div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: '12px', fontWeight: 500 }}>
          {report.title || report.format || 'Untitled'} {projectName && <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>· {projectName}</span>}
        </div>
        <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
          {report.node_address} · {new Date(report.created_at).toLocaleDateString()}
        </div>
      </div>
      <span style={{ fontSize: '10px', color: statusColor, fontWeight: 600, textTransform: 'uppercase' }}>{report.status}</span>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  fontSize: '12px',
  padding: '6px 10px',
  backgroundColor: 'var(--bg-elevated)',
  border: '1px solid var(--border)',
  borderRadius: '4px',
  color: 'var(--text-primary)',
  fontFamily: 'var(--font-mono)',
  width: '200px',
};