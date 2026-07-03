import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Terminal, Server, ScanLine, Settings, Loader2, FileText, Folder, Printer } from 'lucide-react';
import NodeTree from './NodeTree';
import TelnetTerminal from './TelnetTerminal';
import BsToolPanel from './BsToolPanel';
import ScanTab from './ScanTab';
import CommandQueueBar from './CommandQueueBar';
import NodeConfigDialog from './NodeConfigDialog';
import { useActiveProject, useProjects } from '../hooks/useActiveProject';
import type { TreeNodeData, QueueStatusResponse } from '../types/api';

type Tab = 'telnet' | 'bstool' | 'scan' | 'logviewer';

function stripNodeSuffix(name: string): string {
  return name.replace(/[mr]$/, '');
}

function ColorizedLog({ content }: { content: string }) {
  const lines = content.split('\n');
  return (
    <pre style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0, lineHeight: '1.5' }}>
      {lines.map((line, i) => {
        const trimmed = line.trim();
        let color = '#22c55e';
        if (trimmed.startsWith('Error') || trimmed.startsWith('[ERROR') || trimmed.startsWith('ERROR') ||
            trimmed.includes('failed') || trimmed.includes('Failed') || trimmed.includes('FAILED') ||
            trimmed.includes('not found') || trimmed.includes('No such') || trimmed.includes('Unknown agent') ||
            trimmed.includes('[BEL]')) {
          color = '#ef4444';
        } else if (trimmed.startsWith('>') || trimmed.startsWith('[Connecting') || trimmed.startsWith('[Executing') ||
                   trimmed.startsWith('Getting') || trimmed.startsWith('%') || trimmed.includes('49s%') || trimmed.includes('64s%')) {
          color = '#f59e0b';
        } else if (trimmed.startsWith('[Connected') || trimmed.startsWith('[Done') || trimmed.startsWith('OK')) {
          color = '#10b981';
        } else if (trimmed === '' || trimmed === '(empty file)') {
          color = 'var(--text-muted)';
        }
        return <div key={i} style={{ color }}>{line || '\u00A0'}</div>;
      })}
    </pre>
  );
}

