import { useEffect, useState } from 'react'
import { useNodesStore } from '../../store/nodesStore'
import type { Node } from '../../types/node'

const STATUS_COLOR: Record<string, string> = {
  online: '#4caf50',
  offline: '#f44336',
  scanning: '#ff9800',
  error: '#e91e63'
}

function NodeItem({ node }: { node: Node }) {
  const [expanded, setExpanded] = useState(false)
  const selectNode = useNodesStore(s => s.selectNode)
  const selected = useNodesStore(s => s.selectedNode?.name === node.name)

  return (
    <div>
      <div
        onClick={() => { setExpanded(!expanded); selectNode(node) }}
        style={{
          padding: '6px 10px',
          cursor: 'pointer',
          background: selected ? '#2a1a4a' : 'transparent',
          borderLeft: selected ? '3px solid #5D3E8E' : '3px solid transparent',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          userSelect: 'none'
        }}
      >
        <span style={{ fontSize: 10, color: STATUS_COLOR[node.status] || '#888' }}>●</span>
        <span style={{ fontSize: 13, fontWeight: 500 }}>{node.name}</span>
        <span style={{ fontSize: 11, color: '#888', marginLeft: 'auto' }}>{node.ip_address}</span>
        <span style={{ fontSize: 11, color: '#555' }}>{expanded ? '▼' : '▶'}</span>
      </div>
      {expanded && (
        <div style={{ paddingLeft: 24, borderLeft: '1px solid #333', marginLeft: 14 }}>
          {node.tokens.map(t => (
            <div key={`${t.token_id}-${t.token_type}`} style={{ padding: '3px 8px', fontSize: 12, color: '#aaa' }}>
              <span style={{ color: '#7a5aa0' }}>{t.token_type}</span>
              {' '}{t.token_id}
              <span style={{ color: '#555', marginLeft: 8 }}>:{t.port}</span>
            </div>
          ))}
          {node.tokens.length === 0 && (
            <div style={{ padding: '3px 8px', fontSize: 12, color: '#555' }}>no tokens</div>
          )}
        </div>
      )}
    </div>
  )
}

export function NodeTree() {
  const { nodes, loading, error, fetchNodes } = useNodesStore()

  useEffect(() => { fetchNodes() }, [fetchNodes])

  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      <div style={{
        padding: '8px 10px',
        fontSize: 11,
        fontWeight: 600,
        color: '#5D3E8E',
        letterSpacing: 1,
        borderBottom: '1px solid #2a2a2a',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span>NODES</span>
        <button onClick={fetchNodes} style={{
          background: 'none', border: '1px solid #333', color: '#888',
          fontSize: 10, padding: '2px 6px', cursor: 'pointer', borderRadius: 3
        }}>↺</button>
      </div>
      {loading && <div style={{ padding: 10, color: '#555', fontSize: 12 }}>Loading...</div>}
      {error && <div style={{ padding: 10, color: '#f44336', fontSize: 12 }}>{error}</div>}
      {!loading && nodes.map(n => <NodeItem key={n.name} node={n} />)}
      {!loading && !error && nodes.length === 0 && (
        <div style={{ padding: 10, color: '#555', fontSize: 12 }}>No nodes. Load nodes.json.</div>
      )}
    </div>
  )
}
