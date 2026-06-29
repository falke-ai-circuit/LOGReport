import { useState, useCallback } from 'react';
import { Terminal, Server, ScanLine, Settings, FolderOpen, Loader2, FileText, Upload } from 'lucide-react';
import NodeTree from './NodeTree';
import TelnetTerminal from './TelnetTerminal';
import BsToolPanel from './BsToolPanel';
import ScanTab from './ScanTab';
import CommandQueueBar from './CommandQueueBar';
import NodeConfigDialog from './NodeConfigDialog';
import type { TreeNodeData, QueueStatusResponse } from '../types/api';

type Tab = 'telnet' | 'bstool' | 'scan' | 'logviewer';

// Strip suffix from node name: "AP01m" → "AP01", "AP01r" → "AP01"
function stripNodeSuffix(name: string): string {
  return name.replace(/[mr]$/, '');
}

export default function CommanderLayout() {
  const [activeTab, setActiveTab] = useState<Tab>('telnet');
  const [selectedNode, setSelectedNode] = useState<TreeNodeData | null>(null);
  const [, setSelectedToken] = useState<TreeNodeData | null>(null);
  const [currentToken, setCurrentToken] = useState('');
  const [currentTokenType, setCurrentTokenType] = useState('');
  const [currentNodeName, setCurrentNodeName] = useState('');
  const [pendingCommand, setPendingCommand] = useState<string | null>(null);
  const [pendingServerName, setPendingServerName] = useState<string | null>(null);
  const [queueStatus, setQueueStatus] = useState<QueueStatusResponse | null>(null);
  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [logRoot, setLogRoot] = useState<string>(localStorage.getItem('logRoot') || '');
  const [showLogRootInput, setShowLogRootInput] = useState(false);
  const [logRootInput, setLogRootInput] = useState('');
  const [logRootLoading, setLogRootLoading] = useState(false);
  const [logRootError, setLogRootError] = useState<string | null>(null);

  // Sys file scan state
  const [showSysScan, setShowSysScan] = useState(false);
  const [sysDir, setSysDir] = useState(localStorage.getItem('sysDir') || '');
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<{ count: number; totalBefore: number; configs: unknown[] } | null>(null);
  const [scanError, setScanError] = useState<string | null>(null);
  const [includeLIS, setIncludeLIS] = useState(false);

  // File viewer state
  const [fileContent, setFileContent] = useState<string>('');
  const [fileViewName, setFileViewName] = useState<string>('');
  const [fileViewPath, setFileViewPath] = useState<string>('');
  const [fileLoading, setFileLoading] = useState(false);

  // Terminal output log (accumulated from single-command execution via context menu)
  const [terminalLog, setTerminalLog] = useState<string[]>([]);

  // ─── Node tree callbacks ─────────────────────────────────────

  const handleSelectNode = useCallback((node: TreeNodeData) => {
    setSelectedNode(node);
    setCurrentNodeName(node.name);
  }, []);

  const handleSelectToken = useCallback((token: TreeNodeData) => {
    setSelectedToken(token);
    setCurrentToken(token.token_id || '');
    setCurrentTokenType(token.section_type || 'FBC');
  }, []);

  // ─── Double-click file → open content in log viewer ─────────

  const handleDoubleClickFile = useCallback(async (node: TreeNodeData) => {
    if (!node.file_path) return;
    setFileLoading(true);
    setFileViewName(node.file_name || node.name);
    setFileViewPath(node.file_path);
    setActiveTab('logviewer');
    try {
      const res = await fetch(`/api/v1/logs/content?path=${encodeURIComponent(node.file_path)}`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Failed' }));
        setFileContent(`Error: ${data.message || res.statusText}`);
        return;
      }
      const data = await res.json();
      setFileContent(data.content || '(empty file)');
    } catch (err) {
      setFileContent(`Error loading file: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setFileLoading(false);
    }
  }, []);

  // ─── Context menu actions (context-aware) ────────────────────

  const handleContextAction = useCallback(
    async (action: string, node: TreeNodeData) => {
      const nodeName = node.name || currentNodeName;
      const tokenId = node.token_id || '';

      switch (action) {
        case 'print_all': {
          setActiveTab('telnet');
          fetch('/api/v1/commandqueue/batch-node', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ node_name: nodeName }),
          }).then(() => {
            fetch('/api/v1/commandqueue/start', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: '{}',
            });
          }).catch(err => console.error('batch-node error:', err));
          break;
        }
        case 'fbc_print_all': {
          setActiveTab('telnet');
          fetch('/api/v1/commandqueue/batch-node', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ node_name: nodeName, token_type: 'FBC' }),
          }).then(() => {
            fetch('/api/v1/commandqueue/start', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: '{}',
            });
          }).catch(err => console.error('fbc_batch error:', err));
          break;
        }
        case 'rpc_print_all': {
          setActiveTab('telnet');
          fetch('/api/v1/commandqueue/batch-node', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ node_name: nodeName, token_type: 'RPC' }),
          }).then(() => {
            fetch('/api/v1/commandqueue/start', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: '{}',
            });
          }).catch(err => console.error('rpc_batch error:', err));
          break;
        }
        case 'fbc_print': {
          // Execute single FBC command via telnet, show output in terminal
          // Uses the full DIA command: "print from fbc io structure {token}0000"
          const cmd = `print from fbc io structure ${tokenId}0000`;
          setActiveTab('telnet');
          setTerminalLog(prev => [...prev, `> ${cmd}`]);
          try {
            const res = await fetch('/api/v1/telnet/execute', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ command: cmd }),
            });
            const data = await res.json();
            if (data.output) {
              setTerminalLog(prev => [...prev, data.output]);
            }
          } catch (err) {
            setTerminalLog(prev => [...prev, `Error: ${err instanceof Error ? err.message : String(err)}`]);
          }
          break;
        }
        case 'rpc_print': {
          // Execute single RPC command: "print from fbc rupi counters {token}0000"
          const cmd = `print from fbc rupi counters ${tokenId}0000`;
          setActiveTab('telnet');
          setTerminalLog(prev => [...prev, `> ${cmd}`]);
          try {
            const res = await fetch('/api/v1/telnet/execute', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ command: cmd }),
            });
            const data = await res.json();
            if (data.output) {
              setTerminalLog(prev => [...prev, data.output]);
            }
          } catch (err) {
            setTerminalLog(prev => [...prev, `Error: ${err instanceof Error ? err.message : String(err)}`]);
          }
          break;
        }
        case 'rpc_clear': {
          // Clear RPC counters: "clear fbc rupi counters {token}0000"
          const cmd = `clear fbc rupi counters ${tokenId}0000`;
          setActiveTab('telnet');
          setTerminalLog(prev => [...prev, `> ${cmd}`]);
          try {
            const res = await fetch('/api/v1/telnet/execute', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ command: cmd }),
            });
            const data = await res.json();
            if (data.output) {
              setTerminalLog(prev => [...prev, data.output]);
            }
          } catch (err) {
            setTerminalLog(prev => [...prev, `Error: ${err instanceof Error ? err.message : String(err)}`]);
          }
          break;
        }
        case 'bstool_errlog': {
          setActiveTab('bstool');
          setPendingServerName(stripNodeSuffix(nodeName));
          break;
        }
        case 'open_file': {
          handleDoubleClickFile(node);
          break;
        }
        case 'fbc_scan':
        case 'rpc_scan': {
          setActiveTab('scan');
          break;
        }
        case 'clear_logs':
          break;
      }
    },
    [currentNodeName, handleDoubleClickFile],
  );

  // ─── Set Log Root ──────────────────────────────────────────────

  const handleSetLogRoot = useCallback(async () => {
    if (!logRootInput) {
      setLogRootError('Path is required');
      return;
    }
    setLogRootLoading(true);
    setLogRootError(null);
    try {
      const res = await fetch('/api/v1/logs/setroot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: logRootInput }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      localStorage.setItem('logRoot', logRootInput);
      setLogRoot(logRootInput);
      setShowLogRootInput(false);
      setLogRootInput('');
    } catch (err) {
      setLogRootError(err instanceof Error ? err.message : 'Failed to set log root');
    } finally {
      setLogRootLoading(false);
    }
  }, [logRootInput]);

  // ─── Sys file scan + ingest ────────────────────────────────────

  const handleSysScan = useCallback(async () => {
    if (!sysDir) {
      setScanError('Directory is required');
      return;
    }
    setScanning(true);
    setScanError(null);
    setScanResult(null);
    try {
      const lisParam = includeLIS ? '&include_lis=true' : '';
      const res = await fetch(`/api/v1/sysfiles/scan?dir=${encodeURIComponent(sysDir)}${lisParam}`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Scan failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setScanResult({ count: data.count, totalBefore: data.total_before_filter, configs: data.configs });
      localStorage.setItem('sysDir', sysDir);
    } catch (err) {
      setScanError(err instanceof Error ? err.message : 'Scan failed');
    } finally {
      setScanning(false);
    }
  }, [sysDir, includeLIS]);

  const handleSaveNodes = useCallback(async () => {
    if (!scanResult?.configs) return;
    try {
      const res = await fetch('/api/v1/nodesconfig', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(scanResult.configs),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Save failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      // Refresh tree by reloading
      setShowSysScan(false);
      setScanResult(null);
      // Trigger tree reload via key change
      window.location.reload();
    } catch (err) {
      setScanError(err instanceof Error ? err.message : 'Save failed');
    }
  }, [scanResult]);

  // ─── Tab bar ────────────────────────────────────────────────────

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'telnet', label: 'Telnet', icon: <Terminal size={14} /> },
    { id: 'bstool', label: 'BsTool', icon: <Server size={14} /> },
    { id: 'scan', label: 'Scan', icon: <ScanLine size={14} /> },
    { id: 'logviewer', label: 'Log Viewer', icon: <FileText size={14} /> },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '8px 16px',
          borderBottom: '1px solid var(--border)',
          backgroundColor: 'var(--bg-secondary)',
        }}
      >
        <Terminal size={18} color="var(--accent)" />
        <h1 style={{ fontSize: '16px', fontWeight: 700 }}>Commander</h1>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          Interactive Command Center
        </span>
        <div style={{ flex: 1 }} />
        {/* Log Root indicator + Set Log Root button */}
        {logRoot ? (
          <span
            style={{
              fontSize: '11px',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              maxWidth: '200px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={logRoot}
          >
            📁 {logRoot.split('/').pop() || logRoot}
          </span>
        ) : null}
        <button
          className="btn btn-ghost"
          style={{ fontSize: '12px', padding: '4px 8px' }}
          onClick={() => {
            setLogRootInput(logRoot || '');
            setShowLogRootInput(!showLogRootInput);
          }}
          title="Set log root directory for scan and report workflows"
        >
          <FolderOpen size={14} />
          Set Log Root
        </button>
        {showLogRootInput && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <input
              type="text"
              value={logRootInput}
              onChange={(e) => setLogRootInput(e.target.value)}
              placeholder="/path/to/log/files"
              style={{
                fontSize: '12px',
                padding: '4px 8px',
                width: '250px',
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSetLogRoot();
                if (e.key === 'Escape') setShowLogRootInput(false);
              }}
              autoFocus
            />
            <button
              className="btn btn-primary"
              style={{ fontSize: '12px', padding: '4px 10px' }}
              onClick={handleSetLogRoot}
              disabled={logRootLoading}
            >
              {logRootLoading ? <Loader2 size={12} className="spin" /> : 'OK'}
            </button>
            {logRootError && (
              <span style={{ fontSize: '11px', color: 'var(--error)' }}>
                {logRootError}
              </span>
            )}
          </div>
        )}
        <button
          className="btn btn-ghost"
          style={{ fontSize: '12px', padding: '4px 8px' }}
          onClick={() => setShowSysScan(!showSysScan)}
          title="Scan .sys files from BU directory and ingest nodes"
        >
          <Upload size={14} />
          Ingest Nodes
        </button>
        <button
          className="btn btn-ghost"
          style={{ fontSize: '12px', padding: '4px 8px' }}
          onClick={() => setShowConfigDialog(true)}
          title="Configure nodes and tokens"
        >
          <Settings size={14} />
          Config
        </button>
      </div>

      {/* Sys file scan panel */}
      {showSysScan && (
        <div
          style={{
            padding: '12px 16px',
            borderBottom: '1px solid var(--border)',
            backgroundColor: 'var(--bg-secondary)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <Upload size={14} color="var(--accent)" />
            <span style={{ fontSize: '12px', fontWeight: 600 }}>Scan .sys files from BU directory</span>
            <div style={{ flex: 1 }} />
            <input
              type="text"
              value={sysDir}
              onChange={(e) => setSysDir(e.target.value)}
              placeholder="C:\dna\CA\bu or path to _SYS directory"
              style={{
                fontSize: '12px',
                padding: '4px 8px',
                width: '300px',
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
              }}
              onKeyDown={(e) => { if (e.key === 'Enter') handleSysScan(); }}
            />
            <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <input
                type="checkbox"
                checked={includeLIS}
                onChange={(e) => setIncludeLIS(e.target.checked)}
              />
              Include LIS
            </label>
            <button
              className="btn btn-primary"
              style={{ fontSize: '12px', padding: '4px 12px' }}
              onClick={handleSysScan}
              disabled={scanning}
            >
              {scanning ? <Loader2 size={12} className="spin" /> : 'Scan'}
            </button>
            {scanResult && (
              <button
                className="btn btn-primary"
                style={{ fontSize: '12px', padding: '4px 12px', backgroundColor: 'var(--success)' }}
                onClick={handleSaveNodes}
              >
                Save to nodes.json ({scanResult.count} nodes)
              </button>
            )}
            <button
              className="btn btn-ghost"
              style={{ fontSize: '12px', padding: '4px 8px' }}
              onClick={() => { setShowSysScan(false); setScanResult(null); setScanError(null); }}
            >
              Cancel
            </button>
          </div>
          {scanError && (
            <div style={{ fontSize: '11px', color: 'var(--error)', marginTop: '8px' }}>{scanError}</div>
          )}
          {scanResult && (
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '8px' }}>
              Found {scanResult.count} nodes (before filtering: {scanResult.totalBefore}).
              Review and click "Save to nodes.json" to apply.
            </div>
          )}
        </div>
      )}

      {/* Main split panel */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left: Node tree (40%) */}
        <div
          style={{
            width: '40%',
            minWidth: '250px',
            borderRight: '1px solid var(--border)',
            overflow: 'hidden',
          }}
        >
          <NodeTree
            onSelectNode={handleSelectNode}
            onSelectToken={handleSelectToken}
            onContextAction={handleContextAction}
            onDoubleClickFile={handleDoubleClickFile}
            onQueueStatusChange={setQueueStatus}
          />
        </div>

        {/* Right: Tabbed interface (60%) */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Tab bar */}
          <div
            style={{
              display: 'flex',
              gap: '2px',
              padding: '0 12px',
              borderBottom: '1px solid var(--border)',
              backgroundColor: 'var(--bg-secondary)',
            }}
          >
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 16px',
                  fontSize: '12px',
                  fontWeight: activeTab === t.id ? 600 : 400,
                  color: activeTab === t.id ? 'var(--accent)' : 'var(--text-secondary)',
                  backgroundColor: 'transparent',
                  border: 'none',
                  borderBottom: activeTab === t.id ? '2px solid var(--accent)' : '2px solid transparent',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-sans)',
                  transition: 'all 0.15s ease',
                }}
              >
                {t.icon}
                {t.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div style={{ flex: 1, overflow: 'hidden' }}>
            {activeTab === 'telnet' && (
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <TelnetTerminal
                  currentToken={currentToken}
                  currentTokenType={currentTokenType}
                  currentNodeName={currentNodeName}
                  pendingCommand={pendingCommand}
                  onCommandSent={() => setPendingCommand(null)}
                />
                {/* Context menu command output log */}
                {terminalLog.length > 0 && (
                  <div
                    style={{
                      maxHeight: '150px',
                      overflow: 'auto',
                      borderTop: '1px solid var(--border)',
                      backgroundColor: 'var(--bg-secondary)',
                      padding: '4px 8px',
                      fontSize: '11px',
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--text-secondary)',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}
                  >
                    {terminalLog.map((line, i) => (
                      <div key={i}>{line}</div>
                    ))}
                  </div>
                )}
              </div>
            )}
            {activeTab === 'bstool' && (
              <BsToolPanel
                pendingServerName={pendingServerName}
                onServerNameConsumed={() => setPendingServerName(null)}
                currentNodeName={currentNodeName}
              />
            )}
            {activeTab === 'scan' && (
              <ScanTab selectedNode={selectedNode} logRoot={logRoot} />
            )}
            {activeTab === 'logviewer' && (
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%', backgroundColor: 'var(--bg-primary)' }}>
                {/* File viewer header */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 12px',
                    borderBottom: '1px solid var(--border)',
                  }}
                >
                  <FileText size={14} color="var(--accent)" />
                  <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                    {fileViewName || 'No file selected'}
                  </span>
                  {fileViewPath && (
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: 'auto' }} title={fileViewPath}>
                      {fileViewPath}
                    </span>
                  )}
                </div>
                {/* File content */}
                <div style={{ flex: 1, overflow: 'auto', padding: '12px' }}>
                  {fileLoading ? (
                    <div style={{ textAlign: 'center', padding: '24px' }}>
                      <Loader2 size={20} color="var(--accent)" style={{ animation: 'spin 1s linear infinite' }} />
                      <p style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '8px' }}>Loading file...</p>
                    </div>
                  ) : fileContent ? (
                    <pre
                      style={{
                        fontSize: '12px',
                        fontFamily: 'var(--font-mono)',
                        color: 'var(--text-primary)',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        margin: 0,
                      }}
                    >
                      {fileContent}
                    </pre>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)', fontSize: '12px' }}>
                      Double-click a file in the node tree to view its content.
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom: Command queue bar */}
      <CommandQueueBar status={queueStatus} />

      {/* Node config dialog */}
      <NodeConfigDialog
        open={showConfigDialog}
        onClose={() => setShowConfigDialog(false)}
      />
    </div>
  );
}