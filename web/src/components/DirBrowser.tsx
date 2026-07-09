import { useState, useEffect, useCallback } from 'react';
import { Folder, HardDrive, ChevronRight, ArrowUp, Loader2 } from 'lucide-react';

export interface DirBrowserProps {
  open: boolean;
  onSelect: (path: string) => void;
  onClose: () => void;
  title?: string;
  initialPath?: string;
  selectLabel?: string;
}

interface DirEntry {
  name: string;
  path: string;
  type: string; // "dir" or "drive"
}

export default function DirBrowser({
  open,
  onSelect,
  onClose,
  title = 'Browse Directory',
  initialPath = '',
  selectLabel = 'Select',
}: DirBrowserProps) {
  const [currentPath, setCurrentPath] = useState(initialPath);
  const [entries, setEntries] = useState<DirEntry[]>([]);
  const [parent, setParent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPath, setSelectedPath] = useState('');

  const fetchDir = useCallback(async (path: string) => {
    setLoading(true);
    setError(null);
    try {
      const url = `/api/v1/browse?path=${encodeURIComponent(path)}`;
      const res = await fetch(url);
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setEntries(data.entries || []);
      setParent(data.parent || '');
      setCurrentPath(data.path || path);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to browse');
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      // Try common starting points on Windows
      if (!initialPath) {
        // Check if C:\dna\CA\bu exists by trying to browse it
        fetchDir('C:\\dna\\CA\\bu');
      } else {
        fetchDir(initialPath);
      }
    }
  }, [open, initialPath, fetchDir]);

  if (!open) return null;

  function handleEntryClick(entry: DirEntry) {
    setSelectedPath(entry.path);
    fetchDir(entry.path);
  }

  function handleParentClick() {
    if (parent) {
      fetchDir(parent);
      setSelectedPath(parent);
    } else {
      // Go to drive list
      fetchDir('');
      setSelectedPath('');
    }
  }

  function handleSelect() {
    if (selectedPath || currentPath) {
      onSelect(selectedPath || currentPath);
      onClose();
    }
  }

  // Try common BU paths as quick buttons
  const quickPaths = [
    { label: 'C:\\dna\\CA\\bu', path: 'C:\\dna\\CA\\bu' },
    { label: 'D:\\dna\\CA\\bu', path: 'D:\\dna\\CA\\bu' },
    { label: 'C:\\', path: 'C:\\' },
    { label: 'D:\\', path: 'D:\\' },
  ];

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0,0,0,0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 2000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          width: '600px',
          maxHeight: '80vh',
          display: 'flex',
        flexDirection: 'column',
          boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Folder size={16} color="var(--accent)" />
          <span style={{ fontSize: '14px', fontWeight: 600 }}>{title}</span>
          <div style={{ flex: 1 }} />
          <button className="btn btn-ghost" style={{ fontSize: '12px', padding: '2px 8px' }} onClick={onClose}>✕</button>
        </div>

        {/* Quick paths */}
        <div style={{ padding: '6px 16px', borderBottom: '1px solid var(--border)', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {quickPaths.map((qp) => (
            <button
              key={qp.path}
              className="btn btn-ghost"
              style={{ fontSize: '11px', padding: '2px 8px', fontFamily: 'var(--font-mono)' }}
              onClick={() => { setSelectedPath(qp.path); fetchDir(qp.path); }}
            >
              {qp.label}
            </button>
          ))}
        </div>

        {/* Current path + parent button */}
        <div style={{ padding: '8px 16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className="btn btn-ghost"
            style={{ fontSize: '12px', padding: '2px 6px' }}
            onClick={handleParentClick}
            title="Go to parent directory"
          >
            <ArrowUp size={14} />
          </button>
          <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {currentPath || 'Drives'}
          </span>
        </div>

        {/* Directory listing */}
        <div style={{ flex: 1, overflow: 'auto', padding: '8px' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '24px' }}>
              <Loader2 size={20} color="var(--accent)" className="spin" />
            </div>
          ) : error ? (
            <div style={{ padding: '16px', color: 'var(--error)', fontSize: '12px' }}>{error}</div>
          ) : (
            entries.map((entry) => (
              <div
                key={entry.path}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '6px 12px',
                  cursor: 'pointer',
                  borderRadius: '4px',
                  backgroundColor: selectedPath === entry.path ? 'rgba(99,102,241,0.1)' : 'transparent',
                  transition: 'background-color 0.1s ease',
                }}
                onClick={() => handleEntryClick(entry)}
                onMouseEnter={(e) => { if (selectedPath !== entry.path) (e.currentTarget as HTMLElement).style.backgroundColor = 'rgba(255,255,255,0.03)'; }}
                onMouseLeave={(e) => { if (selectedPath !== entry.path) (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent'; }}
              >
                {entry.type === 'drive' ? (
                  <HardDrive size={14} color="var(--accent)" />
                ) : (
                  <Folder size={14} color="var(--text-secondary)" />
                )}
                <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)' }}>{entry.name}</span>
                <ChevronRight size={12} color="var(--text-muted)" style={{ marginLeft: 'auto' }} />
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: '10px 16px', borderTop: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {selectedPath || currentPath || '(no selection)'}
          </span>
          <button className="btn btn-ghost" style={{ fontSize: '12px' }} onClick={onClose}>Cancel</button>
          <button
            className="btn btn-primary"
            style={{ fontSize: '12px' }}
            onClick={handleSelect}
            disabled={!selectedPath && !currentPath}
          >
            {selectLabel}
          </button>
        </div>
      </div>
    </div>
  );
}