import React from 'react'
import { useLogStore } from '../../store/logStore'

const EXT_COLOR: Record<string, string> = {
  '.fbc': '#7a5aa0',
  '.rpc': '#4a8aa0',
  '.log': '#8aa04a',
  '.lis': '#a08a4a',
  '.txt': '#888',
}

export function LogProcessorTab() {
  const {
    rootPath, setRootPath,
    scanResult, scanning, generating, downloadUrl, error,
    scan, generate, clear
  } = useLogStore()

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') scan()
  }

  const title = rootPath ? `LOGReport - ${rootPath.split(/[\\/]/).pop() || rootPath}` : 'LOGReport'

  return (
    <div style={{ padding: 20, height: '100%', overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* Header */}
      <div style={{ fontSize: 16, fontWeight: 600, color: '#5D3E8E' }}>Log Processor</div>

      {/* Folder path input */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <div style={{ fontSize: 12, color: '#888', minWidth: 80 }}>Folder path:</div>
        <input
          value={rootPath}
          onChange={e => setRootPath(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g. C:\\DNA\\_DIA or /mnt/valmet/_DIA"
          style={{
            flex: 1, padding: '6px 10px',
            background: '#0f0f0f', border: '1px solid #333',
            color: '#e0e0e0', fontSize: 13, borderRadius: 4, outline: 'none'
          }}
        />
        <button
          onClick={scan}
          disabled={scanning || !rootPath}
          style={{
            padding: '6px 16px', background: scanning ? '#333' : '#5D3E8E',
            border: 'none', color: '#fff', fontSize: 13, borderRadius: 4,
            cursor: scanning || !rootPath ? 'default' : 'pointer'
          }}
        >
          {scanning ? 'Scanning...' : 'Scan'}
        </button>
        {scanResult && (
          <button onClick={clear} style={{
            padding: '6px 10px', background: 'none', border: '1px solid #444',
            color: '#888', fontSize: 12, borderRadius: 4, cursor: 'pointer'
          }}>Clear</button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div style={{ color: '#f44336', fontSize: 12, padding: '6px 10px', background: '#1a0000', borderRadius: 4 }}>
          {error}
        </div>
      )}

      {/* Scan results */}
      {scanResult && (
        <>
          <div style={{ fontSize: 12, color: '#888' }}>
            Found <span style={{ color: '#5D3E8E', fontWeight: 600 }}>{scanResult.total}</span> files
            in <span style={{ color: '#5D3E8E', fontWeight: 600 }}>{scanResult.groups.length}</span> groups
          </div>

          {/* File groups */}
          <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
            {scanResult.groups.map(group => (
              <div key={group.name} style={{ border: '1px solid #2a2a2a', borderRadius: 4 }}>
                <div style={{
                  padding: '6px 12px', background: '#1a1040',
                  fontSize: 13, fontWeight: 600, color: '#5D3E8E',
                  borderBottom: '1px solid #2a2a2a'
                }}>
                  {group.name}
                  <span style={{ fontWeight: 400, color: '#555', marginLeft: 8, fontSize: 11 }}>
                    {group.files.length} files
                  </span>
                </div>
                <div style={{ padding: '4px 0' }}>
                  {group.files.map(f => (
                    <div key={f.path} style={{
                      padding: '3px 12px', display: 'flex', gap: 10, alignItems: 'center'
                    }}>
                      <span style={{
                        fontSize: 11, color: EXT_COLOR[f.ext] || '#888',
                        fontWeight: 600, minWidth: 32
                      }}>{f.ext.replace('.','').toUpperCase()}</span>
                      <span style={{ fontSize: 12, color: '#ccc' }}>{f.name}</span>
                      <span style={{ fontSize: 11, color: '#555', marginLeft: 'auto' }}>
                        {(f.size / 1024).toFixed(1)}KB
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Generate button */}
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <button
              onClick={() => generate(title)}
              disabled={generating}
              style={{
                padding: '8px 20px', background: generating ? '#333' : '#5D3E8E',
                border: 'none', color: '#fff', fontSize: 13, borderRadius: 4,
                cursor: generating ? 'default' : 'pointer', fontWeight: 600
              }}
            >
              {generating ? 'Generating...' : 'Generate PDF'}
            </button>

            {downloadUrl && (
              <a
                href={downloadUrl}
                download="logreport.pdf"
                style={{
                  padding: '8px 16px', background: '#1a4a1a', border: '1px solid #2a6a2a',
                  color: '#4caf50', fontSize: 13, borderRadius: 4, textDecoration: 'none',
                  fontWeight: 600
                }}
              >
                ⬇ Download PDF
              </a>
            )}
          </div>
        </>
      )}
    </div>
  )
}