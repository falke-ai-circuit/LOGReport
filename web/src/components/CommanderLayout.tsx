// @ts-nocheck
import { useState, useEffect, useCallback } from 'react';
import { Terminal, Server, ScanLine, Settings, FolderOpen, Loader2, FileText, Upload, Plus, Trash2, Save, Box, ChevronDown } from 'lucide-react';
import NodeTree from './NodeTree';
import TelnetTerminal from './TelnetTerminal';
import BsToolPanel from './BsToolPanel';
import ScanTab from './ScanTab';
import CommandQueueBar from './CommandQueueBar';
import NodeConfigDialog from './NodeConfigDialog';
import type { TreeNodeData, QueueStatusResponse, NodeConfig } from '../types/api';

type Tab = 'telnet' | 'nodes' | 'bstool' | 'scan' | 'logviewer';

// ─── Project interface ──────────────────────────────────────────
interface Project {
  id: number;
  project_number: string;
  ship_name: string;
  log_root: string;
  status: string;
  created_at: string;
  updated_at: string;
}

// Strip suffix from node name: "AP01m" → "AP01", "AP01r" → "AP01"
function stripNodeSuffix(name: string): string {
  return name.replace(/[mr]$/, '');
}

// Read project_id from URL query param (?project_id=N)
function getProjectIdFromURL(): number | null {
  try {
    const params = new URLSearchParams(window.location.search);
    const val = params.get('project_id');
    if (val) {
      const n = parseInt(val, 10);
      if (!isNaN(n) && n > 0) return n;
    }
  } catch {
    // ignore
  }
  return null;
}

