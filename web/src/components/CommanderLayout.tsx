import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Terminal, Server, ScanLine, Loader2, FileText, Folder, Printer, ListChecks, Edit2, Save, Clipboard, Play, Pause, Square, Trash2, RotateCcw, Network, AlertCircle } from 'lucide-react';
import NodeTree from './NodeTree';
import TelnetTerminal from './TelnetTerminal';
import BsToolPanel from './BsToolPanel';
import ScanTab from './ScanTab';
import QueueTab from './QueueTab';
import LisDiagTab from './LisDiagTab';
import CommandQueueBar from './CommandQueueBar';
import { useActiveProject, useProjects } from '../hooks/useActiveProject';
import type { TreeNodeData, QueueStatusResponse } from '../types/api';

type Tab = 'debugger' | 'lisdiag' | 'bstool' | 'scan' | 'logviewer' | 'queue';

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
  const [activeTab, setActiveTab] = useState<Tab>('debugger');
  const [lisdiagTarget, setLisdiagTarget] = useState<{ ip: string; node: string; tokenID: string; password: string; exeNum: number; commands: string[] } | null>(null);
  const [selectedNode, setSelectedNode] = useState<TreeNodeData | null>(null);
  const [, setSelectedToken] = useState<TreeNodeData | null>(null);
  const [currentToken, setCurrentToken] = useState('');
  const [currentTokenType, setCurrentTokenType] = useState('');
  const [currentNodeName, setCurrentNodeName] = useState('');
  const [pendingCommand, setPendingCommand] = useState<string | null>(null);
  const [pendingServerName, setPendingServerName] = useState<string | null>(null);
  const [pendingNodeIp, setPendingNodeIp] = useState<string | null>(null);
  const [queueStatus, setQueueStatus] = useState<QueueStatusResponse | null>(null);
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
  const [editingFile, setEditingFile] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [savingFile, setSavingFile] = useState(false);
  const [autoStart, setAutoStart] = useState(false);

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

  const maybeAutoStart = useCallback(() => {
    if (autoStart) {
      fetch('/api/v1/commandqueue/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }).catch(() => {});
    }
  }, [autoStart]);

  const handleSelectNode = useCallback((node: TreeNodeData) => {
    setSelectedNode(node);
    setCurrentNodeName(node.name);
  }, []);

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

  const handleSelectToken = useCallback((token: TreeNodeData) => {
    setSelectedToken(token);
    setCurrentToken(token.token_id || '');
    setCurrentTokenType(token.section_type || 'FBC');
    // Build file key for bidirectional highlighting
    if (token.type === 'file' || token.type === 'token') {
      const sectionType = token.section_type || '';
      const fileName = token.file_name || token.name;
      setSelectedFileKey(`${currentNodeName}:${sectionType}:${fileName}`);
      // Single-click opens file content on the right side (Log Viewer tab)
      handleDoubleClickFile(token);
    }
  }, [currentNodeName, handleDoubleClickFile]);

  const handleContextAction = useCallback(async (action: string, node: TreeNodeData, _parentNode?: TreeNodeData) => {
    let nodeName = node.name || currentNodeName;
    const tokenId = node.token_id || '';
    // Extract IP from the tree node, parent node, or from the filename
    let nodeIp = node.ip || _parentNode?.ip || '';
    if (!nodeIp && (node.type === 'token' || node.type === 'file') && node.file_name) {
      const parts = node.file_name.split('_');
      if (parts.length >= 2) {
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
          .then(() => maybeAutoStart())
          .catch(err => console.error('batch error:', err));
        break;
      case 'fbc_print_all':
        fetch(`/api/v1/commandqueue/batch-node?project_id=${activeProjectId || ''}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ node_name: nodeName, token_type: 'FBC' }) })
          .then(() => maybeAutoStart())
          .catch(err => console.error('fbc batch error:', err));
        break;
      case 'rpc_print_all':
        fetch(`/api/v1/commandqueue/batch-node?project_id=${activeProjectId || ''}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ node_name: nodeName, token_type: 'RPC' }) })
          .then(() => maybeAutoStart())
          .catch(err => console.error('rpc batch error:', err));
        break;
      case 'fbc_print': {
        // Route through queue — single command, auto-start if idle
        const cleanTokenId = tokenId.includes('_') && tokenId.includes('.') 
          ? tokenId.replace(/\.[^.]+$/, '').split('_').pop() || tokenId
          : tokenId;
        const cmd = 'print from fbc io structure ' + cleanTokenId + '0000';
        setActiveTab('queue');
        setTerminalLog(prev => [...prev, '> ' + cmd + ' (queued)']);
        setActiveExecFile(`${nodeName}:${cleanTokenId}:fbc`);
        try {
          await fetch('/api/v1/commandqueue/add', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'fbc', node_name: nodeName, token_id: cleanTokenId, command: cmd, ip_address: nodeIp }) });
          maybeAutoStart();
          // NOTE: No treeReloadKey bump — tree refreshes when queue finishes (running→done in NodeTree polling)
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      }
      case 'rpc_print': {
        const cleanTokenId = tokenId.includes('_') && tokenId.includes('.') 
          ? tokenId.replace(/\.[^.]+$/, '').split('_').pop() || tokenId
          : tokenId;
        const cmd = 'print from fbc rupi counters ' + cleanTokenId + '0000';
        setActiveTab('queue');
        setTerminalLog(prev => [...prev, '> ' + cmd + ' (queued)']);
        setActiveExecFile(`${nodeName}:${cleanTokenId}:rpc`);
        try {
          await fetch('/api/v1/commandqueue/add', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'rpc', node_name: nodeName, token_id: cleanTokenId, command: cmd, ip_address: nodeIp }) });
          maybeAutoStart();
         } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      }
      case 'rpc_clear': {
        const cleanTokenId = tokenId.includes('_') && tokenId.includes('.') 
          ? tokenId.replace(/\.[^.]+$/, '').split('_').pop() || tokenId
          : tokenId;
        const cmd = 'clear fbc rupi counters ' + cleanTokenId + '0000';
        setActiveTab('queue');
        setTerminalLog(prev => [...prev, '> ' + cmd + ' (queued)']);
        setActiveExecFile(`${nodeName}:${cleanTokenId}:rpc`);
        try {
          await fetch('/api/v1/commandqueue/add', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'rpc', node_name: nodeName, token_id: cleanTokenId, command: cmd, ip_address: nodeIp }) });
          maybeAutoStart();
         } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      }
      case 'bstool_errlog':
        // Route through queue as bstool type
        setActiveTab('queue');
        setPendingServerName(stripNodeSuffix(nodeName));
        setPendingNodeIp(nodeIp);
        try {
          await fetch('/api/v1/commandqueue/add', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'bstool', node_name: stripNodeSuffix(nodeName), token_id: '', command: 'errlog', ip_address: nodeIp }) });
          maybeAutoStart();
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      case 'lisdiag_run': {
        // Queue a single combined "exe N" command — the backend executor
        // automatically sends "exe N" then "io N-1" and writes the io output
        // to the .lis file. No need to queue io separately.
        const exeNumMatch = tokenId.match(/_exe(\d+)/);
        const exeNum = exeNumMatch ? parseInt(exeNumMatch[1], 10) : 1;
        const baseTokenID = tokenId.split('_exe')[0] || tokenId;
        // CRITICAL: tokenID for queue MUST include _exe{N} suffix so logwriter
        // creates the correct filename: {station}_{ip}_{token}_exe{N}.lis
        // Without this, all output goes to a single file without _exe suffix.
        const tokenIDWithExe = `${baseTokenID}_exe${exeNum}`;
        const exeCmd = `exe ${exeNum}`;
        // Fetch LisDiag password from settings
        let lisdiagPwd = '';
        try {
          const settingsRes = await fetch('/api/v1/settings');
          const settingsData = await settingsRes.json();
          lisdiagPwd = settingsData?.settings?.lisdiag_password || '';
        } catch {}
        // LisDiag connects to the AL station IP (cmd.IPAddress) which the
        // port proxy on the VM redirects to localhost where LisDiag.exe runs.
        setLisdiagTarget({
          ip: nodeIp,
          node: nodeName,
          tokenID: tokenIDWithExe,
          password: lisdiagPwd,
          exeNum,
          commands: [exeCmd],
        });
        setActiveTab('lisdiag');
        setTerminalLog(prev => [...prev, `> ${exeCmd} (LisDiag ${baseTokenID} exe${exeNum} queued — backend sends exe+io)`]);
        setActiveExecFile(`${nodeName}:${tokenIDWithExe}:lisdiag`);
        try {
          await fetch('/api/v1/commandqueue/add', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'lisdiag', node_name: nodeName, token_id: tokenIDWithExe, command: exeCmd, ip_address: nodeIp, lisdiag_pwd: lisdiagPwd }) });
          // LisDiag commands always auto-start the queue — the LisDiag tab is a
          // visual terminal, not a queue management page. The user expects the
          // command to execute immediately when they right-click → Run LisDiag.
          fetch('/api/v1/commandqueue/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }).catch(() => {});
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      }
      case 'lisdiag_io':
        // No-op: merged into lisdiag_run (exe N + io N-1 queued together)
        break;
      case 'rsu_trace': {
        // Queue combined rx+tx RSU trace command for one exe
        const exeNumMatch = tokenId.match(/_exe(\d+)/);
        const exeNum = exeNumMatch ? parseInt(exeNumMatch[1], 10) : 1;
        const baseTokenId = tokenId.split('_exe')[0] || tokenId;
        const channel = exeNum;
        const rxCmd = `print from rsu rx-trace ${baseTokenId}0000 ${channel}`;
        const txCmd = `print from rsu tx-trace ${baseTokenId}0000 ${channel}`;
        setActiveTab('queue');
        setTerminalLog(prev => [...prev, `> ${rxCmd} + ${txCmd} (queued as combined command)`]);
        setActiveExecFile(`${nodeName}:${tokenId}:rsu`);
        try {
          await fetch('/api/v1/commandqueue/add', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'rsu', node_name: nodeName, token_id: tokenId, command: rxCmd, ip_address: nodeIp, extra_data: txCmd }) });
          maybeAutoStart();
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      }
      case 'rsu_status': {
        // Queue RSU status command for one exe
        const baseTokenId = tokenId.split('_exe')[0] || tokenId;
        const cmd = `print from rsu status ${baseTokenId}0000`;
        setActiveTab('queue');
        setTerminalLog(prev => [...prev, `> ${cmd} (queued)`]);
        setActiveExecFile(`${nodeName}:${tokenId}:rsu`);
        try {
          await fetch('/api/v1/commandqueue/add', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'rsu', node_name: nodeName, token_id: tokenId, command: cmd, ip_address: nodeIp }) });
          maybeAutoStart();
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      }
      case 'lis_print_all': {
        // Batch all LIS commands for the node (same as batch-node with token_type LIS)
        setActiveTab('queue');
        setTerminalLog(prev => [...prev, `> Batch LIS print all for ${nodeName}`]);
        try {
          await fetch(`/api/v1/commandqueue/batch-node?project_id=${activeProjectId || ''}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ node_name: nodeName, token_type: 'LIS' }) });
          // LIS batch commands always auto-start — same rationale as lisdiag_run
          fetch('/api/v1/commandqueue/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }).catch(() => {});
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      }
      case 'diaglis_import': {
        // Queue a diaglis placeholder command
        const exeNumMatch = tokenId.match(/_exe(\d+)/);
        const exeNum = exeNumMatch ? parseInt(exeNumMatch[1], 10) : 1;
        const cmd = `diaglis placeholder exe${exeNum}`;
        setActiveTab('queue');
        setTerminalLog(prev => [...prev, `> ${cmd} (queued)`]);
        try {
          await fetch('/api/v1/commandqueue/add', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'diaglis', node_name: nodeName, token_id: tokenId, command: cmd, ip_address: nodeIp }) });
          maybeAutoStart();
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      }
      case 'open_file':
        handleDoubleClickFile(node);
        break;
      case 'fbc_scan':
      case 'rpc_scan':
        setActiveTab('scan');
        break;
      case 'clear_logs':
        break;
      case 'queue_restart':
        fetch('/api/v1/commandqueue/restart', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
          .catch(err => console.error('queue restart error:', err));
        break;
      case 'queue_clear':
        fetch('/api/v1/commandqueue/clear', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
          .catch(err => console.error('queue clear error:', err));
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
  }, [currentNodeName, handleDoubleClickFile, activeProjectId, maybeAutoStart]);

  // Queue All Logs — batch ALL nodes (FBC + RPC + LOG) into queue (does NOT auto-start)
  const handleQueueAll = useCallback(async () => {
    setPrinting(true);
    try {
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
      maybeAutoStart();
    } catch (err) {
      setTerminalLog(prev => [...prev, 'Queue All Error: ' + (err instanceof Error ? err.message : String(err))]);
    } finally {
      setPrinting(false);
    }
  }, [activeProjectId, maybeAutoStart]);

  // Queue controls (inline in top bar)
  // NOTE: No treeReloadKey bumps on queue control actions — tree refreshes
  // automatically when queue transitions from running→done/idle via NodeTree polling.
  const handleQueueStart = useCallback(async () => {
    await fetch('/api/v1/commandqueue/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
  }, []);
  const handleQueuePause = useCallback(async () => {
    await fetch('/api/v1/commandqueue/pause', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
  }, []);
  const handleQueueResume = useCallback(async () => {
    await fetch('/api/v1/commandqueue/resume', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
  }, []);
  const handleQueueStop = useCallback(async () => {
    await fetch('/api/v1/commandqueue/cancel', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
  }, []);
  const handleQueueClear = useCallback(async () => {
    await fetch('/api/v1/commandqueue/clear', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
  }, []);
  const handleQueueRestart = useCallback(async () => {
    await fetch('/api/v1/commandqueue/restart', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
  }, []);
  const handleQueueRetryFailed = useCallback(async () => {
    await fetch('/api/v1/commandqueue/retry-failed', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
  }, []);

  const handleBatchContextAction = useCallback(async (action: string, nodes: TreeNodeData[]) => {
    const singleAction = action.replace('batch_', '');
    for (const node of nodes) {
      await handleContextAction(singleAction, node);
    }
    maybeAutoStart();
  }, [handleContextAction, maybeAutoStart]);

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'debugger', label: 'Debugger', icon: <Terminal size={14} /> },
    { id: 'lisdiag', label: 'LisDiag', icon: <Network size={14} /> },
    { id: 'bstool', label: 'BsTool', icon: <Server size={14} /> },
    { id: 'scan', label: 'Scan', icon: <ScanLine size={14} /> },
    { id: 'logviewer', label: 'Log Viewer', icon: <FileText size={14} /> },
    { id: 'queue', label: 'Queue', icon: <ListChecks size={14} /> },
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
        <div style={{ position: 'relative', marginLeft: '8px' }}>
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
        <label style={{ fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer', color: 'var(--text-secondary)' }} title="Automatically start queue when a command is added">
          <input type="checkbox" checked={autoStart} onChange={(e) => setAutoStart(e.target.checked)} style={{ cursor: 'pointer' }} />
          Auto-start
        </label>
        {/* Queue controls — inline horizontal */}
        <button
          className="btn btn-primary"
          style={{ fontSize: '12px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '6px' }}
          onClick={handleQueueAll}
          disabled={printing}
          title="Queue all print commands for all nodes (does NOT auto-start)"
        >
          {printing ? <Loader2 size={12} className="spin" /> : <Printer size={12} />}
          All Logs Queue
        </button>
        {(queueStatus?.state === 'idle' || queueStatus?.state === 'done') && queueStatus?.total > 0 && (
          <button
            className="btn btn-primary"
            style={{ fontSize: '12px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '6px' }}
            onClick={handleQueueStart}
            title="Start queue execution"
          >
            <Play size={12} /> Start
          </button>
        )}
        {queueStatus?.state === 'running' && (
          <>
            <button
              className="btn btn-secondary"
              style={{ fontSize: '12px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '6px' }}
              onClick={handleQueuePause}
              title="Pause after current command"
            >
              <Pause size={12} /> Pause
            </button>
            <button
              className="btn btn-secondary"
              style={{ fontSize: '12px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '6px', color: '#ef4444' }}
              onClick={handleQueueStop}
              title="Stop queue"
            >
              <Square size={12} /> Stop
            </button>
          </>
        )}
        {queueStatus?.state === 'paused' && (
          <>
            <button
              className="btn btn-primary"
              style={{ fontSize: '12px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '6px' }}
              onClick={handleQueueResume}
              title="Resume queue execution"
            >
              <Play size={12} /> Resume
            </button>
            <button
              className="btn btn-secondary"
              style={{ fontSize: '12px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '6px', color: '#ef4444' }}
              onClick={handleQueueStop}
              title="Stop queue"
            >
              <Square size={12} /> Stop
            </button>
          </>
        )}
        {/* Clear + Restart always visible */}
        <button
          className="btn btn-ghost"
          style={{ fontSize: '12px', padding: '4px 8px', display: 'flex', alignItems: 'center', gap: '4px' }}
          onClick={handleQueueRestart}
          title="Restart — reset all commands to pending"
        >
          <RotateCcw size={12} /> Restart
        </button>
        {queueStatus?.commands?.some(c => c.status === 'failed') && (queueStatus?.state === 'idle' || queueStatus?.state === 'done') && (
          <button
            className="btn btn-ghost"
            style={{ fontSize: '12px', padding: '4px 8px', display: 'flex', alignItems: 'center', gap: '4px', color: '#f59e0b', borderColor: '#f59e0b' }}
            onClick={handleQueueRetryFailed}
            title="Retry only failed commands"
          >
            <AlertCircle size={12} /> Retry Failed
          </button>
        )}
        <button
          className="btn btn-ghost"
          style={{ fontSize: '12px', padding: '4px 8px', display: 'flex', alignItems: 'center', gap: '4px' }}
          onClick={handleQueueClear}
          title="Clear pending commands"
        >
          <Trash2 size={12} /> Clear
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
      ) : (
      <>
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <div style={{ width: '40%', minWidth: '250px', borderRight: '1px solid var(--border)', overflow: 'hidden' }}>
          <NodeTree reloadKey={treeReloadKey} projectId={activeProjectId} onSelectNode={handleSelectNode} onSelectToken={handleSelectToken} onContextAction={handleContextAction} onBatchContextAction={handleBatchContextAction} onDoubleClickFile={handleDoubleClickFile} onQueueStatusChange={setQueueStatus} selectedFileKey={selectedFileKey} activeExecFile={activeExecFile} />
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ display: 'flex', gap: '2px', padding: '0 12px', borderBottom: '1px solid var(--border)', backgroundColor: 'var(--bg-secondary)' }}>
            {tabs.map((t) => (
              <button key={t.id} onClick={() => setActiveTab(t.id)} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', fontSize: '12px', fontWeight: activeTab === t.id ? 600 : 400, color: activeTab === t.id ? 'var(--accent)' : 'var(--text-secondary)', backgroundColor: 'transparent', border: 'none', borderBottom: activeTab === t.id ? '2px solid var(--accent)' : '2px solid transparent', cursor: 'pointer', fontFamily: 'var(--font-sans)', transition: 'all 0.15s ease' }}>
                {t.icon}{t.label}
              </button>
            ))}
          </div>
          <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
            {activeTab === 'debugger' && (
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <TelnetTerminal currentToken={currentToken} currentTokenType={currentTokenType} currentNodeName={currentNodeName} pendingCommand={pendingCommand} onCommandSent={() => setPendingCommand(null)} externalLog={terminalLog} />
              </div>
            )}
            {activeTab === 'lisdiag' && (
              <LisDiagTab
                targetIP={lisdiagTarget?.ip || ''}
                targetNode={lisdiagTarget?.node || ''}
                tokenID={lisdiagTarget?.tokenID || ''}
                password={lisdiagTarget?.password || ''}
                exeNum={lisdiagTarget?.exeNum || 0}
                commands={lisdiagTarget?.commands || []}
              />
            )}
            {activeTab === 'bstool' && <BsToolPanel pendingServerName={pendingServerName} onServerNameConsumed={() => { setPendingServerName(null); setPendingNodeIp(null); }} currentNodeName={currentNodeName} pendingNodeIp={pendingNodeIp} onExecutionComplete={() => setTreeReloadKey((k) => k + 1)} />}
            {activeTab === 'scan' && <ScanTab selectedNode={selectedNode} logRoot={activeLogRoot || localStorage.getItem('logRoot') || ''} />}
            {activeTab === 'logviewer' && (
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%', backgroundColor: 'var(--bg-primary)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px', borderBottom: '1px solid var(--border)' }}>
                  <FileText size={14} color="var(--accent)" />
                  <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{fileViewName || 'No file selected'}</span>
                  {fileViewPath && <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: 'auto', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={fileViewPath}>{fileViewPath}</span>}
                  {fileContent && !editingFile && (
                    <button className="btn btn-ghost" style={{ fontSize: '11px', padding: '3px 8px', display: 'flex', alignItems: 'center', gap: '4px', marginLeft: fileViewPath ? '0' : 'auto' }} onClick={() => { setEditContent(fileContent); setEditingFile(true); }} title="Edit file content">
                      <Edit2 size={12} /> Edit
                    </button>
                  )}
                  {editingFile && (
                    <>
                      <button className="btn btn-primary" style={{ fontSize: '11px', padding: '3px 8px', display: 'flex', alignItems: 'center', gap: '4px', marginLeft: 'auto' }} onClick={async () => {
                        setSavingFile(true);
                        try {
                          const res = await fetch('/api/v1/logs/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path: fileViewPath, content: editContent }) });
                          if (res.ok) {
                            setFileContent(editContent);
                            setEditingFile(false);
                            setTreeReloadKey((k) => k + 1);
                            setTerminalLog(prev => [...prev, '[File saved: ' + fileViewName + ']']);
                          } else {
                            const data = await res.json().catch(() => ({ message: 'Save failed' }));
                            setTerminalLog(prev => [...prev, 'Error saving: ' + (data.message || 'Unknown')]);
                          }
                        } catch (err) { setTerminalLog(prev => [...prev, 'Error saving: ' + (err instanceof Error ? err.message : String(err))]); }
                        finally { setSavingFile(false); }
                      }} disabled={savingFile} title="Save changes">
                        {savingFile ? <Loader2 size={12} className="spin" /> : <Save size={12} />} Save
                      </button>
                      <button className="btn btn-ghost" style={{ fontSize: '11px', padding: '3px 8px', display: 'flex', alignItems: 'center', gap: '4px' }} onClick={() => { setEditingFile(false); setEditContent(''); }} title="Cancel edit">
                        Cancel
                      </button>
                      <button className="btn btn-ghost" style={{ fontSize: '11px', padding: '3px 8px', display: 'flex', alignItems: 'center', gap: '4px' }} onClick={async () => {
                        try {
                          const clipText = await navigator.clipboard.readText();
                          setEditContent(clipText);
                          setTerminalLog(prev => [...prev, '[Pasted from clipboard: ' + clipText.length + ' chars]']);
                        } catch { setTerminalLog(prev => [...prev, 'Error: clipboard access denied']); }
                      }} title="Paste from clipboard (replaces content)">
                        <Clipboard size={12} /> Paste
                      </button>
                    </>
                  )}
                </div>
                <div style={{ flex: 1, overflow: 'auto', padding: editingFile ? '0' : '12px' }}>
                  {fileLoading ? (
                    <div style={{ textAlign: 'center', padding: '24px' }}><Loader2 size={20} color="var(--accent)" className="spin" /><p style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '8px' }}>Loading file...</p></div>
                  ) : editingFile ? (
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      style={{ width: '100%', height: '100%', fontSize: '12px', fontFamily: 'var(--font-mono)', backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)', border: 'none', outline: 'none', padding: '12px', resize: 'none', whiteSpace: 'pre-wrap', lineHeight: '1.5' }}
                      spellCheck={false}
                    />
                  ) : fileContent ? <ColorizedLog content={fileContent} /> : (
                    <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)', fontSize: '12px' }}>Click a file in the node tree to view its content.</div>
                  )}
                </div>
              </div>
            )}
            {activeTab === 'queue' && <QueueTab onQueueChange={setQueueStatus} />}
          </div>
        </div>
      </div>
      </>
      )}
      <CommandQueueBar status={queueStatus} />
    </div>
  );
}
