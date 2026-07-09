import React, { useEffect, useRef } from 'react'
import { useTelnetStore } from '../../store/telnetStore'

const LINE_COLOR: Record<string, string> = {
  cmd: '#5D3E8E',
  out: '#e0e0e0',
  err: '#f44336',
  info: '#888',
}

export function TelnetTab() {
  const {
    ip, port, session, connecting, lines, inputCmd, contextToken, error,
    setIP, setPort, setInputCmd, setContextToken,
    connect, disconnect, sendCommand, clearTerminal
  } = useTelnetStore()

  const termRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-scroll terminal
  useEffect(() => {
    if (termRef.current) {
      termRef.current.scrollTop = termRef.current.scrollHeight
    }
  }, [lines])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') sendCommand()
  }

  const connected = session?.connected

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 16, gap: 12 }}>

      {/* Header */}
      <div style={{ fontSize: 16, fontWeight: 600, color: '#5D3E8E' }}>Telnet Terminal</div>

      {/* Connection bar */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ fontSize: 12, color: '#888' }}>IP:</span>
        <input
          value={ip}
          onChange={e => setIP(e.target.value)}
          placeholder="192.168.1.40"
          disabled={!!connected}
          style={{
            width: 140, padding: '5px 8px', background: '#0f0f0f',
            border: '1px solid #333', color: '#e0e0e0', fontSize: 13,
            borderRadius: 4, outline: 'none'
          }}
        />
        <span style={{ fontSize: 12, color: '#888' }}>Port:</span>
        <input
          value={port}
          onChange={e => setPort(parseInt(e.target.value) || 23)}
          disabled={!!connected}
          style={{
            width: 70, padding: '5px 8px', background: '#0f0f0f',
            border: '1px solid #333', color: '#e0e0e0', fontSize: 13,
            borderRadius: 4, outline: 'none'
          }}
        />
        <span style={{ fontSize: 12, color: '#888' }}>Token:</span>
        <input
          value={contextToken}
          onChange={e => setContextToken(e.target.value)}
          placeholder="162"
          style={{
            width: 80, padding: '5px 8px', background: '#0f0f0f',
            border: '1px solid #333', color: '#e0e0e0', fontSize: 13,
            borderRadius: 4, outline: 'none'
          }}
        />
        {!connected ? (
          <button
            onClick={connect}
            disabled={connecting || !ip}
            style={{
              padding: '5px 14px', background: connecting ? '#333' : '#5D3E8E',
              border: 'none', color: '#fff', fontSize: 13, borderRadius: 4,
              cursor: connecting || !ip ? 'default' : 'pointer'
            }}
          >
            {connecting ? 'Connecting...' : 'Connect'}
          </button>
        ) : (
          <button
            onClick={disconnect}
            style={{
              padding: '5px 14px', background: '#4a1a1a',
              border: '1px solid #7a2a2a', color: '#f44336',
              fontSize: 13, borderRadius: 4, cursor: 'pointer'
            }}
          >
            Disconnect
          </button>
        )}
        {connected && (
          <span style={{ fontSize: 11, color: '#4caf50', marginLeft: 4 }}>
            ● Connected to {session?.addr || ip}
          </span>
        )}
        <button
          onClick={clearTerminal}
          style={{
            marginLeft: 'auto', padding: '5px 10px', background: 'none',
            border: '1px solid #333', color: '#555', fontSize: 11,
            borderRadius: 4, cursor: 'pointer'
          }}
        >
          Clear
        </button>
      </div>

      {/* Error banner */}
      {error && (
        <div style={{ color: '#f44336', fontSize: 12, padding: '4px 8px', background: '#1a0000', borderRadius: 4 }}>
          {error}
        </div>
      )}

      {/* Terminal output */}
      <div
        ref={termRef}
        style={{
          flex: 1, background: '#0a0a0a', border: '1px solid #2a2a2a',
          borderRadius: 4, padding: '10px 12px', overflow: 'auto',
          fontFamily: 'Courier New, monospace', fontSize: 12
        }}
      >
        {lines.length === 0 && (
          <div style={{ color: '#333' }}>Connect to a DNA node to begin. Use aliases: ps, fis, rc, {'{token} fis'}</div>
        )}
        {lines.map((l, i) => (
          <div key={i} style={{ color: LINE_COLOR[l.type], lineHeight: 1.5, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
            {l.text}
          </div>
        ))}
      </div>

      {/* Command input */}
      <div style={{ display: 'flex', gap: 8 }}>
        <span style={{ color: '#5D3E8E', fontFamily: 'monospace', lineHeight: '32px', fontSize: 14 }}>{'>'}</span>
        <input
          ref={inputRef}
          value={inputCmd}
          onChange={e => setInputCmd(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={connected ? 'Enter command (ps, fis, rc, or raw)...' : 'Connect first'}
          disabled={!connected}
          style={{
            flex: 1, padding: '6px 10px', background: '#0f0f0f',
            border: '1px solid ' + (connected ? '#5D3E8E' : '#222'),
            color: '#e0e0e0', fontSize: 13, borderRadius: 4,
            outline: 'none', fontFamily: 'monospace'
          }}
        />
        <button
          onClick={sendCommand}
          disabled={!connected || !inputCmd.trim()}
          style={{
            padding: '6px 16px',
            background: connected && inputCmd.trim() ? '#5D3E8E' : '#333',
            border: 'none', color: '#fff', fontSize: 13,
            borderRadius: 4, cursor: connected && inputCmd.trim() ? 'pointer' : 'default'
          }}
        >
          Send
        </button>
      </div>

      {/* Command hints */}
      <div style={{ fontSize: 11, color: '#444', display: 'flex', gap: 16 }}>
        <span><span style={{ color: '#5D3E8E' }}>ps</span> → show all</span>
        <span><span style={{ color: '#5D3E8E' }}>fis</span> → print_fieldbus {'{token}'}0000</span>
        <span><span style={{ color: '#5D3E8E' }}>rc</span> → print_fieldbus_rupi_counters {'{token}'}0000</span>
        <span><span style={{ color: '#5D3E8E' }}>{'{token} fis'}</span> → with token</span>
      </div>
    </div>
  )
}