export default function CommanderLayout() {
  const { activeProjectId, activeLogRoot, selectLogRoot } = useActiveProject();
  const { projects } = useProjects();
  const navigate = useNavigate();
  const activeProject = projects.find((p) => p.id === activeProjectId) || null;
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
  const [treeReloadKey, setTreeReloadKey] = useState(0);
  const [fileContent, setFileContent] = useState<string>('');
  const [fileViewName, setFileViewName] = useState<string>('');
  const [fileViewPath, setFileViewPath] = useState<string>('');
  const [fileLoading, setFileLoading] = useState(false);
  const [terminalLog, setTerminalLog] = useState<string[]>([]);
  const [selectedFileKey, setSelectedFileKey] = useState<string | null>(null);
  const [showLogRootDropdown, setShowLogRootDropdown] = useState(false);
  const [customLogRoot, setCustomLogRoot] = useState('');
  const [printing, setPrinting] = useState(false);
  const [activeExecFile, setActiveExecFile] = useState<string | null>(null);
  const logRootDropdownRef = useRef<HTMLDivElement>(null);

  // Close LogRoot dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (logRootDropdownRef.current && !logRootDropdownRef.current.contains(e.target as Node)) {
        setShowLogRootDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Sync log root to backend when it changes (from shared hook)
  useEffect(() => {
    if (activeLogRoot) {
      fetch('/api/v1/logs/setroot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: activeLogRoot }),
      }).catch(() => {});
    }
  }, [activeLogRoot]);

  const handleSelectNode = useCallback((node: TreeNodeData) => {
    setSelectedNode(node);
    setCurrentNodeName(node.name);
  }, []);

  const handleSelectToken = useCallback((token: TreeNodeData) => {
    setSelectedToken(token);
    setCurrentToken(token.token_id || '');
    setCurrentTokenType(token.section_type || 'FBC');
    // Build file key for bidirectional highlighting
    if (token.type === 'file' || token.type === 'token') {
      const sectionType = token.section_type || '';
      const fileName = token.file_name || token.name;
      setSelectedFileKey(`${currentNodeName}:${sectionType}:${fileName}`);
    }
  }, [currentNodeName]);

  const handleDoubleClickFile = useCallback(async (node: TreeNodeData) => {
    let filePath = node.file_path || '';
    let fileName = node.file_name || node.name;
    if (!filePath && (node.type === 'token' || node.type === 'file') && node.file_name) {
      const logRoot = activeLogRoot || localStorage.getItem('logRoot') || '';
      if (logRoot) {
        const sectionType = node.section_type || '';
        const parts = fileName.split('_');
        const station = parts[0] || '';
        filePath = logRoot + '/' + station + '/' + sectionType + '/' + fileName;
      }
    }
    if (!filePath && node.type === 'token') {
      const logRoot = activeLogRoot || localStorage.getItem('logRoot') || '';
      if (logRoot && node.token_id) {
        const sectionType = node.section_type || 'FBC';
        const station = currentNodeName || '';
        if (station) {
          const ext = sectionType === 'FBC' ? '.fbc' : sectionType === 'RPC' ? '.rpc' : sectionType === 'LOG' ? '.log' : '.txt';
          fileName = station + '_' + (node.ip || '').replace(/\./g, '-') + '_' + node.token_id + ext;
          filePath = logRoot + '/' + station + '/' + sectionType + '/' + fileName;
        }
      }
    }
    if (!filePath) {
      setFileContent('No file path available. Set a log root directory first.');
      setActiveTab('logviewer');
      setFileViewName(fileName);
      return;
    }
    setFileLoading(true);
    setFileViewName(fileName);
    setFileViewPath(filePath);
    setActiveTab('logviewer');
    try {
      const res = await fetch('/api/v1/logs/content?path=' + encodeURIComponent(filePath));
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Failed' }));
        setFileContent('Error: ' + (data.message || res.statusText));
        return;
      }
      const data = await res.json();
      setFileContent(data.content || '(empty file)');
    } catch (err) {
      setFileContent('Error loading file: ' + (err instanceof Error ? err.message : String(err)));
    } finally {
      setFileLoading(false);
    }
  }, [currentNodeName, activeLogRoot]);

  const handleContextAction = useCallback(async (action: string, node: TreeNodeData, _parentNode?: TreeNodeData) => {
    let nodeName = node.name || currentNodeName;
    const tokenId = node.token_id || '';
    // Extract IP from the tree node or from the filename
    let nodeIp = node.ip || '';
    if (!nodeIp && (node.type === 'token' || node.type === 'file') && node.file_name) {
      // Filename format: STATION_IP-HYPHENATED_TOKEN.ext — extract IP from filename
      const parts = node.file_name.split('_');
      if (parts.length >= 2) {
        // IP is the second segment, with hyphens replaced by dots
        nodeIp = parts[1].replace(/-/g, '.');
      }
    }
    if (node.type === 'token' || node.type === 'file') {
      const fn = node.file_name || node.name;
      const parts = fn.split('_');
      if (parts.length >= 2) nodeName = parts[0];
    }
    switch (action) {
      case 'print_all':
        fetch(`/api/v1/commandqueue/batch-node?project_id=${activeProjectId || ''}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ node_name: nodeName }) })
          .then(() => fetch('/api/v1/commandqueue/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }))
          .catch(err => console.error('batch error:', err));
        break;
      case 'fbc_print_all':
        fetch(`/api/v1/commandqueue/batch-node?project_id=${activeProjectId || ''}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ node_name: nodeName, token_type: 'FBC' }) })
          .then(() => fetch('/api/v1/commandqueue/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }))
          .catch(err => console.error('fbc batch error:', err));
        break;
      case 'rpc_print_all':
        fetch(`/api/v1/commandqueue/batch-node?project_id=${activeProjectId || ''}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ node_name: nodeName, token_type: 'RPC' }) })
          .then(() => fetch('/api/v1/commandqueue/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }))
          .catch(err => console.error('rpc batch error:', err));
        break;
      case 'fbc_print': {
        // Sanitize tokenId: if it looks like a filename, extract just the number
        const cleanTokenId = tokenId.includes('_') && tokenId.includes('.') 
          ? tokenId.replace(/\.[^.]+$/, '').split('_').pop() || tokenId
          : tokenId;
        const cmd = 'print from fbc io structure ' + cleanTokenId + '0000';
        setActiveTab('telnet');
        setTerminalLog(prev => [...prev, '> ' + cmd]);
        setActiveExecFile(`${nodeName}:${cleanTokenId}:fbc`);
        try {
          const res = await fetch('/api/v1/telnet/execute', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ command: cmd, node_name: nodeName, token_type: 'FBC', token_id: cleanTokenId, ip_address: nodeIp }) });
          const data = await res.json();
          if (data.output) setTerminalLog(prev => [...prev, data.output]);
          setTreeReloadKey((k) => k + 1);
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        finally { setActiveExecFile(null); }
        break;
      }
      case 'rpc_print': {
        // Sanitize tokenId: if it looks like a filename, extract just the number
        const cleanTokenId = tokenId.includes('_') && tokenId.includes('.') 
          ? tokenId.replace(/\.[^.]+$/, '').split('_').pop() || tokenId
          : tokenId;
        const cmd = 'print from fbc rupi counters ' + cleanTokenId + '0000';
        setActiveTab('telnet');
        setTerminalLog(prev => [...prev, '> ' + cmd]);
        setActiveExecFile(`${nodeName}:${cleanTokenId}:rpc`);
        try {
          const res = await fetch('/api/v1/telnet/execute', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ command: cmd, node_name: nodeName, token_type: 'RPC', token_id: cleanTokenId, ip_address: nodeIp }) });
          const data = await res.json();
          if (data.output) setTerminalLog(prev => [...prev, data.output]);
          setTreeReloadKey((k) => k + 1);
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        finally { setActiveExecFile(null); }
        break;
      }
      case 'rpc_clear': {
        // Sanitize tokenId: if it looks like a filename, extract just the number
        const cleanTokenId = tokenId.includes('_') && tokenId.includes('.') 
          ? tokenId.replace(/\.[^.]+$/, '').split('_').pop() || tokenId
          : tokenId;
        const cmd = 'clear fbc rupi counters ' + cleanTokenId + '0000';
        setActiveTab('telnet');
        setTerminalLog(prev => [...prev, '> ' + cmd]);
        try {
          const res = await fetch('/api/v1/telnet/execute', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ command: cmd, node_name: nodeName, token_type: 'RPC', token_id: cleanTokenId, ip_address: nodeIp }) });
          const data = await res.json();
          if (data.output) setTerminalLog(prev => [...prev, data.output]);
          setTreeReloadKey((k) => k + 1);
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      }
      case 'bstool_errlog':
        setActiveTab('bstool');
        setPendingServerName(stripNodeSuffix(nodeName));
        break;
      case 'open_file':
        handleDoubleClickFile(node);
        break;
      case 'fbc_scan':
      case 'rpc_scan':
        setActiveTab('scan');
        break;
      case 'clear_logs':
        break;
      case 'erase_file': {
        const filePath = node.file_path || '';
        const tokenId = node.token_id || '';
        const sectionType = node.section_type || '';
        setActiveTab('logviewer');
        setTerminalLog(prev => [...prev, '> Erasing file: ' + (node.file_name || node.name)]);
        try {
          const body = filePath ? { path: filePath } : { node_name: nodeName, token_type: sectionType, token_id: tokenId };
          const res = await fetch('/api/v1/logs/erase', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
          const data = await res.json();
          if (data.erased) {
            setTerminalLog(prev => [...prev, '[File erased: ' + data.path + ']']);
          } else {
            setTerminalLog(prev => [...prev, 'Error: ' + (data.message || 'Erase failed')]);
          }
          setTreeReloadKey((k) => k + 1);
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      }
    }
  }, [currentNodeName, handleDoubleClickFile, activeProjectId]);

  // Print All Logs — batch ALL nodes (FBC + RPC + LOG) and start execution
  const handlePrintAll = useCallback(async () => {
    setPrinting(true);
    try {
      // Batch all nodes from the active project
      const batchRes = await fetch('/api/v1/commandqueue/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: activeProjectId ? String(activeProjectId) : '' }),
      });
      if (!batchRes.ok) {
        const data = await batchRes.json().catch(() => ({ message: 'Batch failed' }));
        throw new Error(data.message || `HTTP ${batchRes.status}`);
      }
      const batchData = await batchRes.json();
      setTerminalLog(prev => [...prev, `[Queue: ${batchData.total} commands queued]`]);
      // Start execution
      await fetch('/api/v1/commandqueue/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}',
      });
    } catch (err) {
      setTerminalLog(prev => [...prev, 'Print All Error: ' + (err instanceof Error ? err.message : String(err))]);
    } finally {
      setPrinting(false);
    }
  }, [activeProjectId]);

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'telnet', label: 'Telnet', icon: <Terminal size={14} /> },
    { id: 'bstool', label: 'BsTool', icon: <Server size={14} /> },
    { id: 'scan', label: 'Scan', icon: <ScanLine size={14} /> },
    { id: 'logviewer', label: 'Log Viewer', icon: <FileText size={14} /> },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '6px 16px', borderBottom: '1px solid var(--border)', backgroundColor: 'var(--bg-secondary)', flexShrink: 0 }}>
        <Terminal size={18} color="var(--accent)" />
        <h1 style={{ fontSize: '16px', fontWeight: 700 }}>Commander</h1>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Interactive Command Center</span>
        {activeProject && (
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: '4px' }}>
            {activeProject.project_number} — {activeProject.ship_name}
          </span>
        )}
        {/* LogRoot selector — replaces project dropdown */}
        <div style={{ position: 'relative', marginLeft: '8px' }} ref={logRootDropdownRef}>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '12px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '6px' }}
            onClick={() => setShowLogRootDropdown(!showLogRootDropdown)}
            disabled={!activeProjectId}
            title="Select or set log root directory"
          >
            <Folder size={12} />
            {activeLogRoot ? (
              <span style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{activeLogRoot}</span>
            ) : (
              <span style={{ color: 'var(--text-muted)' }}>{activeProjectId ? 'Set LogRoot...' : 'No project'}</span>
            )}
            <span style={{ fontSize: '10px' }}>▼</span>
          </button>
          {showLogRootDropdown && activeProjectId && (
            <div style={{ position: 'absolute', top: '100%', left: 0, marginTop: '4px', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: '6px', boxShadow: '0 4px 12px rgba(0,0,0,0.3)', zIndex: 1000, minWidth: '320px', padding: '12px' }}>
              {/* Current project log root */}
              {activeProject?.log_root && (
                <div
                  style={{ padding: '8px 12px', fontSize: '12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border)', marginBottom: '8px', backgroundColor: activeLogRoot === activeProject.log_root ? 'rgba(99,102,241,0.1)' : 'transparent', borderRadius: '4px' }}
                  onClick={() => { selectLogRoot(activeProject.log_root); setShowLogRootDropdown(false); setTreeReloadKey(k => k + 1); }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = 'rgba(99,102,241,0.08)'; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = activeLogRoot === activeProject.log_root ? 'rgba(99,102,241,0.1)' : 'transparent'; }}
                >
                  <Folder size={12} color={activeLogRoot === activeProject.log_root ? 'var(--accent)' : 'var(--text-muted)'} />
                  <div>
                    <div style={{ fontWeight: 600 }}>Project Default</div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{activeProject.log_root}</div>
                  </div>
                </div>
              )}
              {/* Custom log root input */}
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Set custom log root (e.g. for a new structure):</div>
              <div style={{ display: 'flex', gap: '6px' }}>
                <input
                  type="text"
                  value={customLogRoot}
                  onChange={(e) => setCustomLogRoot(e.target.value)}
                  placeholder="C:\temp\custom-logroot"
                  style={{
                    fontSize: '11px',
                    padding: '4px 8px',
                    flex: 1,
                    backgroundColor: 'var(--bg-elevated)',
                    border: '1px solid var(--border)',
                    borderRadius: '4px',
                    color: 'var(--text-primary)',
                    fontFamily: 'var(--font-mono)',
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && customLogRoot.trim()) {
                      selectLogRoot(customLogRoot.trim());
                      setCustomLogRoot('');
                      setShowLogRootDropdown(false);
                      setTreeReloadKey(k => k + 1);
                    }
                  }}
                />
                <button
                  className="btn btn-primary"
                  style={{ fontSize: '11px', padding: '4px 10px' }}
                  onClick={() => {
                    if (customLogRoot.trim()) {
                      selectLogRoot(customLogRoot.trim());
                      setCustomLogRoot('');
                      setShowLogRootDropdown(false);
                      setTreeReloadKey(k => k + 1);
                    }
                  }}
                >
                  Set
                </button>
              </div>
            </div>
          )}
        </div>
        <div style={{ flex: 1 }} />
        <button
          className="btn btn-primary"
          style={{ fontSize: '12px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '6px' }}
          onClick={handlePrintAll}
          disabled={printing}
          title="Queue and execute all print commands for all nodes"
        >
          {printing ? <Loader2 size={12} className="spin" /> : <Printer size={12} />}
          Print All Logs
        </button>
        <button className="btn btn-ghost" style={{ fontSize: '12px', padding: '4px 8px' }} onClick={() => setShowConfigDialog(true)} title="Configure nodes and tokens">
          <Settings size={14} /> Config
        </button>
      </div>

      {/* No project state */}
      {!activeProjectId ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: '48px', textAlign: 'center' }}>
          <Terminal size={48} color="var(--text-muted)" style={{ marginBottom: '16px' }} />
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '16px' }}>
            No project selected. Select a project from the Dashboard to use the Commander.
          </p>
          <button className="btn btn-primary" onClick={() => navigate('/')}>
            Go to Dashboard
          </button>
        </div>
      ) : !activeLogRoot ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: '48px', textAlign: 'center' }}>
          <Folder size={48} color="var(--text-muted)" style={{ marginBottom: '16px' }} />
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '16px' }}>
            No LogRoot set. Select a LogRoot directory from the dropdown above to load files.
          </p>
          <button className="btn btn-primary" onClick={() => setShowLogRootDropdown(true)}>
            Set LogRoot
          </button>
        </div>
      ) : (
      <>
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <div style={{ width: '40%', minWidth: '250px', borderRight: '1px solid var(--border)', overflow: 'hidden' }}>
          <NodeTree key={treeReloadKey} projectId={activeProjectId} onSelectNode={handleSelectNode} onSelectToken={handleSelectToken} onContextAction={handleContextAction} onDoubleClickFile={handleDoubleClickFile} onQueueStatusChange={setQueueStatus} selectedFileKey={selectedFileKey} activeExecFile={activeExecFile} />
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ display: 'flex', gap: '2px', padding: '0 12px', borderBottom: '1px solid var(--border)', backgroundColor: 'var(--bg-secondary)' }}>
            {tabs.map((t) => (
              <button key={t.id} onClick={() => setActiveTab(t.id)} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', fontSize: '12px', fontWeight: activeTab === t.id ? 600 : 400, color: activeTab === t.id ? 'var(--accent)' : 'var(--text-secondary)', backgroundColor: 'transparent', border: 'none', borderBottom: activeTab === t.id ? '2px solid var(--accent)' : '2px solid transparent', cursor: 'pointer', fontFamily: 'var(--font-sans)', transition: 'all 0.15s ease' }}>
                {t.icon}{t.label}
              </button>
            ))}
          </div>
          <div style={{ flex: 1, overflow: 'hidden' }}>
            {activeTab === 'telnet' && (
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <TelnetTerminal currentToken={currentToken} currentTokenType={currentTokenType} currentNodeName={currentNodeName} pendingCommand={pendingCommand} onCommandSent={() => setPendingCommand(null)} />
                {terminalLog.length > 0 && (
                  <div style={{ maxHeight: '150px', overflow: 'auto', borderTop: '1px solid var(--border)', backgroundColor: 'var(--bg-secondary)', padding: '4px 8px', fontSize: '11px', fontFamily: 'var(--font-mono)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {terminalLog.map((line, i) => (<div key={i} style={{ color: line.startsWith('Error') || line.startsWith('[ERROR') ? '#ef4444' : line.startsWith('>') ? '#f59e0b' : '#22c55e' }}>{line}</div>))}
                  </div>
                )}
              </div>
            )}
            {activeTab === 'bstool' && <BsToolPanel pendingServerName={pendingServerName} onServerNameConsumed={() => setPendingServerName(null)} currentNodeName={currentNodeName} />}
            {activeTab === 'scan' && <ScanTab selectedNode={selectedNode} logRoot={activeLogRoot || localStorage.getItem('logRoot') || ''} />}
            {activeTab === 'logviewer' && (
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%', backgroundColor: 'var(--bg-primary)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px', borderBottom: '1px solid var(--border)' }}>
                  <FileText size={14} color="var(--accent)" />
                  <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{fileViewName || 'No file selected'}</span>
                  {fileViewPath && <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: 'auto' }} title={fileViewPath}>{fileViewPath}</span>}
                </div>
                <div style={{ flex: 1, overflow: 'auto', padding: '12px' }}>
                  {fileLoading ? (
                    <div style={{ textAlign: 'center', padding: '24px' }}><Loader2 size={20} color="var(--accent)" className="spin" /><p style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '8px' }}>Loading file...</p></div>
                  ) : fileContent ? <ColorizedLog content={fileContent} /> : (
                    <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)', fontSize: '12px' }}>Double-click a file in the node tree to view its content.</div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      </>
      )}
      <CommandQueueBar status={queueStatus} />
      <NodeConfigDialog open={showConfigDialog} onClose={() => setShowConfigDialog(false)} />
    </div>
  );
}
