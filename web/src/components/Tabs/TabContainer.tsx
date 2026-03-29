import { useState } from 'react'
import { LogProcessorTab } from './LogProcessorTab'

const TABS = [
  { id: 'log-processor', label: 'Log Processor' },
  { id: 'commander', label: 'Commander' },
  { id: 'telnet', label: 'Telnet' },
  { id: 'scan', label: 'Scan' },
  { id: 'bstool', label: 'BsTool' },
  { id: 'sessions', label: 'Sessions' },
]

const PHASE_MAP: Record<string, string> = {
  'log-processor': 'P2',
  'commander': 'P3',
  'telnet': 'P3',
  'scan': 'P4',
  'bstool': 'P5',
  'sessions': 'P7',
}

export function TabContainer() {
  const [active, setActive] = useState('log-processor')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Tab bar */}
      <div style={{
        display: 'flex',
        background: '#0f0f0f',
        borderBottom: '1px solid #2a2a2a',
        overflow: 'auto'
      }}>
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setActive(t.id)}
            style={{
              padding: '8px 16px',
              background: active === t.id ? '#1a1a1a' : 'transparent',
              border: 'none',
              borderBottom: active === t.id ? '2px solid #5D3E8E' : '2px solid transparent',
              color: active === t.id ? '#e0e0e0' : '#666',
              cursor: 'pointer',
              fontSize: 13,
              whiteSpace: 'nowrap'
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {active === 'log-processor' ? (
          <LogProcessorTab />
        ) : (
          <div style={{ padding: 20, textAlign: 'center', marginTop: 80, color: '#888' }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>🔧</div>
            <div style={{ fontSize: 18, color: '#5D3E8E', fontWeight: 600, marginBottom: 8 }}>
              {TABS.find(t => t.id === active)?.label}
            </div>
            <div style={{ fontSize: 13, color: '#555' }}>
              Coming in Phase {PHASE_MAP[active]} — implementation in progress
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
