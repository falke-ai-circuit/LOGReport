import { useState, useEffect } from 'react';
import { X, Plus, Trash2, Save, Loader2 } from 'lucide-react';
import type { NodeConfig, Token, NodesConfigResponse } from '../types/api';

export interface NodeConfigDialogProps {
  open: boolean;
  onClose: () => void;
  onSaved?: () => void;
}

export default function NodeConfigDialog({ open, onClose, onSaved }: NodeConfigDialogProps) {
  const [configs, setConfigs] = useState<NodeConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedNode, setExpandedNode] = useState<number | null>(null);

  // Fetch configs when dialog opens
  useEffect(() => {
    if (!open) return;
    fetchConfigs();
  }, [open]);

  async function fetchConfigs() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/nodesconfig');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: NodesConfigResponse = await res.json();
      setConfigs(data.configs || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configs');
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/nodesconfig', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configs),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Save failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      onSaved?.();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  }

  function addNode() {
    const newNode: NodeConfig = {
      name: `Node${configs.length + 1}`,
      ip_address: '',
      tokens: [],
    };
    setConfigs([...configs, newNode]);
    setExpandedNode(configs.length);
  }

  function removeNode(idx: number) {
    setConfigs(configs.filter((_, i) => i !== idx));
    if (expandedNode === idx) setExpandedNode(null);
    else if (expandedNode !== null && expandedNode > idx) setExpandedNode(expandedNode - 1);
  }

  function updateNode(idx: number, field: keyof NodeConfig, value: string) {
    const updated = [...configs];
    updated[idx] = { ...updated[idx], [field]: value };
    setConfigs(updated);
  }

  function addToken(nodeIdx: number) {
    const newToken: Token = {
      token_id: '',
      token_type: 'FBC',
      port: 2077,
      protocol: 'telnet',
    };
    const updated = [...configs];
    updated[nodeIdx] = {
      ...updated[nodeIdx],
      tokens: [...updated[nodeIdx].tokens, newToken],
    };
    setConfigs(updated);
  }

  function removeToken(nodeIdx: number, tokenIdx: number) {
    const updated = [...configs];
    updated[nodeIdx] = {
      ...updated[nodeIdx],
      tokens: updated[nodeIdx].tokens.filter((_, i) => i !== tokenIdx),
    };
    setConfigs(updated);
  }

  function updateToken(
    nodeIdx: number,
    tokenIdx: number,
    field: keyof Token,
    value: string | number,
  ) {
    const updated = [...configs];
    const tokens = [...updated[nodeIdx].tokens];
    tokens[tokenIdx] = { ...tokens[tokenIdx], [field]: value };
    updated[nodeIdx] = { ...updated[nodeIdx], tokens };
    setConfigs(updated);
  }

  if (!open) return null;

  const inputStyle: React.CSSProperties = {
    padding: '4px 8px',
    backgroundColor: 'var(--bg-secondary)',
    border: '1px solid var(--border)',
    borderRadius: '4px',
    color: 'var(--text-primary)',
    fontSize: '12px',
    fontFamily: 'var(--font-mono)',
    outline: 'none',
    width: '100%',
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0,0,0,0.6)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 200,
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="card-elevated"
        style={{
          width: '700px',
          maxWidth: '95vw',
          maxHeight: '85vh',
          display: 'flex',
          flexDirection: 'column',
          padding: '20px',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px',
          }}
        >
          <h2 style={{ fontSize: '16px', fontWeight: 600 }}>Node Configuration</h2>
          <button className="btn btn-ghost" style={{ padding: '4px' }} onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Error */}
        {error && (
          <div
            style={{
              padding: '8px 12px',
              fontSize: '12px',
              color: 'var(--error)',
              backgroundColor: 'rgba(239,68,68,0.1)',
              borderRadius: '6px',
              marginBottom: '12px',
            }}
          >
            {error}
          </div>
        )}

        {/* Body */}
        <div style={{ flex: 1, overflow: 'auto' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '32px' }}>
              <Loader2 size={20} color="var(--accent)" style={{ animation: 'spin 1s linear infinite' }} />
            </div>
          ) : (
            <>
              {configs.length === 0 && (
                <p style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', padding: '24px' }}>
                  No nodes configured. Click "Add Node" to create one.
                </p>
              )}

              {configs.map((node, nodeIdx) => (
                <div
                  key={nodeIdx}
                  style={{
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    marginBottom: '8px',
                    overflow: 'hidden',
                  }}
                >
                  {/* Node header */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '8px 12px',
                      backgroundColor: 'var(--bg-secondary)',
                      cursor: 'pointer',
                    }}
                    onClick={() => setExpandedNode(expandedNode === nodeIdx ? null : nodeIdx)}
                  >
                    <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {node.name || '(unnamed)'}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {node.ip_address || '—'}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--accent)', marginLeft: 'auto' }}>
                      {node.tokens.length} token{node.tokens.length !== 1 ? 's' : ''}
                    </span>
                    <button
                      className="btn btn-ghost"
                      style={{ padding: '2px', color: 'var(--error)' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        removeNode(nodeIdx);
                      }}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>

                  {/* Node details (expanded) */}
                  {expandedNode === nodeIdx && (
                    <div style={{ padding: '12px' }}>
                      <div style={{ display: 'flex', gap: '12px', marginBottom: '12px' }}>
                        <div style={{ flex: 1 }}>
                          <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>
                            Name
                          </label>
                          <input
                            type="text"
                            value={node.name}
                            onChange={(e) => updateNode(nodeIdx, 'name', e.target.value)}
                            style={inputStyle}
                          />
                        </div>
                        <div style={{ flex: 1 }}>
                          <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>
                            IP Address
                          </label>
                          <input
                            type="text"
                            value={node.ip_address}
                            onChange={(e) => updateNode(nodeIdx, 'ip_address', e.target.value)}
                            style={inputStyle}
                            placeholder="192.168.1.100"
                          />
                        </div>
                      </div>

                      {/* Tokens */}
                      <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                        Tokens
                      </div>
                      {node.tokens.map((tok, tokenIdx) => (
                        <div
                          key={tokenIdx}
                          style={{
                            display: 'flex',
                            gap: '6px',
                            marginBottom: '4px',
                            alignItems: 'flex-end',
                          }}
                        >
                          <div style={{ width: '80px' }}>
                            <input
                              type="text"
                              value={tok.token_id}
                              onChange={(e) => updateToken(nodeIdx, tokenIdx, 'token_id', e.target.value)}
                              style={inputStyle}
                              placeholder="Token ID"
                            />
                          </div>
                          <div style={{ width: '80px' }}>
                            <select
                              value={tok.token_type}
                              onChange={(e) => updateToken(nodeIdx, tokenIdx, 'token_type', e.target.value)}
                              style={inputStyle}
                            >
                              <option value="FBC">FBC</option>
                              <option value="RPC">RPC</option>
                              <option value="LOG">LOG</option>
                              <option value="LIS">LIS</option>
                              <option value="FTP">FTP</option>
                            </select>
                          </div>
                          <div style={{ width: '70px' }}>
                            <input
                              type="number"
                              value={tok.port}
                              onChange={(e) => updateToken(nodeIdx, tokenIdx, 'port', Number(e.target.value) || 23)}
                              style={inputStyle}
                              placeholder="Port"
                            />
                          </div>
                          <div style={{ width: '80px' }}>
                            <select
                              value={tok.protocol}
                              onChange={(e) => updateToken(nodeIdx, tokenIdx, 'protocol', e.target.value)}
                              style={inputStyle}
                            >
                              <option value="telnet">telnet</option>
                              <option value="ftp">ftp</option>
                            </select>
                          </div>
                          <button
                            className="btn btn-ghost"
                            style={{ padding: '4px', color: 'var(--error)' }}
                            onClick={() => removeToken(nodeIdx, tokenIdx)}
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      ))}
                      <button
                        className="btn btn-secondary"
                        style={{ fontSize: '11px', padding: '2px 8px', marginTop: '4px' }}
                        onClick={() => addToken(nodeIdx)}
                      >
                        <Plus size={10} />
                        Add Token
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            display: 'flex',
            gap: '8px',
            paddingTop: '12px',
            borderTop: '1px solid var(--border)',
          }}
        >
          <button className="btn btn-secondary" style={{ fontSize: '12px' }} onClick={addNode}>
            <Plus size={14} />
            Add Node
          </button>
          <div style={{ flex: 1 }} />
          <button className="btn btn-ghost" style={{ fontSize: '12px' }} onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            style={{ fontSize: '12px' }}
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? (
              <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
            ) : (
              <Save size={14} />
            )}
            Save
          </button>
        </div>
      </div>
    </div>
  );
}