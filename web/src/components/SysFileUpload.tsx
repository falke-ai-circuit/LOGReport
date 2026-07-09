import { useState, useRef, useCallback } from 'react';
import { Upload, FileText, Loader2, AlertCircle, CheckCircle2, X } from 'lucide-react';

interface SysFileEntry {
  lid: string;
  node_type: string;
  description: string;
}

interface ParseResponse {
  filename: string;
  file_size_bytes: number;
  parsed_at: string;
  entries: SysFileEntry[];
  total_entries: number;
  nodes_created: number;
}

type UploadState = 'idle' | 'dragging' | 'uploading' | 'success' | 'error';

export default function SysFileUpload() {
  const [state, setState] = useState<UploadState>('idle');
  const [result, setResult] = useState<ParseResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropRef = useRef<HTMLDivElement>(null);

  const handleFile = useCallback(async (file: File) => {
    // Validate file extension
    if (!file.name.toLowerCase().endsWith('.sys')) {
      setError('Only .sys files are supported');
      setState('error');
      return;
    }

    setSelectedFile(file);
    setState('uploading');
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch('/api/v1/parse/sysfile', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Upload failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }

      const data: ParseResponse = await res.json();
      setResult(data);
      setState('success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      setState('error');
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setState('idle');

      const file = e.dataTransfer.files[0];
      if (file) {
        handleFile(file);
      }
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setState('dragging');
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setState('idle');
  }, []);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        handleFile(file);
      }
    },
    [handleFile]
  );

  const reset = useCallback(() => {
    setState('idle');
    setResult(null);
    setError(null);
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '24px',
        }}
      >
        <FileText size={24} color="var(--accent)" />
        <h1 style={{ fontSize: '24px', fontWeight: 700 }}>SysFile Upload</h1>
      </div>

      <p style={{ color: 'var(--text-secondary)', marginBottom: '24px', fontSize: '14px' }}>
        Upload a <code style={codeStyle}>.sys</code> file to parse node entries. Drag and drop or
        click to select a file.
      </p>

      {/* Drop zone */}
      <div
        ref={dropRef}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${
            state === 'dragging'
              ? 'var(--accent)'
              : state === 'error'
              ? 'var(--error)'
              : state === 'success'
              ? 'var(--success)'
              : 'var(--border-light)'
          }`,
          borderRadius: '12px',
          padding: '48px 24px',
          textAlign: 'center',
          cursor: 'pointer',
          backgroundColor:
            state === 'dragging'
              ? 'rgba(245,158,11,0.08)'
              : 'var(--bg-card)',
          transition: 'all 0.2s ease',
          marginBottom: '24px',
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".sys"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />

        {state === 'idle' && (
          <>
            <Upload
              size={40}
              color="var(--text-muted)"
              style={{ marginBottom: '12px' }}
            />
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '4px' }}>
              Drag and drop a <code style={codeStyle}>.sys</code> file here
            </p>
            <p style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
              or click to browse
            </p>
          </>
        )}

        {state === 'dragging' && (
          <>
            <Upload
              size={40}
              color="var(--accent)"
              style={{ marginBottom: '12px' }}
            />
            <p style={{ color: 'var(--accent)', fontSize: '14px', fontWeight: 600 }}>
              Drop file to parse
            </p>
          </>
        )}

        {state === 'uploading' && (
          <>
            <Loader2
              size={40}
              color="var(--accent)"
              style={{
                animation: 'spin 1s linear infinite',
                marginBottom: '12px',
              }}
            />
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
              Parsing <strong>{selectedFile?.name}</strong>...
            </p>
            <p style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: '4px' }}>
              {selectedFile ? formatSize(selectedFile.size) : ''}
            </p>
          </>
        )}

        {state === 'success' && (
          <>
            <CheckCircle2
              size={40}
              color="var(--success)"
              style={{ marginBottom: '12px' }}
            />
            <p style={{ color: 'var(--success)', fontSize: '14px', fontWeight: 600 }}>
              Parsed successfully
            </p>
            <p style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '4px' }}>
              {result?.total_entries} entries found
            </p>
          </>
        )}

        {state === 'error' && (
          <>
            <AlertCircle
              size={40}
              color="var(--error)"
              style={{ marginBottom: '12px' }}
            />
            <p style={{ color: 'var(--error)', fontSize: '14px', fontWeight: 600 }}>
              Parse failed
            </p>
            <p style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '4px' }}>
              {error}
            </p>
          </>
        )}
      </div>

      {/* Results */}
      {result && state === 'success' && (
        <div className="card-elevated" style={{ padding: '20px' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '16px',
            }}
          >
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '4px' }}>
                Parse Results
              </h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                {result.filename} &middot; {formatSize(result.file_size_bytes)} &middot;{' '}
                {result.total_entries} entries
              </p>
            </div>
            <button className="btn btn-ghost" onClick={reset} style={{ padding: '4px' }}>
              <X size={18} />
            </button>
          </div>

          {/* Entry table */}
          <div style={{ overflowX: 'auto' }}>
            <table
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '13px',
              }}
            >
              <thead>
                <tr
                  style={{
                    borderBottom: '1px solid var(--border)',
                    textAlign: 'left',
                  }}
                >
                  <th style={thStyle}>LID</th>
                  <th style={thStyle}>Node Type</th>
                  <th style={thStyle}>Description</th>
                </tr>
              </thead>
              <tbody>
                {result.entries.map((entry, i) => (
                  <tr
                    key={i}
                    style={{
                      borderBottom: '1px solid var(--border)',
                    }}
                  >
                    <td style={tdStyle}>
                      <code style={codeStyle}>{entry.lid}</code>
                    </td>
                    <td style={tdStyle}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          backgroundColor: 'var(--bg-secondary)',
                          color: 'var(--accent)',
                          fontFamily: 'var(--font-mono)',
                          fontSize: '12px',
                          fontWeight: 500,
                        }}
                      >
                        {entry.node_type}
                      </span>
                    </td>
                    <td style={{ ...tdStyle, color: 'var(--text-secondary)' }}>
                      {entry.description || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {result.entries.length === 0 && (
            <div
              style={{
                textAlign: 'center',
                padding: '32px',
                color: 'var(--text-muted)',
              }}
            >
              No entries found in this file.
            </div>
          )}
        </div>
      )}

      {/* Error state (standalone, not in drop zone) */}
      {state === 'error' && !selectedFile && (
        <div
          className="card"
          style={{
            textAlign: 'center',
            padding: '32px',
            borderColor: 'var(--error)',
          }}
        >
          <AlertCircle
            size={24}
            color="var(--error)"
            style={{ marginBottom: '8px' }}
          />
          <p style={{ color: 'var(--error)', marginBottom: '12px' }}>{error}</p>
          <button className="btn btn-secondary" onClick={reset}>
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}

const codeStyle: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  backgroundColor: 'var(--bg-secondary)',
  padding: '1px 6px',
  borderRadius: '4px',
  fontSize: '13px',
  color: 'var(--accent)',
};

const thStyle: React.CSSProperties = {
  padding: '10px 12px',
  fontWeight: 600,
  color: 'var(--text-secondary)',
  fontSize: '12px',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
};

const tdStyle: React.CSSProperties = {
  padding: '10px 12px',
  color: 'var(--text-primary)',
};
