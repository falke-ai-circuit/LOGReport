import { useState } from 'react'
import { LogProcessorTab } from './LogProcessorTab'
import { CommanderTab } from './CommanderTab'
import { TelnetTab } from './TelnetTab'
import { ScanTab } from './ScanTab'
import { BstoolTab } from './BstoolTab'
import { SessionsTab } from './SessionsTab'

const TABS = [
  { id: 'log-processor', label: 'Log Processor' },
  { id: 'commander', label: 'Commander' },
  { id: 'telnet', label: 'Telnet' },
  { id: 'scan', label: 'Scan' },
  { id: 'bstool', label: 'BsTool' },
  { id: 'sessions', label: 'Sessions' },
]

export function TabContainer() {
  const [active, setActive] = useState('log-processor')

  const renderTab = () => {
    switch (active) {
      case 'log-processor': return <LogProcessorTab />
      case 'commander':    return <CommanderTab />
      case 'telnet':       return <TelnetTab />
      case 'scan':         return <ScanTab />
      case 'bstool':       return <BstoolTab />
      case 'sessions':     return <SessionsTab />
      default:             return null
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
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

      <div style={{ flex: 1, overflow: 'auto' }}>
        {renderTab()}
      </div>
    </div>
  )
}
