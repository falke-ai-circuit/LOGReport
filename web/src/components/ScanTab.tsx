import { useState, useEffect, useRef, useCallback } from 'react';
import { Loader2, RefreshCw, AlertTriangle, FileText } from 'lucide-react';
import type {
  TreeNodeData,
  ScanCompareRequest,
  ScanCompareResponse,
  ComparisonCell,
} from '../types/api';

export interface ScanTabProps {
  selectedNode?: TreeNodeData | null;
  treeNodes?: TreeNodeData[];
  logRoot?: string;
}

const CELL_COLORS: Record<string, string> = {
  match: 'var(--success)',
  mismatch: 'var(--error)',
  file_only: '#3b82f6',
  live_only: '#f59e0b',
};

const FILE_TYPES = [
  { label: 'FBC', value: 'fbc' },
  { label: 'RPC', value: 'rpc' },
  { label: 'LOG', value: 'log' },
  { label: 'LIS', value: 'lis' },
];

interface LogFileEntry {
  file_name: string;
  file_path: string;
  extension: string;
  size: number;
  modified_at: string;
  node_name: string;
}

export default function ScanTab({ treeNodes, logRoot: propLogRoot }: ScanTabProps) {
  const [configs, setConfigs] = useState<TreeNodeData[]>([]);
  const [activeNodeName, setActiveNodeName] = useState<string>('');
  const [fileData, setFileData] = useState('');
  const [fileData2, setFileData2] = useState('');
  const [selectedFile1, setSelectedFile1] = useState<string>('');
  const [selectedFile2, setSelectedFile2] = useState<string>('');
  const [fileType, setFileType] = useState<string>('fbc');
  const [fileList, setFileList] = useState<LogFileEntry[]>([]);
  const [filesLoading, setFilesLoading] = useState(false);
  const [comparing, setComparing] = useState(false);
  const [comparison, setComparison] = useState<ScanCompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [parsedTable, setParsedTable] = useState<{ key: string; value: string }[] | null>(null);
  const [parsedTable2, setParsedTable2] = useState<{ key: string; value: string }[] | null>(null);
  const [selectedCell, setSelectedCell] = useState<ComparisonCell | null>(null);

  // Use prop logRoot or localStorage
  const logRoot = propLogRoot || localStorage.getItem('logRoot') || '';

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

  // Fetch file list when logRoot or fileType changes
  const fetchFiles = useCallback(async () => {
    if (!logRoot) {
      setFileList([]);
      return;
    }
    setFilesLoading(true);
    try {
      const res = await fetch(`/api/v1/logs/files?path=${encodeURIComponent(logRoot)}&type=${fileType}`);
      if (!res.ok) {
        setFileList([]);
        return;
      }
      const data = await res.json();
      setFileList(data.files || []);
    } catch {
      setFileList([]);
    } finally {
      setFilesLoading(false);
    }
  }, [logRoot, fileType]);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  // Fetch and parse a file when selected
  async function handleFileSelect(file: string, slot: 1 | 2) {
    if (!file) {
      if (slot === 1) {
        setSelectedFile1('');
        setFileData('');
        setParsedTable(null);
      } else {
        setSelectedFile2('');
        setFileData2('');
        setParsedTable2(null);
      }
      return;
    }

    try {
      // Fetch file content from the log root
      const res = await fetch(`/api/v1/logs/files?path=${encodeURIComponent(logRoot)}&type=${fileType}`);
      if (!res.ok) return;
      const data = await res.json();
      const entry = (data.files || []).find((f: LogFileEntry) => f.file_name === file);
      if (!entry) return;

      // Read the file content via the API
      const contentRes = await fetch(`/api/v1/logs/list?path=${encodeURIComponent(logRoot)}`);
      // We need the raw file content - let's fetch it directly
      // Since there's no direct file content endpoint, we parse from the file path
      const response = await fetch(`/api/v1/logs/files?path=${encodeURIComponent(logRoot)}&type=${fileType}`);
      const fileListData = await response.json();
      const fileEntry = (fileListData.files || []).find((f: LogFileEntry) => f.file_name === file);

      if (fileEntry) {
        // Fetch file content — use a fetch to get the raw content
        // The API doesn't have a direct "read file" endpoint for log root files,
        // but we can use the log list to get path and then read via the node log endpoint
        // For now, let's use a simple approach: fetch via a dedicated content fetch
        const content = await fetchFileContent(fileEntry.file_path);
        if (slot === 1) {
          setSelectedFile1(file);
          setFileData(content);
          setParsedTable(parseKeyValue(content));
        } else {
          setSelectedFile2(file);
          setFileData2(content);
          setParsedTable2(parseKeyValue(content));
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load file');
    }
  }

  // Fetch file content by reading from the server
  async function fetchFileContent(filePath: string): Promise<string> {
    // Use the log content endpoint to read raw file content
    const res = await fetch(`/api/v1/logs/content?path=${encodeURIComponent(filePath)}`);
    if (!res.ok) return '';
    const data = await res.json();
    return data.content || '';
  }

  // Parse key=value content into a table structure
  function parseKeyValue(content: string): { key: string; value: string }[] {
    const rows: { key: string; value: string }[] = [];
    const lines = content.split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#') || trimmed === 'END') continue;
      const idx = trimmed.indexOf('=');
      if (idx > 0) {
        rows.push({
          key: trimmed.substring(0, idx).trim(),
          value: trimmed.substring(idx + 1).trim(),
        });
      }
    }
    return rows;
  }

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

  // Compare two loaded files cell-by-cell
  const runFileCompare = useCallback(() => {
    if (!parsedTable || !parsedTable2) {
      setError('Load two files to compare');
      return;
    }

    // Build comparison from key-value pairs
    const map1 = new Map(parsedTable.map((r) => [r.key, r.value]));
    const map2 = new Map(parsedTable2.map((r) => [r.key, r.value]));
    const allKeys = new Set([...map1.keys(), ...map2.keys()]);

    const cells: ComparisonCell[] = [];
    let matching = 0, mismatched = 0, fileOnly = 0, liveOnly = 0;
    let row = 0;

    for (const key of allKeys) {
      const v1 = map1.get(key) || '';
      const v2 = map2.get(key) || '';
      const cell: ComparisonCell = { row, col: 0, file_value: v1, live_value: v2, status: '' };

      if (v1 && v2) {
        if (v1 === v2) {
          cell.status = 'match';
          matching++;
        } else {
          cell.status = 'mismatch';
          mismatched++;
        }
      } else if (v1 && !v2) {
        cell.status = 'file_only';
        fileOnly++;
      } else if (!v1 && v2) {
        cell.status = 'live_only';
        liveOnly++;
      }
      cells.push(cell);
      row++;
    }

    setComparison({
      comparison: {
        total_cells: matching + mismatched + fileOnly + liveOnly,
        matching,
        mismatched,
        file_only: fileOnly,
        live_only: liveOnly,
        cells,
      },
    });
  }, [parsedTable, parsedTable2]);

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
        {/* Log root indicator */}
        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          Log Root: <span style={{ color: logRoot ? 'var(--accent)' : 'var(--error)', fontFamily: 'var(--font-mono)' }}>
            {logRoot || 'not set'}
          </span>
        </div>

        {/* File type selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Type:</label>
          <select
            value={fileType}
            onChange={(e) => {
              setFileType(e.target.value);
              setSelectedFile1('');
              setSelectedFile2('');
              setParsedTable(null);
              setParsedTable2(null);
              setComparison(null);
            }}
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
            {FILE_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        {/* File 1 dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>File 1:</label>
          <select
            value={selectedFile1}
            onChange={(e) => handleFileSelect(e.target.value, 1)}
            disabled={filesLoading || !logRoot}
            style={{
              padding: '4px 8px',
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              borderRadius: '4px',
              color: 'var(--text-primary)',
              fontSize: '11px',
              outline: 'none',
              minWidth: '180px',
            }}
          >
            <option value="">Select file...</option>
            {fileList.map((f) => (
              <option key={f.file_name} value={f.file_name}>{f.file_name}</option>
            ))}
          </select>
        </div>

        {/* File 2 dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>File 2:</label>
          <select
            value={selectedFile2}
            onChange={(e) => handleFileSelect(e.target.value, 2)}
            disabled={filesLoading || !logRoot}
            style={{
              padding: '4px 8px',
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              borderRadius: '4px',
              color: 'var(--text-primary)',
              fontSize: '11px',
              outline: 'none',
              minWidth: '180px',
            }}
          >
            <option value="">Select file...</option>
            {fileList.map((f) => (
              <option key={f.file_name} value={f.file_name}>{f.file_name}</option>
            ))}
          </select>
        </div>

        <button
          className="btn btn-primary"
          style={{ fontSize: '12px', padding: '4px 12px' }}
          onClick={() => runCompare()}
          disabled={comparing || !activeNodeName || !fileData}
          title="Compare File 1 with live node data"
        >
          {comparing ? (
            <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />
          ) : (
            <RefreshCw size={12} />
          )}
          Compare with Live
        </button>

        <button
          className="btn btn-secondary"
          style={{ fontSize: '12px', padding: '4px 12px' }}
          onClick={runFileCompare}
          disabled={!parsedTable || !parsedTable2}
          title="Compare File 1 and File 2 side by side"
        >
          Compare Files
        </button>
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

      {/* Parsed file tables */}
      {(parsedTable || parsedTable2) && (
        <div style={{ display: 'flex', gap: '12px', padding: '0 12px 8px', flexWrap: 'wrap' }}>
          {parsedTable && (
            <div style={{ flex: '1 1 300px' }}>
              <h4 style={{ fontSize: '12px', fontWeight: 600, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <FileText size={12} /> {selectedFile1}
              </h4>
              <ParsedTable data={parsedTable} />
            </div>
          )}
          {parsedTable2 && (
            <div style={{ flex: '1 1 300px' }}>
              <h4 style={{ fontSize: '12px', fontWeight: 600, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <FileText size={12} /> {selectedFile2}
              </h4>
              <ParsedTable data={parsedTable2} />
            </div>
          )}
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
      {!comparison && !comparing && !error && !parsedTable && (
        <div
          style={{
            padding: '48px',
            textAlign: 'center',
            color: 'var(--text-muted)',
            fontSize: '13px',
          }}
        >
          {logRoot ? (
            <>Select a file from the dropdown to view and compare FBC data.</>
          ) : (
            <>Set Log Root in the Commander toolbar to enable file-based scanning.</>
          )}
        </div>
      )}
    </div>
  );
}

// ─── ParsedTable helper ───────────────────────────────────────────

function ParsedTable({ data }: { data: { key: string; value: string }[] }) {
  if (data.length === 0) {
    return <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>No key-value entries found.</div>;
  }
  return (
    <table style={{ borderCollapse: 'collapse', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
      <thead>
        <tr>
          <th style={{ padding: '3px 8px', borderBottom: '1px solid var(--border)', color: 'var(--text-muted)', textAlign: 'left' }}>Key</th>
          <th style={{ padding: '3px 8px', borderBottom: '1px solid var(--border)', color: 'var(--text-muted)', textAlign: 'left' }}>Value</th>
        </tr>
      </thead>
      <tbody>
        {data.map((row, i) => (
          <tr key={i}>
            <td style={{ padding: '3px 8px', color: 'var(--accent)', borderBottom: '1px solid var(--border)' }}>{row.key}</td>
            <td style={{ padding: '3px 8px', color: 'var(--text-primary)', borderBottom: '1px solid var(--border)' }}>{row.value}</td>
          </tr>
        ))}
      </tbody>
    </table>
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