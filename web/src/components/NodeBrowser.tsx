import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Server, Search, Plus, X, Loader2 } from 'lucide-react';
import type { ApiNode, NodeListResponse, ConnectRequest } from '../types/api';

const STATUS_COLORS: Record<string, string> = {
  connected: 'var(--success)',
  disconnected: 'var(--error)',
  unknown: 'var(--text-muted)',
  error: 'var(--error)',
};

export default function NodeBrowser() {
  const navigate = useNavigate();

  // Node list state
  const [nodes, setNodes] = useState<ApiNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search/filter
  const [search, setSearch] = useState('');

  // Connect form
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<ConnectRequest>({
    address: '',
    port: 23,
    name: '',
    node_type: '',
    token: '',
    username: '',
    password: '',
  });
  const [connecting, setConnecting] = useState(false);
  const [connectError, setConnectError] = useState<string | null>(null);

  // Fetch nodes
  useEffect(() => {
    let cancelled = false;

    async function fetchNodes() {
      setLoading(true);
      setError(null);
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
          setError(err instanceof Error ? err.message : 'Failed to load nodes');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchNodes();
    return () => { cancelled = true; };
  }, []);

  // Filtered nodes
  const filtered = nodes.filter((n) => {
    const q = search.toLowerCase();
    return (
      n.name.toLowerCase().includes(q) ||
      n.address.toLowerCase().includes(q) ||
      n.node_type.toLowerCase().includes(q)
    );
  });

  // Connect handler
  async function handleConnect(e: React.FormEvent) {
    e.preventDefault();
    setConnecting(true);
    setConnectError(null);
    try {
      const res = await fetch('/api/v1/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Connection failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      // Refresh node list
      const listRes = await fetch('/api/v1/nodes');
      const listData: NodeListResponse = await listRes.json();
      setNodes(listData.nodes ?? []);
      setShowForm(false);
      setForm({
        address: '',
        port: 23,
        name: '',
        node_type: '',
        token: '',
        username: '',
        password: '',
      });
    } catch (err) {
      setConnectError(err instanceof Error ? err.message : 'Connection failed');
    } finally {
      setConnecting(false);
    }
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
          <Server size={24} color="var(--accent)" />
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Node Browser</h1>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          <Plus size={16} />
          Add Node
        </button>
      </div>

      {/* Search bar */}
      <div style={{ marginBottom: '16px', position: 'relative' }}>
        <Search
          size={16}
          color="var(--text-muted)"
          style={{ position: 'absolute', left: '12px', top: '10px' }}
        />
        <input
          type="text"
          placeholder="Search by name, address, or type..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            width: '100%',
            padding: '10px 12px 10px 36px',
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            color: 'var(--text-primary)',
            fontSize: '14px',
            fontFamily: 'var(--font-sans)',
            outline: 'none',
          }}
        />
      </div>

      {/* Connect form modal */}
      {showForm && (
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
            if (e.target === e.currentTarget) setShowForm(false);
          }}
        >
          <div
            className="card-elevated"
            style={{ width: '420px', maxWidth: '90vw', padding: '24px' }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '16px',
              }}
            >
              <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Connect Node</h2>
              <button
                className="btn btn-ghost"
                onClick={() => setShowForm(false)}
                style={{ padding: '4px' }}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleConnect} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={labelStyle}>Address *</label>
                <input
                  type="text"
                  required
                  value={form.address}
                  onChange={(e) => setForm({ ...form, address: e.target.value })}
                  style={inputStyle}
                  placeholder="e.g. 192.168.1.100"
                />
              </div>
              <div style={{ display: 'flex', gap: '12px' }}>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>Port</label>
                  <input
                    type="number"
                    value={form.port}
                    onChange={(e) => setForm({ ...form, port: Number(e.target.value) || 23 })}
                    style={inputStyle}
                  />
                </div>
                <div style={{ flex: 2 }}>
                  <label style={labelStyle}>Name *</label>
                  <input
                    type="text"
                    required
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    style={inputStyle}
                    placeholder="Node display name"
                  />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '12px' }}>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>Type</label>
                  <input
                    type="text"
                    value={form.node_type}
                    onChange={(e) => setForm({ ...form, node_type: e.target.value })}
                    style={inputStyle}
                    placeholder="e.g. ACN, CIS"
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>Token</label>
                  <input
                    type="text"
                    value={form.token}
                    onChange={(e) => setForm({ ...form, token: e.target.value })}
                    style={inputStyle}
                    placeholder="Node token"
                  />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '12px' }}>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>Username</label>
                  <input
                    type="text"
                    value={form.username}
                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                    style={inputStyle}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>Password</label>
                  <input
                    type="password"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    style={inputStyle}
                  />
                </div>
              </div>

              {connectError && (
                <div
                  style={{
                    color: 'var(--error)',
                    fontSize: '13px',
                    padding: '8px 12px',
                    backgroundColor: 'rgba(239,68,68,0.1)',
                    borderRadius: '6px',
                  }}
                >
                  {connectError}
                </div>
              )}

              <button
                type="submit"
                className="btn btn-primary"
                disabled={connecting}
                style={{ justifyContent: 'center', marginTop: '4px' }}
              >
                {connecting ? (
                  <>
                    <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                    Connecting...
                  </>
                ) : (
                  'Connect'
                )}
              </button>
            </form>
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
          <p style={{ color: 'var(--text-secondary)' }}>Loading nodes...</p>
        </div>
      )}

      {/* Error state */}
      {!loading && error && (
        <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
          <p style={{ color: 'var(--error)', marginBottom: '12px' }}>{error}</p>
          <button className="btn btn-secondary" onClick={() => window.location.reload()}>
            Retry
          </button>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && nodes.length === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
          <Server size={32} color="var(--text-muted)" style={{ marginBottom: '12px' }} />
          <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
            No nodes configured. Add a node to get started.
          </p>
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            <Plus size={16} />
            Add Node
          </button>
        </div>
      )}

      {/* Node list */}
      {!loading && !error && nodes.length > 0 && (
        <>
          {filtered.length === 0 && search && (
            <div className="card" style={{ textAlign: 'center', padding: '32px', marginBottom: '16px' }}>
              <p style={{ color: 'var(--text-secondary)' }}>
                No nodes match "{search}".
              </p>
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {filtered.map((node) => (
              <div
                key={node.address}
                className="card"
                onClick={() => navigate(`/nodes/${encodeURIComponent(node.address)}`)}
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
                  {/* Status dot */}
                  <span
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: STATUS_COLORS[node.status] || 'var(--text-muted)',
                      flexShrink: 0,
                    }}
                  />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '14px' }}>
                      {node.name}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                      {node.address}:{node.port}
                    </div>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div
                    style={{
                      fontSize: '11px',
                      color: 'var(--accent)',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 500,
                    }}
                  >
                    {node.node_type}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {node.last_connected
                      ? new Date(node.last_connected).toLocaleString()
                      : 'never'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
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
