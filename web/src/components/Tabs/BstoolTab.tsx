import { useState, useEffect } from 'react'
import { useNodesStore } from '../../store/nodesStore'
import { bstoolApi, BstoolStatus, BstoolResult } from '../../api/bstool'

export function BstoolTab() {
  const { nodes } = useNodesStore()
  const [status, setStatus] = useState<BstoolStatus | null>(null)
  const [selectedNode, setSelectedNode] = useState('')
  const [selectedToken, setSelectedToken] = useState('')
  const [timeoutSec, setTimeoutSec] = useState(30)
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<BstoolResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    bstoolApi.status().then(setStatus).catch(() => setStatus({ available: false, path: '' }))
  }, [])

  const selectedNodeObj = nodes.find(n => n.name === selectedNode)

  const handleNodeChange = (name: string) => {
    setSelectedNode(name)
    const node = nodes.find(n => n.name === name)
    if (node && node.tokens.length > 0) {
      setSelectedToken(node.tokens[0].token_id)
    } else {
      setSelectedToken('')
    }
    setResult(null)
  }

  const run = async () => {
    if (!selectedNodeObj || !selectedToken) return
    setRunning(true)
    setError(null)
    setResult(null)
    try {
      const r = await bstoolApi.run(selectedNodeObj.ip_address, selectedToken, timeoutSec)
      setResult(r)
    } catch (e) {
      setError(String(e))
    } finally {
      setRunning(false)
    }
  }

  const tokens = selectedNodeObj?.tokens || []

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 16, gap: 12 }}>

      <div style={{ fontSize: 16, fontWeight: 600, color: '#5D3E8E' }}>BsTool</div>

      {/* BsTool availability */}
      {status && (
        <div style={{
          padding: '6px 10px', borderRadius: 4, fontSize: 12,
          background: status.available ? '#0d1a0d' : '#1a0d0d',
          border: '1px solid ' + (status.available ? '#2a4a2a' : '#4a2a2a'),
          color: status.available ? '#4caf50' : '#f44336'
        }}>
          {status.available
            ? `✓ BsTool.exe found: ${status.path}`
            : '✗ BsTool.exe not found — place BsTool.exe next to LOGReporter.exe'}
        </div>
      )}

      {/* Controls */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ fontSize: 12, color: '#888' }}>Node:</span>
        <select
          value={selectedNode}
          onChange={e => handleNodeChange(e.target.value)}
          style={{
            padding: '5px 8px', background: '#0f0f0f', border: '1px solid #333',
            color: '#e0e0e0', fontSize: 13, borderRadius: 4, outline: 'none', minWidth: 120
          }}
        >
          <option value="">— select —</option>
          {nodes.map(n => (
            <option key={n.name} value={n.name}>{n.name} ({n.ip_address})</option>
          ))}
        </select>

        <span style={{ fontSize: 12, color: '#888' }}>Token:</span>
        <select
          value={selectedToken}
          onChange={e => setSelectedToken(e.target.value)}
          style={{
            padding: '5px 8px', background: '#0f0f0f', border: '1px solid #333',
            color: '#e0e0e0', fontSize: 13, borderRadius: 4, outline: 'none', minWidth: 80
          }}
        >
          <option value="">— select —</option>
          {tokens.map(t => (
            <option key={t.token_id} value={t.token_id}>{t.token_id}</option>
          ))}
        </select>

        <span style={{ fontSize: 12, color: '#888' }}>Timeout:</span>
        <input
          type="number"
          value={timeoutSec}
          onChange={e => setTimeoutSec(parseInt(e.target.value) || 30)}
          style={{
            width: 60, padding: '5px 8px', background: '#0f0f0f', border: '1px solid #333',
            color: '#e0e0e0', fontSize: 13, borderRadius: 4, outline: 'none'
          }}
        />
        <span style={{ fontSize: 12, color: '#555' }}>sec</span>

        <button
          onClick={run}
          disabled={running || !selectedNode || !selectedToken || !status?.available}
          style={{
            padding: '5px 16px',
            background: running || !selectedNode || !selectedToken || !status?.available ? '#333' : '#5D3E8E',
            border: 'none', color: '#fff', fontSize: 13, borderRadius: 4,
            cursor: running || !selectedNode || !selectedToken || !status?.available ? 'default' : 'pointer',
            fontWeight: 600
          }}
        >
          {running ? 'Running...' : 'Run BsTool'}
        </button>

        {result && (
          <button
            onClick={() => setResult(null)}
            style={{
              padding: '5px 10px', background: 'none', border: '1px solid #333',
              color: '#555', fontSize: 12, borderRadius: 4, cursor: 'pointer'
            }}
          >Clear</button>
        )}
      </div>

      {error && (
        <div style={{ color: '#f44336', fontSize: 12, padding: '4px 8px', background: '#1a0000', borderRadius: 4 }}>
          {error}
        </div>
      )}

      {/* Output */}
      {result && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8, overflow: 'hidden' }}>
          <div style={{ display: 'flex', gap: 12, fontSize: 12 }}>
            <span style={{ color: result.exit_code === 0 ? '#4caf50' : '#f44336' }}>
              Exit: {result.exit_code}
            </span>
            {result.timed_out && <span style={{ color: '#ff9800' }}>⚠ Timed out</span>}
            <span style={{ color: '#555' }}>
              {result.output.split('\n').length} lines
            </span>
          </div>
          <div style={{
            flex: 1, background: '#0a0a0a', border: '1px solid #2a2a2a',
            borderRadius: 4, padding: '10px 12px', overflow: 'auto',
            fontFamily: 'Courier New, monospace', fontSize: 12,
            color: '#c0c0c0', whiteSpace: 'pre-wrap', wordBreak: 'break-all'
          }}>
            {result.output || '(no output)'}
          </div>
        </div>
      )}

      {!result && !running && (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ textAlign: 'center', color: '#333' }}>
            <div style={{ fontSize: 28, marginBottom: 8 }}>⚙</div>
            <div style={{ fontSize: 13 }}>Select node + token → Run BsTool</div>
          </div>
        </div>
      )}
    </div>
  )
}
