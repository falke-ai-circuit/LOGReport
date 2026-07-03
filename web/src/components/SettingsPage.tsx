import { useState, useEffect, useCallback } from 'react';
import { Settings as SettingsIcon, Save, Loader2, Server, Network, FolderOpen, CheckCircle } from 'lucide-react';

interface SettingsData {
  dia_host: string;
  dia_port: number;
  bstool_host: string;
  bstool_port: number;
  log_root: string;
  logroot_name: string;
  bstool_path: string;
  communication_line: string;
  output_dir: string;
  lis_mode: string;
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSettings = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/settings');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setSettings(data.settings);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  async function handleSave() {
    if (!settings) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const res = await fetch('/api/v1/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Save failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
      // Also update localStorage for frontend components
      if (settings.log_root) {
        localStorage.setItem('logRoot', settings.log_root);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  }

  function updateField(field: keyof SettingsData, value: string | number) {
    if (!settings) return;
    setSettings({ ...settings, [field]: value });
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
        <Loader2 size={24} color="var(--accent)" className="spin" />
      </div>
    );
  }

  if (!settings) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: 'var(--error)' }}>
        {error || 'Failed to load settings'}
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <SettingsIcon size={24} color="var(--accent)" />
        <h1 style={{ fontSize: '20px', fontWeight: 700 }}>Settings</h1>
        {saved && (
          <span style={{ fontSize: '12px', color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '4px', marginLeft: 'auto' }}>
            <CheckCircle size={14} /> Saved
          </span>
        )}
      </div>

      {error && (
        <div style={{ padding: '8px 12px', marginBottom: '16px', backgroundColor: 'rgba(239,68,68,0.1)', border: '1px solid var(--error)', borderRadius: '6px', fontSize: '12px', color: 'var(--error)' }}>
          {error}
        </div>
      )}

      {/* DIA Settings */}
      <SettingsSection title="DIA Debugger" icon={<Server size={16} />}>
        <FormField label="DIA Host" hint="IP address of the DIA debugger">
          <input
            type="text"
            value={settings.dia_host}
            onChange={(e) => updateField('dia_host', e.target.value)}
            placeholder="127.0.0.1"
            style={inputStyle}
          />
        </FormField>
        <FormField label="DIA Port" hint="Telnet port for DIA (default 1234)">
          <input
            type="number"
            value={settings.dia_port}
            onChange={(e) => updateField('dia_port', parseInt(e.target.value) || 0)}
            placeholder="1234"
            style={inputStyle}
          />
        </FormField>
      </SettingsSection>

      {/* BsTool Settings */}
      <SettingsSection title="BsTool" icon={<Network size={16} />}>
        <FormField label="BsTool Host" hint="IP address for BsTool TCP connection">
          <input
            type="text"
            value={settings.bstool_host}
            onChange={(e) => updateField('bstool_host', e.target.value)}
            placeholder="127.0.0.1"
            style={inputStyle}
          />
        </FormField>
        <FormField label="BsTool Port" hint="TCP port for BsTool (default 1516)">
          <input
            type="number"
            value={settings.bstool_port}
            onChange={(e) => updateField('bstool_port', parseInt(e.target.value) || 0)}
            placeholder="1516"
            style={inputStyle}
          />
        </FormField>
        <FormField label="BsTool Path" hint="Path to BsTool.exe (optional, for local execution)">
          <input
            type="text"
            value={settings.bstool_path}
            onChange={(e) => updateField('bstool_path', e.target.value)}
            placeholder="C:\\dna\\CA\\bstool\\BsTool.exe"
            style={inputStyle}
          />
        </FormField>
        <FormField label="Communication Line" hint="COMMUNICATION_LINE env var (BU hostname)">
          <input
            type="text"
            value={settings.communication_line}
            onChange={(e) => updateField('communication_line', e.target.value)}
            placeholder="EAS-C2023"
            style={inputStyle}
          />
        </FormField>
      </SettingsSection>

      {/* LIS Capture Mode */}
      <SettingsSection title="LIS Capture Mode" icon={<Network size={16} />}>
        <FormField label="LIS Capture Method" hint="How AL node LIS frames are captured: RSU6 (DIA telnet), LisDiag (direct telnet port 4321), or DiagLIS (manual)">
          <select
            value={settings.lis_mode || 'rsu'}
            onChange={(e) => updateField('lis_mode', e.target.value)}
            style={inputStyle}
          >
            <option value="rsu">RSU6 via DIA (requires RSU6 hardware)</option>
            <option value="lisdiag">LisDiag Telnet (direct, no RSU6 needed)</option>
            <option value="diaglis">DiagLIS Manual (skip automated capture)</option>
          </select>
        </FormField>
      </SettingsSection>

      {/* Log Settings */}
      <SettingsSection title="Log Storage" icon={<FolderOpen size={16} />}>
        <FormField label="Log Root Directory" hint="Where log files are written/read">
          <input
            type="text"
            value={settings.log_root}
            onChange={(e) => updateField('log_root', e.target.value)}
            placeholder="C:\\temp\\logreport-output"
            style={inputStyle}
          />
        </FormField>
        <FormField label="Log Root Folder Name" hint="Name of the wrapper folder inside log root (default: _LOG). Structure: {log_root}/{logroot_name}/{station}/{type}/{file}">
          <input
            type="text"
            value={settings.logroot_name}
            onChange={(e) => updateField('logroot_name', e.target.value)}
            placeholder="_LOG"
            style={inputStyle}
          />
        </FormField>
        <FormField label="Report Output Directory" hint="Where generated reports are saved">
          <input
            type="text"
            value={settings.output_dir}
            onChange={(e) => updateField('output_dir', e.target.value)}
            placeholder="C:\\temp\\logreport-reports"
            style={inputStyle}
          />
        </FormField>
      </SettingsSection>

      {/* Save button */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
        <button
          className="btn btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', padding: '8px 20px' }}
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? <Loader2 size={16} className="spin" /> : <Save size={16} />}
          Save Settings
        </button>
      </div>
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────

function SettingsSection({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <span style={{ color: 'var(--accent)' }}>{icon}</span>
        <h2 style={{ fontSize: '14px', fontWeight: 600 }}>{title}</h2>
      </div>
      <div style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: '8px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {children}
      </div>
    </div>
  );
}

function FormField({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      <label style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-secondary)' }}>{label}</label>
      {children}
      {hint && <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{hint}</span>}
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
  width: '100%',
  boxSizing: 'border-box',
};