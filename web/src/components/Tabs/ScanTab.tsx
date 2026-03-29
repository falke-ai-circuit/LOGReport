import { useState } from 'react'
import { useLogStore } from '../../store/logStore'
import { scanApi, ParsedScan } from '../../api/scan'
import { FBCResult, RPCResult } from '../../api/types'

type ViewMode = 'fbc' | 'rpc'

export function ScanTab() {
  const { scanResult } = useLogStore()
  const [parsed, setParsed] = useState<ParsedScan | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('fbc')
  const [selectedNode, setSelectedNode] = useState<string | null>(null)

  const load = async () => {
    if (!scanResult) return
    setLoading(true)
    setError(null)
    try {
      const result = await scanApi.getParsed(scanResult.scan_id)
      setParsed(result)
      if (result.fbc.length > 0) setSelectedNode(result.fbc[0].node)
      else if (result.rpc.length > 0) setSelectedNode(result.rpc[0].node)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  if (!scanResult) {
    return (
      <div style={{ padding: 20, textAlign: 'center', marginTop: 60, color: '#555' }}>
        <div style={{ fontSize: 24, marginBottom: 8 }}>📂</div>
        <div style={{ fontSize: 14, color: '#5D3E8E' }}>No scan loaded</div>
        <div style={{ fontSize: 12, marginTop: 4 }}>Go to Log Processor tab and scan a folder first</div>
      </div>
    )
  }

  const fbcNodes = parsed ? [...new Set(parsed.fbc.map(f => f.node))] : []
  const rpcNodes = parsed ? [...new Set(parsed.rpc.map(f => f.node))] : []
  const allNodes = [...new Set([...fbcNodes, ...rpcNodes])]

  const fbcForNode = parsed?.fbc.filter(f => f.node === selectedNode) || []
  const rpcForNode = parsed?.rpc.filter(f => f.node === selectedNode) || []

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 16, gap: 12 }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ fontSize: 16, fontWeight: 600, color: '#5D3E8E' }}>Scan / FBC+RPC Analysis</div>
        <div style={{ fontSize: 12, color: '#555' }}>
          Scan: <span style={{ color: '#888' }}>{scanResult.scan_id}</span>
          {' · '}{scanResult.total} files
        </div>
        {!parsed && (
          <button
            onClick={load}
            disabled={loading}
            style={{
              marginLeft: 'auto', padding: '5px 14px',
              background: loading ? '#333' : '#5D3E8E',
              border: 'none', color: '#fff', fontSize: 13,
              borderRadius: 4, cursor: loading ? 'default' : 'pointer'
            }}
          >
            {loading ? 'Parsing...' : 'Parse FBC/RPC'}
          </button>
        )}
      </div>

      {error && (
        <div style={{ color: '#f44336', fontSize: 12, padding: '4px 8px', background: '#1a0000', borderRadius: 4 }}>
          {error}
        </div>
      )}

      {parsed && (
        <div style={{ display: 'flex', gap: 12, flex: 1, overflow: 'hidden' }}>

          {/* Node selector sidebar */}
          <div style={{
            width: 160, flexShrink: 0,
            border: '1px solid #2a2a2a', borderRadius: 4,
            overflow: 'auto', background: '#0d0d0d'
          }}>
            <div style={{ padding: '6px 10px', fontSize: 11, color: '#555', borderBottom: '1px solid #222' }}>
              NODES ({allNodes.length})
            </div>
            {allNodes.map(node => (
              <div
                key={node}
                onClick={() => setSelectedNode(node)}
                style={{
                  padding: '6px 10px', cursor: 'pointer', fontSize: 13,
                  background: selectedNode === node ? '#1a1040' : 'transparent',
                  color: selectedNode === node ? '#e0e0e0' : '#888',
                  borderLeft: selectedNode === node ? '2px solid #5D3E8E' : '2px solid transparent'
                }}
              >
                {node}
              </div>
            ))}
          </div>

          {/* Main content */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8, overflow: 'hidden' }}>

            {/* View mode toggle */}
            <div style={{ display: 'flex', gap: 4 }}>
              {(['fbc', 'rpc'] as ViewMode[]).map(mode => (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode)}
                  style={{
                    padding: '4px 12px',
                    background: viewMode === mode ? '#5D3E8E' : '#1a1a1a',
                    border: '1px solid ' + (viewMode === mode ? '#5D3E8E' : '#333'),
                    color: viewMode === mode ? '#fff' : '#666',
                    fontSize: 12, borderRadius: 4, cursor: 'pointer',
                    textTransform: 'uppercase', fontWeight: 600
                  }}
                >
                  {mode} {mode === 'fbc' ? `(${fbcForNode.length})` : `(${rpcForNode.length})`}
                </button>
              ))}
            </div>

            {/* Data table */}
            <div style={{ flex: 1, overflow: 'auto' }}>
              {viewMode === 'fbc' && <FBCTable results={fbcForNode} />}
              {viewMode === 'rpc' && <RPCTable results={rpcForNode} />}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function FBCTable({ results }: { results: FBCResult[] }) {
  if (results.length === 0) return <div style={{ color: '#444', padding: 20, fontSize: 13 }}>No FBC files for this node</div>

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {results.map((r, i) => (
        <div key={i} style={{ border: '1px solid #2a2a2a', borderRadius: 4 }}>
          <div style={{
            padding: '5px 10px', background: '#1a1040',
            fontSize: 12, color: '#7a5aa0', borderBottom: '1px solid #222'
          }}>
            Token: {r.token || '—'}
            {r.error && <span style={{ color: '#f44336', marginLeft: 8 }}>⚠ {r.error}</span>}
          </div>
          {r.rows && r.rows.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ background: '#111' }}>
                  {['#', 'Type', 'Name', 'Value', 'Status'].map(h => (
                    <th key={h} style={{ padding: '4px 8px', textAlign: 'left', color: '#555', fontWeight: 600, borderBottom: '1px solid #222' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {r.rows.map((row, j) => (
                  <tr key={j} style={{ background: j % 2 === 0 ? 'transparent' : '#0d0d0d' }}>
                    <td style={{ padding: '3px 8px', color: '#555' }}>{row.index}</td>
                    <td style={{ padding: '3px 8px', color: typeColor(row.type) }}>{row.type}</td>
                    <td style={{ padding: '3px 8px', color: '#ccc' }}>{row.name}</td>
                    <td style={{ padding: '3px 8px', color: row.value === '1' ? '#4caf50' : '#e0e0e0', fontWeight: 600 }}>{row.value}</td>
                    <td style={{ padding: '3px 8px', color: row.status === 'OK' ? '#4caf50' : '#f44336' }}>{row.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: '8px 10px', color: '#444', fontSize: 12 }}>
              {r.error ? 'Parse error' : 'No IO rows found'}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function RPCTable({ results }: { results: RPCResult[] }) {
  if (results.length === 0) return <div style={{ color: '#444', padding: 20, fontSize: 13 }}>No RPC files for this node</div>

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {results.map((r, i) => (
        <div key={i} style={{ border: '1px solid #2a2a2a', borderRadius: 4 }}>
          <div style={{
            padding: '5px 10px', background: '#0d1a1a',
            fontSize: 12, color: '#4a8aa0', borderBottom: '1px solid #222'
          }}>
            Token: {r.token || '—'}
            {r.error && <span style={{ color: '#f44336', marginLeft: 8 }}>⚠ {r.error}</span>}
          </div>
          {r.counters && r.counters.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ background: '#111' }}>
                  {['Counter', 'Value', 'Unit'].map(h => (
                    <th key={h} style={{ padding: '4px 8px', textAlign: 'left', color: '#555', fontWeight: 600, borderBottom: '1px solid #222' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {r.counters.map((c, j) => (
                  <tr key={j} style={{ background: j % 2 === 0 ? 'transparent' : '#0d0d0d' }}>
                    <td style={{ padding: '3px 8px', color: '#ccc' }}>{c.name}</td>
                    <td style={{ padding: '3px 8px', color: c.value !== '0' ? '#f44336' : '#4caf50', fontWeight: 600 }}>{c.value}</td>
                    <td style={{ padding: '3px 8px', color: '#555' }}>{c.unit || ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: '8px 10px', color: '#444', fontSize: 12 }}>
              {r.error ? 'Parse error' : 'No counters found'}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function typeColor(t: string): string {
  switch (t?.toUpperCase()) {
    case 'DI': return '#4a8aa0'
    case 'DO': return '#7a5aa0'
    case 'AI': return '#8aa04a'
    case 'AO': return '#a08a4a'
    default: return '#888'
  }
}
