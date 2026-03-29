import { useState, useEffect } from 'react'
import { sessionsApi, SessionRecord } from '../../api/sessions'

export function SessionsTab() {
  const [sessions, setSessions] = useState<SessionRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const r = await sessionsApi.list()
      setSessions(r.sessions || [])
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  const clear = async () => {
    await sessionsApi.clear()
    setSessions([])
  }

  useEffect(() => { load() }, [])

  const fmt = (iso: string) => {
    try {
      return new Date(iso).toLocaleTimeString()
    } catch { return iso }
  }

  const duration = (start: string, end?: string) => {
    try {
      const s = new Date(start).getTime()
      const e = end ? new Date(end).getTime() : Date.now()
      const ms = e - s
      if (ms < 1000) return `${ms}ms`
      return `${(ms / 1000).toFixed(1)}s`
    } catch { return '—' }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 16, gap: 12 }}>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ fontSize: 16, fontWeight: 600, color: '#5D3E8E' }}>Sessions</div>
        <button
          onClick={load}
          disabled={loading}
          style={{
            padding: '4px 12px', background: '#1a1a1a', border: '1px solid #333',
            color: '#888', fontSize: 12, borderRadius: 4, cursor: 'pointer'
          }}
        >
          {loading ? '...' : '↺ Refresh'}
        </button>
        {sessions.length > 0 && (
          <button
            onClick={clear}
            style={{
              padding: '4px 12px', background: 'none', border: '1px solid #4a2a2a',
              color: '#f44336', fontSize: 12, borderRadius: 4, cursor: 'pointer'
            }}
          >
            Clear All
          </button>
        )}
        <span style={{ fontSize: 12, color: '#555', marginLeft: 'auto' }}>
          {sessions.length} session{sessions.length !== 1 ? 's' : ''} recorded
        </span>
      </div>

      {error && (
        <div style={{ color: '#f44336', fontSize: 12, padding: '4px 8px', background: '#1a0000', borderRadius: 4 }}>
          {error}
        </div>
      )}

      {sessions.length === 0 && !loading && (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ textAlign: 'center', color: '#333' }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>📋</div>
            <div style={{ fontSize: 13 }}>No sessions recorded yet</div>
            <div style={{ fontSize: 12, marginTop: 4, color: '#2a2a2a' }}>
              Telnet + BsTool activity will appear here
            </div>
          </div>
        </div>
      )}

      {sessions.length > 0 && (
        <div style={{ flex: 1, overflow: 'auto', border: '1px solid #2a2a2a', borderRadius: 4 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead>
              <tr style={{ background: '#111', position: 'sticky', top: 0 }}>
                {['Kind', 'Node', 'IP', 'Token', 'Started', 'Duration', 'Lines', 'Status'].map(h => (
                  <th key={h} style={{ padding: '6px 10px', textAlign: 'left', color: '#555', fontWeight: 600, whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sessions.map((s, i) => (
                <tr key={s.id} style={{ background: i % 2 === 0 ? 'transparent' : '#0d0d0d' }}>
                  <td style={{ padding: '4px 10px' }}>
                    <span style={{
                      padding: '2px 6px', borderRadius: 3, fontSize: 11, fontWeight: 600,
                      background: s.kind === 'telnet' ? '#1a1040' : '#0d1a0d',
                      color: s.kind === 'telnet' ? '#7a5aa0' : '#4caf50'
                    }}>
                      {s.kind.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: '4px 10px', color: '#e0e0e0' }}>{s.node_name || '—'}</td>
                  <td style={{ padding: '4px 10px', color: '#888', fontFamily: 'monospace' }}>{s.ip}</td>
                  <td style={{ padding: '4px 10px', color: '#555' }}>{s.token || '—'}</td>
                  <td style={{ padding: '4px 10px', color: '#666', whiteSpace: 'nowrap' }}>{fmt(s.started_at)}</td>
                  <td style={{ padding: '4px 10px', color: '#666', fontFamily: 'monospace' }}>
                    {duration(s.started_at, s.ended_at)}
                  </td>
                  <td style={{ padding: '4px 10px', color: '#555' }}>{s.lines || '—'}</td>
                  <td style={{ padding: '4px 10px' }}>
                    <span style={{ color: s.active ? '#4caf50' : '#555' }}>
                      {s.active ? '● active' : '○ ended'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
