import { useState } from 'react'
import { useNodesStore } from '../../store/nodesStore'
import { nodeScanApi, NodeScanResult } from '../../api/nodescan'

export function CommanderTab() {
  const { nodes } = useNodesStore()
  const [scanning, setScanning] = useState(false)
  const [results, setResults] = useState<NodeScanResult[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<string[]>([])

  const toggleSelect = (name: string) => {
    setSelected(prev =>
      prev.includes(name) ? prev.filter(n => n !== name) : [...prev, name]
    )
  }

  const scan = async (names: string[] = []) => {
    setScanning(true)
    setError(null)
    try {
      const r = await nodeScanApi.scan(names)
      setResults(r.results)
    } catch (e) {
      setError(String(e))
    } finally {
      setScanning(false)
    }
  }

  const reachable = results?.filter(r => r.reachable).length ?? 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 16, gap: 12 }}>

      <div style={{ fontSize: 16, fontWeight: 600, color: '#5D3E8E' }}>Commander — Node Status</div>

      {/* Toolbar */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <button
          onClick={() => scan([])}
          disabled={scanning}
          style={{
            padding: '5px 14px',
            background: scanning ? '#333' : '#5D3E8E',
            border: 'none', color: '#fff', fontSize: 13, borderRadius: 4,
            cursor: scanning ? 'default' : 'pointer', fontWeight: 600
          }}
        >
          {scanning ? 'Scanning...' : `Scan All (${nodes.length})`}
        </button>

        {selected.length > 0 && (
          <button
            onClick={() => scan(selected)}
            disabled={scanning}
            style={{
              padding: '5px 14px', background: scanning ? '#333' : '#3E5D8E',
              border: 'none', color: '#fff', fontSize: 13, borderRadius: 4,
              cursor: scanning ? 'default' : 'pointer'
            }}
          >
            Scan Selected ({selected.length})
          </button>
        )}

        {results && (
          <>
            <button
              onClick={() => { setResults(null); setSelected([]) }}
              style={{
                padding: '5px 10px', background: 'none', border: '1px solid #333',
                color: '#555', fontSize: 12, borderRadius: 4, cursor: 'pointer'
              }}
            >Clear</button>
            <span style={{ fontSize: 12, color: '#888', marginLeft: 4 }}>
              <span style={{ color: '#4caf50', fontWeight: 600 }}>{reachable}</span>
              {' / '}{results.length} reachable
            </span>
          </>
        )}
      </div>

      {error && (
        <div style={{ color: '#f44336', fontSize: 12, padding: '4px 8px', background: '#1a0000', borderRadius: 4 }}>
          {error}
        </div>
      )}

      {/* Node table */}
      <div style={{ flex: 1, overflow: 'auto', border: '1px solid #2a2a2a', borderRadius: 4 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ background: '#111', position: 'sticky', top: 0 }}>
              <th style={{ width: 28, padding: '6px 8px' }}></th>
              <th style={{ padding: '6px 10px', textAlign: 'left', color: '#555', fontWeight: 600 }}>Node</th>
              <th style={{ padding: '6px 10px', textAlign: 'left', color: '#555', fontWeight: 600 }}>IP</th>
              <th style={{ padding: '6px 10px', textAlign: 'left', color: '#555', fontWeight: 600 }}>Tokens</th>
              {results && <>
                <th style={{ padding: '6px 10px', textAlign: 'center', color: '#555', fontWeight: 600 }}>Status</th>
                <th style={{ padding: '6px 10px', textAlign: 'center', color: '#555', fontWeight: 600 }}>:23</th>
                <th style={{ padding: '6px 10px', textAlign: 'center', color: '#555', fontWeight: 600 }}>:1234</th>
                <th style={{ padding: '6px 10px', textAlign: 'right', color: '#555', fontWeight: 600 }}>Latency</th>
              </>}
            </tr>
          </thead>
          <tbody>
            {nodes.map((n, i) => {
              const scanRes = results?.find(r => r.name === n.name)
              const isSelected = selected.includes(n.name)
              return (
                <tr
                  key={n.name}
                  onClick={() => toggleSelect(n.name)}
                  style={{
                    background: isSelected ? '#1a1040' : i % 2 === 0 ? 'transparent' : '#0d0d0d',
                    cursor: 'pointer',
                    borderLeft: isSelected ? '2px solid #5D3E8E' : '2px solid transparent'
                  }}
                >
                  <td style={{ padding: '4px 8px', textAlign: 'center' }}>
                    <span style={{
                      width: 8, height: 8, borderRadius: '50%', display: 'inline-block',
                      background: scanRes
                        ? scanRes.reachable ? '#4caf50' : '#f44336'
                        : '#333'
                    }} />
                  </td>
                  <td style={{ padding: '4px 10px', color: '#e0e0e0', fontWeight: 600 }}>{n.name}</td>
                  <td style={{ padding: '4px 10px', color: '#888', fontFamily: 'monospace' }}>{n.ip_address}</td>
                  <td style={{ padding: '4px 10px', color: '#555' }}>
                    {n.tokens.map(t => t.token_id).join(', ')}
                  </td>
                  {results && (
                    scanRes ? <>
                      <td style={{ padding: '4px 10px', textAlign: 'center', color: scanRes.reachable ? '#4caf50' : '#f44336' }}>
                        {scanRes.reachable ? '✓' : '✗'}
                      </td>
                      <td style={{ padding: '4px 10px', textAlign: 'center', color: scanRes.port_23 ? '#4caf50' : '#555' }}>
                        {scanRes.port_23 ? '●' : '○'}
                      </td>
                      <td style={{ padding: '4px 10px', textAlign: 'center', color: scanRes.port_1234 ? '#4caf50' : '#555' }}>
                        {scanRes.port_1234 ? '●' : '○'}
                      </td>
                      <td style={{ padding: '4px 10px', textAlign: 'right', color: '#555', fontFamily: 'monospace' }}>
                        {scanRes.latency_ms}ms
                      </td>
                    </> : <>
                      <td colSpan={4} style={{ padding: '4px 10px', color: '#333', textAlign: 'center' }}>—</td>
                    </>
                  )}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