export default function CommanderLayout() {
  const [activeTab, setActiveTab] = useState<Tab>('telnet');
  const [selectedNode, setSelectedNode] = useState<TreeNodeData | null>(null);
  const [, setSelectedToken] = useState<TreeNodeData | null>(null);
  const [setCurrentToken] = useState('');
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

  // ─── Project selector state ────────────────────────────────────
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<number | null>(() => {
    const fromURL = getProjectIdFromURL();
    if (fromURL) {
      localStorage.setItem('activeProjectId', String(fromURL));
      return fromURL;
    }
    const stored = localStorage.getItem('activeProjectId');
    return stored ? parseInt(stored, 10) : null;
  });
  const [projectsLoading, setProjectsLoading] = useState(false);
  const [showProjectDropdown, setShowProjectDropdown] = useState(false);
  const [treeReloadKey, setTreeReloadKey] = useState(0);

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

  // ─── Fetch projects ────────────────────────────────────────────
  useEffect(() => {
    async function fetchProjects() {
      setProjectsLoading(true);
      try {
        const res = await fetch('/api/v1/projects');
        if (!res.ok) return;
        const data = await res.json();
        setProjects(data.projects || []);
        // Auto-select first project if none selected and projects exist
        if (!activeProjectId && data.projects && data.projects.length > 0) {
          const first = data.projects[0];
          setActiveProjectId(first.id);
          localStorage.setItem('activeProjectId', String(first.id));
        }
      } catch {
        // ignore
      } finally {
        setProjectsLoading(false);
      }
    }
    fetchProjects();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const activeProject = projects.find((p) => p.id === activeProjectId) || null;

  function handleSelectProject(id: number) {
    setActiveProjectId(id);
    localStorage.setItem('activeProjectId', String(id));
    setShowProjectDropdown(false);
    setTreeReloadKey((k) => k + 1); // force tree reload
  }

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
          const cmd = `print from fbc io structure ${tokenId}0000`;
          setActiveTab('telnet');
          setTerminalLog(prev => [...prev, `> ${cmd}`]);
          try {
            const res = await fetch('/api/v1/telnet/execute', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ command: cmd, node_name: nodeName, token_type: 'FBC', token_id: tokenId, ip_address: node.ip || '' }),
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
          const cmd = `print from fbc rupi counters ${tokenId}0000`;
          setActiveTab('telnet');
          setTerminalLog(prev => [...prev, `> ${cmd}`]);
          try {
            const res = await fetch('/api/v1/telnet/execute', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ command: cmd, node_name: nodeName, token_type: 'RPC', token_id: tokenId, ip_address: node.ip || '' }),
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
          const cmd = `clear fbc rupi counters ${tokenId}0000`;
          setActiveTab('telnet');
          setTerminalLog(prev => [...prev, `> ${cmd}`]);
          try {
            const res = await fetch('/api/v1/telnet/execute', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ command: cmd, node_name: nodeName, token_type: 'RPC', token_id: tokenId, ip_address: node.ip || '' }),
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

  // ─── Sys file scan + ingest (header version, legacy) ───────────

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
      const projectIdParam = activeProjectId ? `?project_id=${activeProjectId}` : '';
      const res = await fetch(`/api/v1/nodesconfig${projectIdParam}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(scanResult.configs),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Save failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      setShowSysScan(false);
      setScanResult(null);
      setTreeReloadKey((k) => k + 1);
    } catch (err) {
      setScanError(err instanceof Error ? err.message : 'Save failed');
    }
  }, [scanResult, activeProjectId]);

  // ─── Tab bar ────────────────────────────────────────────────────

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'telnet', label: 'Telnet', icon: <Terminal size={14} /> },
    { id: 'nodes', label: 'Nodes', icon: <Box size={14} /> },
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

        {/* ─── Project selector dropdown ─────────────────────────── */}
        <div style={{ position: 'relative', marginLeft: '8px' }}>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '12px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '6px' }}
            onClick={() => setShowProjectDropdown(!showProjectDropdown)}
            title="Select active project"
          >
            <Box size={12} />
            {activeProject ? (
              <span>{activeProject.project_number} — {activeProject.ship_name}</span>
            ) : projectsLoading ? (
              <Loader2 size={12} className="spin" />
            ) : (
              <span style={{ color: 'var(--text-muted)' }}>Select Project...</span>
            )}
            <ChevronDown size={12} />
          </button>
          {showProjectDropdown && (
            <div
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                marginTop: '4px',
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                zIndex: 1000,
                minWidth: '280px',
                maxHeight: '300px',
                overflow: 'auto',
              }}
            >
              {projects.length === 0 ? (
                <div style={{ padding: '12px', fontSize: '12px', color: 'var(--text-muted)' }}>
                  No projects. Create one from the Dashboard.
                </div>
              ) : (
                projects.map((p) => (
                  <div
                    key={p.id}
                    onClick={() => handleSelectProject(p.id)}
                    style={{
                      padding: '8px 12px',
                      fontSize: '12px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      borderBottom: '1px solid var(--border)',
                      backgroundColor: p.id === activeProjectId ? 'rgba(99,102,241,0.1)' : 'transparent',
                    }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = 'rgba(99,102,241,0.08)'; }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = p.id === activeProjectId ? 'rgba(99,102,241,0.1)' : 'transparent'; }}
                  >
                    <Box size={12} color={p.id === activeProjectId ? 'var(--accent)' : 'var(--text-muted)'} />
                    <div>
                      <div style={{ fontWeight: p.id === activeProjectId ? 600 : 400 }}>
                        {p.project_number} — {p.ship_name}
                      </div>
                      <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                        {p.status} · {p.log_root || 'no log root'}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

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

      {/* Sys file scan panel (header version, legacy) */}
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
                Save to project ({scanResult.count} nodes)
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
              {activeProject ? ` Saving to project "${activeProject.ship_name}".` : ' No project selected — saves to global nodes.'}
              Review and click "Save to project" to apply.
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
            key={treeReloadKey}
            projectId={activeProjectId}
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
            {activeTab === 'nodes' && (
              <NodesTabContent
                projectId={activeProjectId}
                projectName={activeProject ? `${activeProject.project_number} — ${activeProject.ship_name}` : null}
                onNodesSaved={() => setTreeReloadKey((k) => k + 1)}
              />
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

// ═══════════════════════════════════════════════════════════════
// NodesTabContent — Node browser + sys file import
// ═══════════════════════════════════════════════════════════════

interface NodesTabContentProps {
  projectId: number | null;
  projectName: string | null;
  onNodesSaved: () => void;
}

function NodesTabContent({ projectId, projectName, onNodesSaved }: NodesTabContentProps) {
  // Node config state (NodeConfig[] from nodesconfig API)
  const [nodes, setNodes] = useState<NodeConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingStation, setEditingStation] = useState<string | null>(null);
  const [editNodes, setEditNodes] = useState<NodeConfig[]>([]);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  // Sys file import state
  const [importDir, setImportDir] = useState(localStorage.getItem('sysDir') || '');
  const [importScanning, setImportScanning] = useState(false);
  const [importResult, setImportResult] = useState<{ count: number; totalBefore: number; configs: NodeConfig[] } | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [selectedImports, setSelectedImports] = useState<Set<number>>(new Set());
  const [singleSysPath, setSingleSysPath] = useState('');
  const [showImport, setShowImport] = useState(false);

  // Load from project state
  const [allProjects, setAllProjects] = useState<Array<{ id: number; project_number: string; ship_name: string }>>([]);
  const [loadProjectId, setLoadProjectId] = useState<number | ''>('');

  // ─── Station grouping helpers ────────────────────────────────────
  function getStationName(name: string): string {
    // Extract base station name and append m (main) or r (reserve)
    // AP01 → AP01m, AP01 Main → AP01m, AP01_m2 → AP01m
    // AP02 Reserve → AP02r, AP02_r2 → AP02r
    // AL01 → AL01, A1OA OPS → A1OA (no m/r for non-PCS)
    
    // Strip _mN or _rN suffix
    let base = name.replace(/_m\d+$/, '').replace(/_r\d+$/, '');
    // Strip " Main" or " Reserve" suffix
    base = base.replace(/\s+Main$/, '').replace(/\s+Reserve$/, '');
    
    // Check if it's a reserve node
    const isReserve = /_r\d+$/.test(name) || /\s+Reserve$/.test(name) || /Reserve/.test(name);
    // Check if it's a PCS node (AP prefix)
    const isPCS = /^AP/.test(base);
    // Check if it's LIS (AL prefix) or OPS — no m/r suffix
    
    if (isPCS) {
      return isReserve ? base + 'r' : base + 'm';
    }
    return base; // LIS, OPS — no m/r suffix
  }

  function getSlotNumber(name: string): number {
    // Slot 1 = base (CPU), Slot 2 = _m2 or _r2, etc.
    const mMatch = name.match(/_m(\d+)$/);
    if (mMatch) return parseInt(mMatch[1], 10);
    const rMatch = name.match(/_r(\d+)$/);
    if (rMatch) return parseInt(rMatch[1], 10);
    return 1; // Base node = slot 1
  }

  interface StationGroup {
    stationName: string;
    ipAddress: string;
    slots: Array<{ node: NodeConfig; slotNumber: number; index: number }>;
  }

  function groupByStation(nodeList: NodeConfig[]): StationGroup[] {
    const map = new Map<string, StationGroup>();
    nodeList.forEach((node, idx) => {
      const stationName = getStationName(node.name);
      if (!map.has(stationName)) {
        map.set(stationName, {
          stationName,
          ipAddress: node.ip_address,
          slots: [],
        });
      }
      const station = map.get(stationName)!;
      if (!station.ipAddress && node.ip_address) {
        station.ipAddress = node.ip_address;
      }
      station.slots.push({ node, slotNumber: getSlotNumber(node.name), index: idx });
    });
    // Sort slots by slot number
    for (const station of map.values()) {
      station.slots.sort((a, b) => a.slotNumber - b.slotNumber);
    }
    return Array.from(map.values()).sort((a, b) => a.stationName.localeCompare(b.stationName));
  }

  // ─── Fetch all projects for "Load from project" dropdown ───────
  useEffect(() => {
    async function fetchAllProjects() {
      try {
        const res = await fetch('/api/v1/projects');
        if (!res.ok) return;
        const data = await res.json();
        setAllProjects(data.projects || []);
      } catch {
        // ignore
      }
    }
    fetchAllProjects();
  }, []);

  // ─── Load nodes from another project (without saving) ──────────
  async function handleLoadFromProject(otherId: number) {
    setLoadProjectId(otherId);
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/nodesconfig?project_id=${otherId}`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      const loadedNodes: NodeConfig[] = data.configs || [];
      setNodes(loadedNodes);
      setSaveMsg(`Loaded ${loadedNodes.length} nodes from another project — click Save Changes to commit to current project`);
      setTimeout(() => setSaveMsg(null), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load nodes from project');
    } finally {
      setLoading(false);
    }
  }

  // ─── Fetch nodes for active project ────────────────────────────
  const fetchNodes = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const pidParam = projectId ? `?project_id=${projectId}` : '';
      const res = await fetch(`/api/v1/nodesconfig${pidParam}`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      setNodes(data.configs || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load nodes');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchNodes();
  }, [fetchNodes]);

  // ─── Save all nodes ─────────────────────────────────────────────
  async function handleSaveAll() {
    setSaving(true);
    setSaveMsg(null);
    try {
      const pidParam = projectId ? `?project_id=${projectId}` : '';
      const res = await fetch(`/api/v1/nodesconfig${pidParam}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(nodes),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Save failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      setSaveMsg('Saved successfully');
      setTimeout(() => setSaveMsg(null), 3000);
      onNodesSaved();
    } catch (err) {
      setSaveMsg(`Error: ${err instanceof Error ? err.message : 'Save failed'}`);
    } finally {
      setSaving(false);
    }
  }

  // ─── Add new node (adds a new station) ────────────────────────────
  function handleAddNode() {
    const newNode: NodeConfig = { name: 'NewStation', ip_address: '192.168.0.1', tokens: [{ token_id: '0000', token_type: 'FBC', port: 23, protocol: 'telnet' }] };
    setNodes([...nodes, newNode]);
    setEditingStation(getStationName('NewStation'));
    setEditNodes([JSON.parse(JSON.stringify(newNode))]);
  }

  // ─── Delete station (all nodes belonging to that station) ───────
  function handleDeleteStation(stationName: string) {
    const updated = nodes.filter((n) => getStationName(n.name) !== stationName);
    setNodes(updated);
    if (editingStation === stationName) {
      setEditingStation(null);
    }
  }

  // ─── Start editing a station ─────────────────────────────────────
  function startEditStation(stationName: string, stationSlots: NodeConfig[]) {
    setEditingStation(stationName);
    setEditNodes(JSON.parse(JSON.stringify(stationSlots)));
  }

  // ─── Save edited station ──────────────────────────────────────────
  function saveEditStation(stationName: string) {
    if (editingStation !== stationName) return;
    // Replace all nodes belonging to this station with the edited versions
    const otherNodes = nodes.filter((n) => getStationName(n.name) !== stationName);
    const updated = [...otherNodes, ...editNodes];
    setNodes(updated);
    setEditingStation(null);
  }

  // ─── Cancel editing ──────────────────────────────────────────────
  function cancelEdit() {
    setEditingStation(null);
  }

  // ─── Add token to edited slot ─────────────────────────────────────
  function addTokenToSlot(slotIdx: number) {
    const updated = [...editNodes];
    updated[slotIdx] = {
      ...updated[slotIdx],
      tokens: [...updated[slotIdx].tokens, { token_id: '0000', token_type: 'FBC', port: 23, protocol: 'telnet' }],
    };
    setEditNodes(updated);
  }

  // ─── Remove token from edited slot ────────────────────────────────
  function removeTokenFromSlot(slotIdx: number, ti: number) {
    const updated = [...editNodes];
    updated[slotIdx] = {
      ...updated[slotIdx],
      tokens: updated[slotIdx].tokens.filter((_, i) => i !== ti),
    };
    setEditNodes(updated);
  }

  // ─── Add a new slot to the station being edited ──────────────────
  function addSlotToStation(stationName: string) {
    const existingSlots = editNodes.map((n) => getSlotNumber(n.name));
    const maxSlot = existingSlots.length > 0 ? Math.max(...existingSlots) : 0;
    const newSlotNum = maxSlot + 1;
    const newNode: NodeConfig = {
      name: newSlotNum === 1 ? stationName : `${stationName}_m${newSlotNum}`,
      ip_address: editNodes[0]?.ip_address || '',
      tokens: [{ token_id: '0000', token_type: 'FBC', port: 23, protocol: 'telnet' }],
    };
    setEditNodes([...editNodes, newNode]);
  }

  // ─── Remove a slot from the station being edited ─────────────────
  function removeSlotFromStation(slotIdx: number) {
    setEditNodes(editNodes.filter((_, i) => i !== slotIdx));
  }

  // ─── Sys file import: Scan ──────────────────────────────────────
  async function handleImportScan() {
    if (!importDir) {
      setImportError('Directory is required');
      return;
    }
    setImportScanning(true);
    setImportError(null);
    setImportResult(null);
    setSelectedImports(new Set());
    try {
      const res = await fetch(`/api/v1/sysfiles/parse?dir=${encodeURIComponent(importDir)}`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Scan failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      const data = await res.json();
      const configs: NodeConfig[] = data.configs || data.nodes || [];
      setImportResult({ count: configs.length, totalBefore: data.total_before_filter || configs.length, configs });
      // Select all by default
      setSelectedImports(new Set(configs.map((_, i) => i)));
      localStorage.setItem('sysDir', importDir);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Scan failed');
    } finally {
      setImportScanning(false);
    }
  }

  // ─── Sys file import: Import selected ────────────────────────────
  async function handleImportSelected() {
    if (!importResult || selectedImports.size === 0) return;
    const selectedNodes = importResult.configs.filter((_, i) => selectedImports.has(i));
    // Merge with existing nodes
    const merged = [...nodes, ...selectedNodes];
    setSaving(true);
    setImportError(null);
    try {
      const pidParam = projectId ? `?project_id=${projectId}` : '';
      const res = await fetch(`/api/v1/nodesconfig${pidParam}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(merged),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Import failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      setNodes(merged);
      setImportResult(null);
      setSelectedImports(new Set());
      setSaveMsg(`Imported ${selectedNodes.length} nodes`);
      setTimeout(() => setSaveMsg(null), 3000);
      onNodesSaved();
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Import failed');
    } finally {
      setSaving(false);
    }
  }

  // ─── Import single .sys file ─────────────────────────────────────
  async function handleImportSingle() {
    if (!singleSysPath) {
      setImportError('File path is required');
      return;
    }
    setImportScanning(true);
    setImportError(null);
    try {
      // Use parse endpoint with the file path — it handles single files too
      const res = await fetch(`/api/v1/sysfiles/parse?dir=${encodeURIComponent(singleSysPath)}`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Parse failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      const data = await res.json();
      const configs: NodeConfig[] = data.configs || data.nodes || [];
      if (configs.length === 0) {
        setImportError('No nodes found in file');
        return;
      }
      const merged = [...nodes, ...configs];
      const pidParam = projectId ? `?project_id=${projectId}` : '';
      const saveRes = await fetch(`/api/v1/nodesconfig${pidParam}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(merged),
      });
      if (!saveRes.ok) throw new Error('Save failed');
      setNodes(merged);
      setSingleSysPath('');
      setSaveMsg(`Imported ${configs.length} node(s) from file`);
      setTimeout(() => setSaveMsg(null), 3000);
      onNodesSaved();
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Import failed');
    } finally {
      setImportScanning(false);
    }
  }

  // ─── Toggle import selection ─────────────────────────────────────
  function toggleImportSelection(idx: number) {
    setSelectedImports((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  }

  // ─── Token type badge colors ──────────────────────────────────────
  const TOKEN_COLORS: Record<string, string> = {
    FBC: '#6366f1',
    RPC: '#10b981',
    LOG: '#f59e0b',
    LIS: '#ec4899',
    FTP: '#8b5cf6',
  };

  function getTokenTypes(node: NodeConfig): string[] {
    const types = new Set<string>();
    node.tokens.forEach((t) => types.add(t.token_type));
    return Array.from(types);
  }

  return (
    <div style={{ height: '100%', overflow: 'auto', backgroundColor: 'var(--bg-primary)' }}>
      {/* Active project name banner (Issue 3) */}
      {projectName && (
        <div
          style={{
            padding: '8px 16px',
            backgroundColor: 'var(--accent-dim)',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <Box size={16} color="var(--accent)" />
          <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--accent)' }}>
            {projectName}
          </span>
        </div>
      )}

      {/* Toolbar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 16px',
          borderBottom: '1px solid var(--border)',
          backgroundColor: 'var(--bg-secondary)',
          flexWrap: 'wrap',
        }}
      >
        <Box size={16} color="var(--accent)" />
        <span style={{ fontSize: '13px', fontWeight: 600 }}>
          Node Browser
          {projectId ? '' : ' (no project selected)'}
        </span>

        {/* Load from project dropdown (Issue 5) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginLeft: '8px' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Load from project:</span>
          <select
            value={loadProjectId}
            onChange={(e) => {
              const val = e.target.value;
              if (val === '') { setLoadProjectId(''); return; }
              const id = Number(val);
              if (id !== projectId) {
                handleLoadFromProject(id);
              }
            }}
            style={{
              fontSize: '11px',
              padding: '3px 8px',
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border)',
              borderRadius: '4px',
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-sans)',
              maxWidth: '200px',
            }}
            title="Load nodes from another project into the editor (without saving)"
          >
            <option value="">— Select —</option>
            {allProjects.filter((p) => p.id !== projectId).map((p) => (
              <option key={p.id} value={p.id}>
                {p.project_number} — {p.ship_name}
              </option>
            ))}
          </select>
        </div>

        <div style={{ flex: 1 }} />
        <button
          className="btn btn-ghost"
          style={{ fontSize: '12px', padding: '4px 8px' }}
          onClick={() => setShowImport(!showImport)}
          title="Import nodes from .sys files"
        >
          <Upload size={14} />
          Import
        </button>
        <button
          className="btn btn-ghost"
          style={{ fontSize: '12px', padding: '4px 8px' }}
          onClick={handleAddNode}
          title="Add a new node manually"
        >
          <Plus size={14} />
          Add Node
        </button>
        <button
          className="btn btn-primary"
          style={{ fontSize: '12px', padding: '4px 12px' }}
          onClick={handleSaveAll}
          disabled={saving}
          title="Save all node changes"
        >
          {saving ? <Loader2 size={12} className="spin" /> : <Save size={14} />}
          Save Changes
        </button>
        {saveMsg && (
          <span style={{ fontSize: '11px', color: saveMsg.startsWith('Error') ? 'var(--error)' : 'var(--success)' }}>
            {saveMsg}
          </span>
        )}
      </div>

      {/* Import panel */}
      {showImport && (
        <div
          style={{
            padding: '12px 16px',
            borderBottom: '1px solid var(--border)',
            backgroundColor: 'var(--bg-secondary)',
          }}
        >
          {/* BU Directory scan */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '8px' }}>
            <Upload size={14} color="var(--accent)" />
            <span style={{ fontSize: '12px', fontWeight: 600 }}>Scan BU Directory for .sys files</span>
            <div style={{ flex: 1 }} />
            <input
              type="text"
              value={importDir}
              onChange={(e) => setImportDir(e.target.value)}
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
              onKeyDown={(e) => { if (e.key === 'Enter') handleImportScan(); }}
            />
            <button
              className="btn btn-primary"
              style={{ fontSize: '12px', padding: '4px 12px' }}
              onClick={handleImportScan}
              disabled={importScanning}
            >
              {importScanning ? <Loader2 size={12} className="spin" /> : 'Scan'}
            </button>
          </div>

          {/* Single .sys file path */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Or import a single .sys file:</span>
            <input
              type="text"
              value={singleSysPath}
              onChange={(e) => setSingleSysPath(e.target.value)}
              placeholder="C:\path\to\file.sys"
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
              onKeyDown={(e) => { if (e.key === 'Enter') handleImportSingle(); }}
            />
            <button
              className="btn btn-secondary"
              style={{ fontSize: '12px', padding: '4px 10px' }}
              onClick={handleImportSingle}
              disabled={importScanning}
            >
              Import File
            </button>
          </div>

          {importError && (
            <div style={{ fontSize: '11px', color: 'var(--error)', marginTop: '8px' }}>{importError}</div>
          )}

          {/* Scan results with checkboxes */}
          {importResult && (
            <div style={{ marginTop: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ fontSize: '12px', fontWeight: 600 }}>
                  Found {importResult.count} nodes (before filter: {importResult.totalBefore})
                </span>
                <div style={{ flex: 1 }} />
                <button
                  className="btn btn-ghost"
                  style={{ fontSize: '11px', padding: '2px 8px' }}
                  onClick={() => setSelectedImports(new Set(importResult.configs.map((_, i) => i)))}
                >
                  Select All
                </button>
                <button
                  className="btn btn-ghost"
                  style={{ fontSize: '11px', padding: '2px 8px' }}
                  onClick={() => setSelectedImports(new Set())}
                >
                  Select None
                </button>
                <button
                  className="btn btn-primary"
                  style={{ fontSize: '12px', padding: '4px 12px', backgroundColor: 'var(--success)' }}
                  onClick={handleImportSelected}
                  disabled={saving || selectedImports.size === 0}
                >
                  Import Selected ({selectedImports.size})
                </button>
              </div>
              <div style={{ maxHeight: '200px', overflow: 'auto', border: '1px solid var(--border)', borderRadius: '4px' }}>
                {importResult.configs.map((cfg, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '6px 12px',
                      borderBottom: '1px solid var(--border)',
                      fontSize: '12px',
                      fontFamily: 'var(--font-mono)',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={selectedImports.has(i)}
                      onChange={() => toggleImportSelection(i)}
                    />
                    <span style={{ fontWeight: 600 }}>{cfg.name}</span>
                    <span style={{ color: 'var(--text-muted)' }}>{cfg.ip_address}</span>
                    <span style={{ color: 'var(--text-muted)' }}>
                      {cfg.tokens.length} token(s): {cfg.tokens.map((t) => t.token_type).join(', ')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Station cards grid (Issue 4) */}
      <div style={{ padding: '16px' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '48px' }}>
            <Loader2 size={24} color="var(--accent)" className="spin" />
            <p style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '8px' }}>Loading nodes...</p>
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '48px' }}>
            <p style={{ color: 'var(--error)', fontSize: '13px', marginBottom: '12px' }}>{error}</p>
            <button className="btn btn-secondary" onClick={fetchNodes}>Retry</button>
          </div>
        ) : nodes.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
            <Box size={32} style={{ marginBottom: '12px', opacity: 0.5 }} />
            <p style={{ fontSize: '13px', marginBottom: '16px' }}>
              No nodes in this project. Use Import to scan .sys files, or Add Node to create one manually.
            </p>
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
              gap: '12px',
            }}
          >
            {groupByStation(nodes).map((station) => (
              <div
                key={station.stationName}
                style={{
                  backgroundColor: 'var(--bg-secondary)',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  padding: '12px',
                  transition: 'border-color 0.15s ease',
                }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--accent)'; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'; }}
              >
                {editingStation === station.stationName ? (
                  // ─── Station edit mode ───────────────────────────
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div>
                      <label style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Station Name</label>
                      <input
                        type="text"
                        value={getStationName(editNodes[0]?.name || '')}
                        onChange={(e) => {
                          const newStationName = e.target.value;
                          const updated = editNodes.map((n) => {
                            const slotNum = getSlotNumber(n.name);
                            return { ...n, name: slotNum === 1 ? newStationName : `${newStationName}_m${slotNum}` };
                          });
                          setEditNodes(updated);
                        }}
                        style={nodeInputStyle}
                      />
                    </div>
                    <div>
                      <label style={{ fontSize: '10px', color: 'var(--text-muted)' }}>IP Address</label>
                      <input
                        type="text"
                        value={editNodes[0]?.ip_address || ''}
                        onChange={(e) => {
                          const updated = editNodes.map((n) => ({ ...n, ip_address: e.target.value }));
                          setEditNodes(updated);
                        }}
                        style={nodeInputStyle}
                      />
                    </div>
                    {/* Slots editor */}
                    <div>
                      <label style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Slots</label>
                      {editNodes.map((slotNode, slotIdx) => (
                        <div key={slotIdx} style={{ border: '1px solid var(--border)', borderRadius: '4px', padding: '6px', marginBottom: '6px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
                            <span style={{ fontSize: '11px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                              Slot {getSlotNumber(slotNode.name)}: {slotNode.name}
                            </span>
                            <button
                              className="btn btn-ghost"
                              style={{ fontSize: '10px', padding: '1px 4px', color: 'var(--error)', marginLeft: 'auto' }}
                              onClick={() => removeSlotFromStation(slotIdx)}
                              title="Remove this slot"
                            >
                              <Trash2 size={10} />
                            </button>
                          </div>
                          {slotNode.tokens.map((tok, ti) => (
                            <div key={ti} style={{ display: 'flex', gap: '4px', marginBottom: '4px' }}>
                              <input
                                type="text"
                                value={tok.token_id}
                                onChange={(e) => {
                                  const updated = [...editNodes];
                                  const newTokens = [...updated[slotIdx].tokens];
                                  newTokens[ti] = { ...tok, token_id: e.target.value };
                                  updated[slotIdx] = { ...updated[slotIdx], tokens: newTokens };
                                  setEditNodes(updated);
                                }}
                                placeholder="token_id"
                                style={{ ...nodeInputStyle, width: '80px', fontSize: '11px', padding: '2px 4px' }}
                              />
                              <select
                                value={tok.token_type}
                                onChange={(e) => {
                                  const updated = [...editNodes];
                                  const newTokens = [...updated[slotIdx].tokens];
                                  newTokens[ti] = { ...tok, token_type: e.target.value };
                                  updated[slotIdx] = { ...updated[slotIdx], tokens: newTokens };
                                  setEditNodes(updated);
                                }}
                                style={{ ...nodeInputStyle, width: '70px', fontSize: '11px', padding: '2px 4px' }}
                              >
                                <option value="FBC">FBC</option>
                                <option value="RPC">RPC</option>
                                <option value="LOG">LOG</option>
                                <option value="LIS">LIS</option>
                                <option value="FTP">FTP</option>
                              </select>
                              <input
                                type="number"
                                value={tok.port}
                                onChange={(e) => {
                                  const updated = [...editNodes];
                                  const newTokens = [...updated[slotIdx].tokens];
                                  newTokens[ti] = { ...tok, port: Number(e.target.value) || 23 };
                                  updated[slotIdx] = { ...updated[slotIdx], tokens: newTokens };
                                  setEditNodes(updated);
                                }}
                                placeholder="port"
                                style={{ ...nodeInputStyle, width: '50px', fontSize: '11px', padding: '2px 4px' }}
                              />
                              <button
                                className="btn btn-ghost"
                                style={{ fontSize: '10px', padding: '2px 4px', color: 'var(--error)' }}
                                onClick={() => removeTokenFromSlot(slotIdx, ti)}
                              >
                                <Trash2 size={12} />
                              </button>
                            </div>
                          ))}
                          <button
                            className="btn btn-ghost"
                            style={{ fontSize: '10px', padding: '2px 8px' }}
                            onClick={() => addTokenToSlot(slotIdx)}
                          >
                            <Plus size={10} /> Add Token
                          </button>
                        </div>
                      ))}
                      <button
                        className="btn btn-ghost"
                        style={{ fontSize: '10px', padding: '2px 8px', marginTop: '4px' }}
                        onClick={() => addSlotToStation(station.stationName)}
                      >
                        <Plus size={10} /> Add Slot
                      </button>
                    </div>
                    {/* Save / Cancel buttons */}
                    <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
                      <button
                        className="btn btn-primary"
                        style={{ fontSize: '11px', padding: '4px 10px' }}
                        onClick={() => saveEditStation(station.stationName)}
                      >
                        <Save size={12} /> OK
                      </button>
                      <button
                        className="btn btn-ghost"
                        style={{ fontSize: '11px', padding: '4px 10px' }}
                        onClick={cancelEdit}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  // ─── Station display mode ────────────────────────
                  <div>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '15px', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                          {station.stationName}
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                          {station.ipAddress || '—'}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        <button
                          className="btn btn-ghost"
                          style={{ fontSize: '10px', padding: '2px 4px', color: 'var(--error)' }}
                          onClick={() => handleDeleteStation(station.stationName)}
                          title="Delete this station (all slots)"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                    {/* Slots listing */}
                    <div style={{ marginTop: '8px' }}>
                      {station.slots.map((slot) => (
                        <div
                          key={slot.index}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            padding: '4px 0',
                            borderBottom: '1px solid var(--border)',
                            fontSize: '12px',
                            fontFamily: 'var(--font-mono)',
                          }}
                        >
                          <span style={{ fontWeight: 600, color: 'var(--text-primary)', minWidth: '48px' }}>
                            Slot {slot.slotNumber}
                          </span>
                          <span style={{ color: 'var(--text-secondary)' }}>
                            {slot.node.name}
                          </span>
                          {/* Token IDs */}
                          {slot.node.tokens.map((t, ti) => (
                            <span key={ti} style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
                              <span style={{
                                fontSize: '10px',
                                fontWeight: 700,
                                padding: '1px 6px',
                                borderRadius: '8px',
                                backgroundColor: (TOKEN_COLORS[t.token_type] || '#666') + '22',
                                color: TOKEN_COLORS[t.token_type] || '#666',
                                border: `1px solid ${TOKEN_COLORS[t.token_type] || '#666'}44`,
                              }}>
                                {t.token_type}
                              </span>
                              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{t.token_id}</span>
                            </span>
                          ))}
                        </div>
                      ))}
                    </div>
                    {/* Edit button */}
                    <button
                      className="btn btn-ghost"
                      style={{ fontSize: '11px', padding: '4px 10px', marginTop: '8px', width: '100%' }}
                      onClick={() => startEditStation(station.stationName, station.slots.map((s) => s.node))}
                    >
                      Edit Station
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Shared styles for NodesTabContent ──────────────────────────────
const nodeInputStyle: React.CSSProperties = {
  fontSize: '12px',
  padding: '4px 8px',
  backgroundColor: 'var(--bg-elevated)',
  border: '1px solid var(--border)',
  borderRadius: '4px',
  color: 'var(--text-primary)',
  fontFamily: 'var(--font-mono)',
  width: '100%',
  boxSizing: 'border-box',
};