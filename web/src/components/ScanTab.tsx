import { useState, useEffect, useRef, useCallback } from 'react';
import { Loader2, RefreshCw, AlertTriangle } from 'lucide-react';
import type {
  TreeNodeData,
  ScanCompareRequest,
  ScanCompareResponse,
  ComparisonCell,
} from '../types/api';

export interface ScanTabProps {
  selectedNode?: TreeNodeData | null;
  treeNodes?: TreeNodeData[];
}

const CELL_COLORS: Record<string, string> = {
  match: 'var(--success)',
  mismatch: 'var(--error)',
  file_only: '#3b82f6',
  live_only: '#f59e0b',
};

const REFRESH_INTERVALS = [
  { label: 'Off', value: 0 },
  { label: '5s', value: 5 },
  { label: '10s', value: 10 },
  { label: '30s', value: 30 },
  { label: '60s', value: 60 },
  { label: '300s', value: 300 },
];

export default function ScanTab({ treeNodes }: ScanTabProps) {
  const [configs, setConfigs] = useState<TreeNodeData[]>([]);
  const [activeNodeName, setActiveNodeName] = useState<string>('');
  const [fileData, setFileData] = useState('');
  const [comparing, setComparing] = useState(false);
  const [comparison, setComparison] = useState<ScanCompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshInterval, setRefreshInterval] = useState(0);
  const [countdown, setCountdown] = useState(0);
  const [selectedCell, setSelectedCell] = useState<ComparisonCell | null>(null);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Use provided treeNodes or extract from selectedNode
  const nodeConfigs = configs.length > 0 ? configs : treeNodes || [];

  // Fetch nodesconfig if no nodes provided
  const fetchConfigs = useCallback(async () => {
    if (treeNodes && treeNodes.length > 0) {
      setConfigs(treeNodes);
      if (!activeNodeName && treeNodes.length > 0) {
        setActiveNodeName(treeNodes[0].name);
      }
      return;
    }
    try {
      const res = await fetch('/api/v1/nodesconfig/tree');
      if (!res.ok) return;
      const data = await res.json();
      const root: TreeNodeData = data.tree;
      const nodes = root.children || [];
      setConfigs(nodes);
      if (!activeNodeName && nodes.length > 0) {
        setActiveNodeName(nodes[0].name);
      }
    } catch {
      // ignore
    }
  }, [treeNodes, activeNodeName]);

  useEffect(() => {
    fetchConfigs();
  }, [fetchConfigs]);

  // ─── Compare ─────────────────────────────────────────────────

  const runCompare = useCallback(
    async (nodeName?: string) => {
      const target = nodeName || activeNodeName;
      if (!target) return;

      // Find the node and a token
      const node = nodeConfigs.find((n) => n.name === target);
      if (!node) return;

      // Find first FBC token
      let fbcToken: TreeNodeData | null = null;
      if (node.children) {
        for (const group of node.children) {
          if (group.name === 'FBC' && group.children) {
            fbcToken = group.children[0] || null;
            if (fbcToken) break;
          }
        }
      }

      if (!fbcToken || !node.ip || !fbcToken.token_id) {
        setError('No FBC token found for this node');
        return;
      }

      setComparing(true);
      setError(null);
      try {
        const req: ScanCompareRequest = {
          node_address: node.ip,
          port: fbcToken.port || 23,
          token: fbcToken.token_id,
          file_data: fileData,
        };
        const res = await fetch('/api/v1/scan/compare', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(req),
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({ message: 'Compare failed' }));
          throw new Error(data.message || `HTTP ${res.status}`);
        }
        const data: ScanCompareResponse = await res.json();
        setComparison(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Comparison failed');
      } finally {
        setComparing(false);
      }
    },
    [activeNodeName, nodeConfigs, fileData],
  );

  // ─── Auto-refresh ────────────────────────────────────────────

  useEffect(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (countdownRef.current) clearInterval(countdownRef.current);

    if (refreshInterval > 0) {
      setCountdown(refreshInterval);
      intervalRef.current = setInterval(() => {
        runCompare();
        setCountdown(refreshInterval);
      }, refreshInterval * 1000);

      countdownRef.current = setInterval(() => {
        setCountdown((prev) => (prev > 0 ? prev - 1 : 0));
      }, 1000);
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (countdownRef.current) clearInterval(countdownRef.current);
    };
  }, [refreshInterval, runCompare]);

  // ─── Build table from comparison cells ───────────────────────

  const cells = comparison?.comparison.cells || [];
  const rows = [...new Set(cells.map((c) => c.row))].sort((a, b) => a - b);
  const cols = [...new Set(cells.map((c) => c.col))].sort((a, b) => a - b);

  function getCell(row: number, col: number): ComparisonCell | undefined {
    return cells.find((c) => c.row === row && c.col === col);
  }

  // ─── Render ──────────────────────────────────────────────────

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'auto' }}>
      {/* Node subtabs */}
      <div
        style={{
          display: 'flex',
          gap: '2px',
          padding: '8px 12px 0',
          borderBottom: '1px solid var(--border)',
          flexWrap: 'wrap',
        }}
      >
        {nodeConfigs.length === 0 && (
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', padding: '4px 8px' }}>
            No nodes available. Load nodes.json first.
          </span>
        )}
        {nodeConfigs.map((n) => (
          <button
            key={n.name}
            onClick={() => {
              setActiveNodeName(n.name);
              setComparison(null);
              setSelectedCell(null);
            }}
            style={{
              padding: '4px 12px',
              fontSize: '11px',
              fontWeight: activeNodeName === n.name ? 600 : 400,
              color: activeNodeName === n.name ? 'var(--accent)' : 'var(--text-secondary)',
              backgroundColor: 'transparent',
              border: 'none',
              borderBottom:
                activeNodeName === n.name ? '2px solid var(--accent)' : '2px solid transparent',
              cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
            }}
          >
            {n.name}
          </button>
        ))}
      </div>

      {/* Controls */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '12px',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>File Data:</label>
          <textarea
            placeholder="Paste FBC file data here..."
            value={fileData}
            onChange={(e) => setFileData(e.target.value)}
            style={{
              width: '300px',
              height: '40px',
              padding: '4px 8px',
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              borderRadius: '4px',
              color: 'var(--text-primary)',
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
              outline: 'none',
              resize: 'vertical',
            }}
          />
        </div>

        <button
          className="btn btn-primary"
          style={{ fontSize: '12px', padding: '4px 12px' }}
          onClick={() => runCompare()}
          disabled={comparing || !activeNodeName}
        >
          {comparing ? (
            <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />
          ) : (
            <RefreshCw size={12} />
          )}
          Compare with Live
        </button>

        {/* Auto-refresh dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Auto-refresh:</label>
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            style={{
              padding: '4px 8px',
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              borderRadius: '4px',
              color: 'var(--text-primary)',
              fontSize: '11px',
              outline: 'none',
            }}
          >
            {REFRESH_INTERVALS.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
          {refreshInterval > 0 && (
            <span style={{ fontSize: '11px', color: 'var(--accent)', fontFamily: 'var(--font-mono)' }}>
              {countdown}s
            </span>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div
          style={{
            margin: '0 12px',
            padding: '8px 12px',
            fontSize: '12px',
            color: 'var(--error)',
            backgroundColor: 'rgba(239,68,68,0.1)',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <AlertTriangle size={14} />
          {error}
        </div>
      )}

      {/* Comparison summary */}
      {comparison && (
        <div style={{ padding: '0 12px 8px', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
          <SummaryStat label="Total" value={comparison.comparison.total_cells} color="var(--text-primary)" />
          <SummaryStat label="Match" value={comparison.comparison.matching} color="var(--success)" />
          <SummaryStat label="Mismatch" value={comparison.comparison.mismatched} color="var(--error)" />
          <SummaryStat label="File Only" value={comparison.comparison.file_only} color="#3b82f6" />
          <SummaryStat label="Live Only" value={comparison.comparison.live_only} color="#f59e0b" />
        </div>
      )}

      {/* FBC comparison table */}
      {comparison && cells.length > 0 && (
        <div style={{ padding: '0 12px 12px', overflow: 'auto' }}>
          <h3 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>FBC Comparison</h3>
          <table
            style={{
              borderCollapse: 'collapse',
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
            }}
          >
            <thead>
              <tr>
                <th
                  style={{
                    padding: '4px 8px',
                    borderBottom: '1px solid var(--border)',
                    color: 'var(--text-muted)',
                    textAlign: 'left',
                  }}
                >
                  PIC
                </th>
                {cols.map((col) => (
                  <th
                    key={col}
                    style={{
                      padding: '4px 8px',
                      borderBottom: '1px solid var(--border)',
                      color: 'var(--text-muted)',
                      textAlign: 'center',
                    }}
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row}>
                  <td
                    style={{
                      padding: '4px 8px',
                      color: 'var(--accent)',
                      fontWeight: 600,
                      borderBottom: '1px solid var(--border)',
                    }}
                  >
                    {row}
                  </td>
                  {cols.map((col) => {
                    const cell = getCell(row, col);
                    const color = cell ? CELL_COLORS[cell.status] || 'var(--text-muted)' : 'var(--text-muted)';
                    return (
                      <td
                        key={col}
                        onClick={() => cell && setSelectedCell(cell)}
                        style={{
                          padding: '4px 8px',
                          textAlign: 'center',
                          borderBottom: '1px solid var(--border)',
                          backgroundColor: cell ? `${color}22` : 'transparent',
                          color,
                          cursor: cell ? 'pointer' : 'default',
                          fontWeight: 500,
                        }}
                        title={cell ? `${cell.file_value || '—'} vs ${cell.live_value || '—'}` : ''}
                      >
                        {cell?.file_value || cell?.live_value || '—'}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Selected cell detail */}
      {selectedCell && (
        <div
          style={{
            margin: '0 12px 12px',
            padding: '12px',
            backgroundColor: 'var(--bg-elevated)',
            borderRadius: '8px',
            border: '1px solid var(--border)',
          }}
        >
          <h4 style={{ fontSize: '12px', fontWeight: 600, marginBottom: '8px' }}>
            Cell Detail (PIC {selectedCell.row}, Ch {selectedCell.col})
          </h4>
          <div style={{ display: 'flex', gap: '16px', fontSize: '12px' }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>File: </span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                {selectedCell.file_value || '—'}
              </span>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Live: </span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                {selectedCell.live_value || '—'}
              </span>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Status: </span>
              <span style={{ color: CELL_COLORS[selectedCell.status] || 'var(--text-muted)' }}>
                {selectedCell.status}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!comparison && !comparing && !error && (
        <div
          style={{
            padding: '48px',
            textAlign: 'center',
            color: 'var(--text-muted)',
            fontSize: '13px',
          }}
        >
          Paste FBC file data and click "Compare with Live" to see the comparison table.
        </div>
      )}
    </div>
  );
}

// ─── SummaryStat helper ───────────────────────────────────────────

function SummaryStat({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
      <span
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: color,
        }}
      />
      <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{label}:</span>
      <span style={{ fontSize: '12px', fontWeight: 600, color, fontFamily: 'var(--font-mono)' }}>
        {value}
      </span>
    </div>
  );
}