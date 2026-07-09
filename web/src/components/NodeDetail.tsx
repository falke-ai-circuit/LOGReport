import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Cpu,
  ScanLine,
  FileText,
  Loader2,
  AlertTriangle,
  ArrowLeft,
} from 'lucide-react';
import FBCView from './FBCView';
import RPCView from './RPCView';
import type {
  NodeDetailResponse,
  ScanResponse,
  FBCResponse,
  RPCResponse,
  ApiFBCModule,
  ApiRPCModule,
} from '../types/api';

type Tab = 'info' | 'fbc' | 'rpc';

const STATUS_COLORS: Record<string, string> = {
  connected: 'var(--success)',
  disconnected: 'var(--error)',
  unknown: 'var(--text-muted)',
  error: 'var(--error)',
};

export default function NodeDetail() {
  const { addr } = useParams<{ addr: string }>();
  const navigate = useNavigate();

  // Node detail
  const [node, setNode] = useState<NodeDetailResponse['node'] | null>(null);
  const [ioSummary, setIoSummary] = useState<NodeDetailResponse['io_summary'] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Tabs
  const [tab, setTab] = useState<Tab>('info');

  // FBC data
  const [fbcModules, setFbcModules] = useState<ApiFBCModule[]>([]);
  const [fbcLoading, setFbcLoading] = useState(false);
  const [fbcError, setFbcError] = useState<string | null>(null);

  // RPC data
  const [rpcModules, setRpcModules] = useState<ApiRPCModule[]>([]);
  const [rpcLoading, setRpcLoading] = useState(false);
  const [rpcError, setRpcError] = useState<string | null>(null);

  // Scan
  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<string | null>(null);

  // Fetch node detail
  useEffect(() => {
    if (!addr) return;
    const nodeAddr = addr;
    let cancelled = false;

    async function fetchNode() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`/api/v1/nodes/${encodeURIComponent(nodeAddr)}`);
        if (!res.ok) {
          const data = await res.json().catch(() => ({ message: 'Not found' }));
          throw new Error(data.message || `HTTP ${res.status}`);
        }
        const data: NodeDetailResponse = await res.json();
        if (!cancelled) {
          setNode(data.node);
          setIoSummary(data.io_summary);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load node');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchNode();
    return () => { cancelled = true; };
  }, [addr]);

  // Fetch FBC when tab selected
  useEffect(() => {
    if (tab !== 'fbc' || !addr) return;
    const nodeAddr = addr;
    let cancelled = false;

    async function fetchFBC() {
      setFbcLoading(true);
      setFbcError(null);
      try {
        const res = await fetch(`/api/v1/nodes/${encodeURIComponent(nodeAddr)}/fbc`);
        if (!res.ok) {
          const data = await res.json().catch(() => ({ message: 'No FBC data' }));
          throw new Error(data.message || `HTTP ${res.status}`);
        }
        const data: FBCResponse = await res.json();
        if (!cancelled) {
          setFbcModules(data.fbc_modules ?? []);
        }
      } catch (err) {
        if (!cancelled) {
          setFbcError(err instanceof Error ? err.message : 'Failed to load FBC data');
        }
      } finally {
        if (!cancelled) setFbcLoading(false);
      }
    }

    fetchFBC();
    return () => { cancelled = true; };
  }, [tab, addr]);

  // Fetch RPC when tab selected
  useEffect(() => {
    if (tab !== 'rpc' || !addr) return;
    const nodeAddr = addr;
    let cancelled = false;

    async function fetchRPC() {
      setRpcLoading(true);
      setRpcError(null);
      try {
        const res = await fetch(`/api/v1/nodes/${encodeURIComponent(nodeAddr)}/rpc`);
        if (!res.ok) {
          const data = await res.json().catch(() => ({ message: 'No RPC data' }));
          throw new Error(data.message || `HTTP ${res.status}`);
        }
        const data: RPCResponse = await res.json();
        if (!cancelled) {
          setRpcModules(data.rpc_modules ?? []);
        }
      } catch (err) {
        if (!cancelled) {
          setRpcError(err instanceof Error ? err.message : 'Failed to load RPC data');
        }
      } finally {
        if (!cancelled) setRpcLoading(false);
      }
    }

    fetchRPC();
    return () => { cancelled = true; };
  }, [tab, addr]);

  // Scan handler
  async function handleScan() {
    if (!addr) return;
    const nodeAddr = addr;
    setScanning(true);
    setScanError(null);
    setScanResult(null);
    try {
      const res = await fetch(`/api/v1/nodes/${encodeURIComponent(nodeAddr)}/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modules: ['fbc', 'rpc'] }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Scan failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      const data: ScanResponse = await res.json();
      setScanResult(
        `Scan complete: ${data.fbc_modules.length} FBC modules, ${data.rpc_modules.length} RPC modules, ${data.io_points_total} total IO points`
      );
      // Refresh node detail
      const nodeRes = await fetch(`/api/v1/nodes/${encodeURIComponent(nodeAddr)}`);
      if (nodeRes.ok) {
        const nodeData: NodeDetailResponse = await nodeRes.json();
        setNode(nodeData.node);
        setIoSummary(nodeData.io_summary);
      }
    } catch (err) {
      setScanError(err instanceof Error ? err.message : 'Scan failed');
    } finally {
      setScanning(false);
    }
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
          <p style={{ color: 'var(--text-secondary)' }}>Loading node...</p>
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
          <button className="btn btn-secondary" onClick={() => navigate('/nodes')}>
            <ArrowLeft size={16} />
            Back to Nodes
          </button>
        </div>
      </div>
    );
  }

  if (!node) return null;

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
            onClick={() => navigate('/nodes')}
            style={{ padding: '4px 8px' }}
          >
            <ArrowLeft size={18} />
          </button>
          <Cpu size={24} color="var(--accent)" />
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>{node.name}</h1>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className="btn btn-primary"
            onClick={handleScan}
            disabled={scanning}
          >
            {scanning ? (
              <>
                <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                Scanning...
              </>
            ) : (
              <>
                <ScanLine size={16} />
                Scan
              </>
            )}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => navigate(`/reports?node=${encodeURIComponent(node.address)}`)}
          >
            <FileText size={16} />
            Generate Report
          </button>
        </div>
      </div>

      {/* Scan feedback */}
      {scanResult && (
        <div
          style={{
            padding: '10px 16px',
            backgroundColor: 'rgba(16,185,129,0.1)',
            border: '1px solid var(--success)',
            borderRadius: '8px',
            color: 'var(--success)',
            fontSize: '13px',
            marginBottom: '16px',
          }}
        >
          {scanResult}
        </div>
      )}
      {scanError && (
        <div
          style={{
            padding: '10px 16px',
            backgroundColor: 'rgba(239,68,68,0.1)',
            border: '1px solid var(--error)',
            borderRadius: '8px',
            color: 'var(--error)',
            fontSize: '13px',
            marginBottom: '16px',
          }}
        >
          {scanError}
        </div>
      )}

      {/* Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '4px',
          marginBottom: '16px',
          borderBottom: '1px solid var(--border)',
          paddingBottom: '0',
        }}
      >
        {(['info', 'fbc', 'rpc'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              padding: '8px 16px',
              fontSize: '13px',
              fontWeight: tab === t ? 600 : 400,
              color: tab === t ? 'var(--accent)' : 'var(--text-secondary)',
              backgroundColor: 'transparent',
              border: 'none',
              borderBottom: tab === t ? '2px solid var(--accent)' : '2px solid transparent',
              cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
              transition: 'all 0.15s ease',
            }}
          >
            {t === 'info' ? 'Info' : t.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Info tab */}
      {tab === 'info' && (
        <div className="card" style={{ padding: '20px' }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
              gap: '16px',
            }}
          >
            <InfoField label="Name" value={node.name} />
            <InfoField label="Address" value={`${node.address}:${node.port}`} mono />
            <InfoField label="Type" value={node.node_type} accent />
            <InfoField
              label="Status"
              value={
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: STATUS_COLORS[node.status] || 'var(--text-muted)',
                    }}
                  />
                  {node.status}
                </span>
              }
            />
            <InfoField label="Token ID" value={node.token || '—'} mono />
            <InfoField
              label="Last Seen"
              value={node.last_connected ? new Date(node.last_connected).toLocaleString() : 'never'}
            />
            {ioSummary && (
              <>
                <InfoField label="FBC Modules" value={String(ioSummary.fbc_modules)} />
                <InfoField label="RPC Modules" value={String(ioSummary.rpc_modules)} />
                <InfoField label="Total IO Points" value={String(ioSummary.total_io_points)} />
              </>
            )}
          </div>
        </div>
      )}

      {/* FBC tab */}
      {tab === 'fbc' && (
        <>
          {fbcLoading && (
            <div className="card" style={{ textAlign: 'center', padding: '32px' }}>
              <Loader2
                size={20}
                color="var(--accent)"
                style={{ animation: 'spin 1s linear infinite', marginBottom: '8px' }}
              />
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Loading FBC data...</p>
            </div>
          )}
          {!fbcLoading && fbcError && (
            <div className="card" style={{ textAlign: 'center', padding: '32px' }}>
              <AlertTriangle size={20} color="var(--warning)" style={{ marginBottom: '8px' }} />
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '12px' }}>
                {fbcError}
              </p>
              <button className="btn btn-primary" onClick={handleScan} disabled={scanning}>
                <ScanLine size={14} />
                Run Scan
              </button>
            </div>
          )}
          {!fbcLoading && !fbcError && <FBCView modules={fbcModules} />}
        </>
      )}

      {/* RPC tab */}
      {tab === 'rpc' && (
        <>
          {rpcLoading && (
            <div className="card" style={{ textAlign: 'center', padding: '32px' }}>
              <Loader2
                size={20}
                color="var(--accent)"
                style={{ animation: 'spin 1s linear infinite', marginBottom: '8px' }}
              />
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Loading RPC data...</p>
            </div>
          )}
          {!rpcLoading && rpcError && (
            <div className="card" style={{ textAlign: 'center', padding: '32px' }}>
              <AlertTriangle size={20} color="var(--warning)" style={{ marginBottom: '8px' }} />
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '12px' }}>
                {rpcError}
              </p>
              <button className="btn btn-primary" onClick={handleScan} disabled={scanning}>
                <ScanLine size={14} />
                Run Scan
              </button>
            </div>
          )}
          {!rpcLoading && !rpcError && <RPCView modules={rpcModules} />}
        </>
      )}
    </div>
  );
}

// ─── InfoField helper ─────────────────────────────────────────────

function InfoField({
  label,
  value,
  mono,
  accent,
}: {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
  accent?: boolean;
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
          color: accent ? 'var(--accent)' : 'var(--text-primary)',
          fontFamily: mono ? 'var(--font-mono)' : 'var(--font-sans)',
        }}
      >
        {value}
      </div>
    </div>
  );
}
