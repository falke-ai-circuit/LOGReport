import { useState, useEffect, useCallback } from 'react';
import { Ship, FolderPlus, FileText, Server, Loader2, Plus, ArrowRight } from 'lucide-react';

interface Project {
  id: number;
  project_number: string;
  ship_name: string;
  log_root: string;
  status: string;
  created_at: string;
  updated_at: string;
}

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

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newProject, setNewProject] = useState({ project_number: '', ship_name: '', log_root: '' });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
        // try /health
        const r2 = await fetch('/health');
        if (r2.ok) setHealth(await r2.json());
        return;
      }
      setHealth(await res.json());
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    fetchProjects();
    fetchHealth();
  }, [fetchProjects, fetchHealth]);

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
        body: JSON.stringify(newProject),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      const created = await res.json().catch(() => null);
      setShowCreate(false);
      setNewProject({ project_number: '', ship_name: '', log_root: '' });
      fetchProjects();
      // If the API returns the created project id, link to Commander with that project
      if (created && created.id) {
        localStorage.setItem('activeProjectId', String(created.id));
        window.location.href = `/commander?project_id=${created.id}`;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project');
    } finally {
      setCreating(false);
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
          label="DB Status"
          value={health?.db_status || 'unknown'}
          color="var(--text-secondary)"
        />
      </div>

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
              display: 'flex',
              gap: '12px',
              flexWrap: 'wrap',
              alignItems: 'flex-end',
            }}
          >
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
              <ProjectCard key={p.id} project={p} />
            ))}
          </div>
        )}
      </div>

      {/* Quick actions */}
      <div>
        <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '12px' }}>Quick Actions</h2>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <QuickAction
            icon={<FolderPlus size={18} />}
            label="Ingest Sys Files"
            description="Scan BU directory and load nodes"
            href="/sysfile"
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
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────

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

function ProjectCard({ project }: { project: Project }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '12px 16px',
        backgroundColor: 'var(--bg-secondary)',
        borderRadius: '8px',
        border: '1px solid var(--border)',
        transition: 'border-color 0.15s ease',
      }}
      onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--accent)'; }}
      onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'; }}
    >
      <Ship size={18} color="var(--accent)" style={{ flexShrink: 0 }} />
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: '14px', fontWeight: 600 }}>
          {project.project_number} — {project.ship_name}
        </div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          {project.log_root || 'No log root set'} · {project.status} · {new Date(project.created_at).toLocaleDateString()}
        </div>
      </div>
      <a
        href={`/commander?project_id=${project.id}`}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          fontSize: '12px',
          color: 'var(--accent)',
          textDecoration: 'none',
        }}
      >
        Open <ArrowRight size={14} />
      </a>
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