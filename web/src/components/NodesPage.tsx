import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Server, Loader2, Box, Upload, Plus, Trash2, Save, FolderOpen, FileText, ScanLine } from 'lucide-react';
import NodeTree from './NodeTree';
import CommandQueueBar from './CommandQueueBar';
import DirBrowser from './DirBrowser';
import { useActiveProject, useProjects } from '../hooks/useActiveProject';
import type { TreeNodeData, QueueStatusResponse, NodeConfig } from '../types/api';

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

export default function NodesPage() {
  const { activeProjectId, activeLogRoot } = useActiveProject();
  const { projects } = useProjects();
  const activeProject = projects.find((p) => p.id === activeProjectId) || null;
  const navigate = useNavigate();
  const [showFileModal, setShowFileModal] = useState(false);
  const [, setSelectedNode] = useState<TreeNodeData | null>(null);
  const [, setSelectedToken] = useState<TreeNodeData | null>(null);
  const [currentNodeName, setCurrentNodeName] = useState('');
  const [queueStatus, setQueueStatus] = useState<QueueStatusResponse | null>(null);
  const toolbarRef = useRef<{ save: () => void; addNode: () => void; openFile: () => void; toggleImport: () => void; isSaving: () => boolean; getSaveMsg: () => string | null } | null>(null);
  const [treeReloadKey, setTreeReloadKey] = useState(0);
  const [fileContent, setFileContent] = useState<string>('');
  const [fileViewName, setFileViewName] = useState<string>('');
  const [fileViewPath, setFileViewPath] = useState<string>('');
  const [fileLoading, setFileLoading] = useState(false);
  const [, setTerminalLog] = useState<string[]>([]);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<{ count: number; configs: NodeConfig[]; structure?: string } | null>(null);
  const [selectedFileKey, setSelectedFileKey] = useState<string | null>(null);

  // Scan Nodes: connect to DIA, parse structure, probe tokens
  const handleScanNodes = useCallback(async () => {
    setScanning(true);
    setScanResult(null);
    try {
      const res = await fetch('/api/v1/sysfiles/scan-nodes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Scan failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      const data = await res.json();
      const configs: NodeConfig[] = data.configs || [];
      setScanResult({ count: configs.length, configs, structure: data.structure_raw });
      // Reload tree with newly scanned nodes
      setTreeReloadKey((k) => k + 1);
    } catch (err) {
      setTerminalLog(prev => [...prev, 'Scan Error: ' + (err instanceof Error ? err.message : String(err))]);
    } finally {
      setScanning(false);
    }
  }, []);

  // Auto-set log root from shared hook (only if not already set by project selection)
  useEffect(() => {
    if (activeLogRoot) {
      // Ensure backend knows about the log root
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
    // Build file key for bidirectional highlighting
    if (token.type === 'file' || token.type === 'token') {
      const sectionType = token.section_type || '';
      const fileName = token.file_name || token.name;
      // Station name comes from the parent node — but we only have currentNodeName
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
      setShowFileModal(true);
      setFileViewName(fileName);
      return;
    }
    setFileLoading(true);
    setFileViewName(fileName);
    setFileViewPath(filePath);
    setShowFileModal(true);
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

  const handleCreateStructure = useCallback(async () => {
    const logRoot = activeLogRoot || localStorage.getItem('logRoot') || '';
    try {
      const res = await fetch('/api/v1/nodesconfig/create-structure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ log_root: logRoot }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setTerminalLog(prev => [...prev, `[Structure created: ${data.created_dirs} dirs, ${data.created_files} files at ${data.log_root}]`]);
      setTreeReloadKey((k) => k + 1);
    } catch (err) {
      setTerminalLog(prev => [...prev, 'Error creating structure: ' + (err instanceof Error ? err.message : String(err))]);
    }
  }, [activeLogRoot]);

  const handleDeleteStructure = useCallback(async () => {
    const logRoot = activeLogRoot || localStorage.getItem('logRoot') || '';
    try {
      const res = await fetch('/api/v1/nodesconfig/delete-structure', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ log_root: logRoot }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setTerminalLog(prev => [...prev, `[Structure deleted: ${data.log_dir} ${data.deleted ? 'removed' : 'did not exist'}]`]);
      setTreeReloadKey((k) => k + 1);
    } catch (err) {
      setTerminalLog(prev => [...prev, 'Error deleting structure: ' + (err instanceof Error ? err.message : String(err))]);
    }
  }, [activeLogRoot]);

  const handleFileMove = useCallback(async (sourcePath: string, targetPath: string) => {
    setTerminalLog(prev => [...prev, '> Moving file: ' + sourcePath + ' → ' + targetPath]);
    try {
      const res = await fetch('/api/v1/logs/move', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ source_path: sourcePath, target_path: targetPath }) });
      const data = await res.json();
      if (data.moved) {
        setTerminalLog(prev => [...prev, '[File moved: ' + data.source_path + ' → ' + data.target_path + ']']);
      } else {
        setTerminalLog(prev => [...prev, 'Error: ' + (data.message || 'Move failed')]);
      }
    } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
  }, []);

  const handleContextAction = useCallback(async (action: string, node: TreeNodeData, parentNode?: TreeNodeData) => {
    let nodeName = node.name || currentNodeName;
    const tokenId = node.token_id || '';
    if (node.type === 'token' || node.type === 'file') {
      const fn = node.file_name || node.name;
      const parts = fn.split('_');
      if (parts.length >= 2) nodeName = parts[0];
    }
    switch (action) {
      case 'open_file':
        handleDoubleClickFile(node);
        break;
      case 'rename_node': {
        const newName = window.prompt('Enter new name for node:', node.name);
        if (!newName || newName === node.name) break;
        setTerminalLog(prev => [...prev, '> Renaming node: ' + node.name + ' → ' + newName]);
        try {
          // Update in nodes.json via rename endpoint
          const res = await fetch(`/api/v1/nodesconfig/rename?name=${encodeURIComponent(node.name)}&project_id=${activeProjectId || ''}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_name: newName }),
          });
          const data = await res.json();
          if (data.renamed) {
            setTerminalLog(prev => [...prev, '[Node renamed: ' + node.name + ' → ' + newName + ']']);
            setTreeReloadKey((k) => k + 1);
          } else {
            setTerminalLog(prev => [...prev, 'Error: ' + (data.message || 'Rename failed')]);
          }
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      }
      case 'delete_node': {
        if (!window.confirm('Delete node "' + node.name + '" and all its files?\nThis removes the node from nodes.json and deletes the folder from disk.')) break;
        setTerminalLog(prev => [...prev, '> Deleting node: ' + node.name]);
        try {
          // Delete from nodes.json
          const res = await fetch(`/api/v1/nodesconfig/entry?name=${encodeURIComponent(node.name)}&project_id=${activeProjectId || ''}`, {
            method: 'DELETE',
          });
          const data = await res.json();
          if (data.deleted) {
            setTerminalLog(prev => [...prev, '[Node deleted from config: ' + node.name + ']']);
          } else {
            setTerminalLog(prev => [...prev, 'Warning: ' + (data.message || 'Node not found in config')]);
          }
          // Also delete the folder from disk
          const logRoot = activeLogRoot || '';
          if (logRoot) {
            const folderPath = logRoot + '/' + node.name;
            try {
              await fetch('/api/v1/logs/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: folderPath }),
              });
            } catch { /* folder deletion is best-effort */ }
          }
          setTreeReloadKey((k) => k + 1);
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      }
      case 'erase_file': {
        const filePath = node.file_path || '';
        const sectionType = node.section_type || '';
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
      case 'delete_file': {
        const filePath = node.file_path || '';
        const sectionType = node.section_type || '';
        if (!window.confirm('Delete file: ' + (node.file_name || node.name) + '?\nThis removes the file from disk entirely.')) break;
        setTerminalLog(prev => [...prev, '> Deleting file: ' + (node.file_name || node.name)]);
        try {
          const body = filePath ? { path: filePath } : { node_name: nodeName, token_type: sectionType, token_id: tokenId };
          const res = await fetch('/api/v1/logs/delete', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
          const data = await res.json();
          if (data.deleted) {
            setTerminalLog(prev => [...prev, '[File deleted: ' + data.path + ']']);
          } else {
            setTerminalLog(prev => [...prev, 'Error: ' + (data.message || 'Delete failed')]);
          }
          setTreeReloadKey((k) => k + 1);
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      }
      case 'create_file': {
        const filePath = node.file_path || '';
        const sectionType = node.section_type || '';
        setTerminalLog(prev => [...prev, '> Creating file: ' + (node.file_name || node.name)]);
        try {
          const body = filePath ? { path: filePath } : { node_name: nodeName, token_type: sectionType, token_id: tokenId, ip_address: node.ip || '' };
          const res = await fetch('/api/v1/logs/create', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
          const data = await res.json();
          if (data.created) {
            setTerminalLog(prev => [...prev, '[File created: ' + data.path + ']']);
          } else {
            setTerminalLog(prev => [...prev, 'Error: ' + (data.message || 'Create failed')]);
          }
          setTreeReloadKey((k) => k + 1);
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      }
      case 'move_file': {
        const filePath = node.file_path || '';
        if (!filePath) {
          setTerminalLog(prev => [...prev, 'Error: No file path available for move']);
          break;
        }
        const targetSubfolder = window.prompt('Move to subfolder (FBC, RPC, LOG, etc.):', node.section_type || '');
        if (!targetSubfolder) break;
        setTerminalLog(prev => [...prev, '> Moving file to ' + targetSubfolder + '/']);
        try {
          const res = await fetch('/api/v1/logs/move', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ source_path: filePath, target_subfolder: targetSubfolder }) });
          const data = await res.json();
          if (data.moved) {
            setTerminalLog(prev => [...prev, '[File moved: ' + data.source_path + ' → ' + data.target_path + ']']);
          } else {
            setTerminalLog(prev => [...prev, 'Error: ' + (data.message || 'Move failed')]);
          }
          setTreeReloadKey((k) => k + 1);
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      }
      case 'create_folder': {
        const folderName = window.prompt('Enter folder name:', '');
        if (!folderName) break;
        // Build path from node context
        const logRoot = activeLogRoot || localStorage.getItem('logRoot') || '';
        let folderPath = '';
        if (node.type === 'node') {
          folderPath = logRoot + '/' + node.name + '/' + folderName;
        } else if (node.type === 'group') {
          const stationName = parentNode?.name || nodeName;
          folderPath = logRoot + '/' + stationName + '/' + folderName;
        } else {
          folderPath = logRoot + '/' + folderName;
        }
        setTerminalLog(prev => [...prev, '> Creating folder: ' + folderPath]);
        try {
          const res = await fetch('/api/v1/logs/create-folder', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path: folderPath }) });
          const data = await res.json();
          if (data.created) {
            setTerminalLog(prev => [...prev, '[Folder created: ' + data.path + ']']);
          } else {
            setTerminalLog(prev => [...prev, 'Error: ' + (data.message || 'Create folder failed')]);
          }
          setTreeReloadKey((k) => k + 1);
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      }
      case 'create_file_in_group': {
        const fileName = window.prompt('Enter file name:', '');
        if (!fileName) break;
        const logRoot = activeLogRoot || localStorage.getItem('logRoot') || '';
        const stationName = parentNode?.name || nodeName;
        const sectionType = node.section_type || node.name || '';
        const filePath = logRoot + '/' + stationName + '/' + sectionType.toLowerCase() + '/' + fileName;
        setTerminalLog(prev => [...prev, '> Creating file: ' + filePath]);
        try {
          const res = await fetch('/api/v1/logs/create', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path: filePath }) });
          const data = await res.json();
          if (data.created) {
            setTerminalLog(prev => [...prev, '[File created: ' + data.path + ']']);
          } else {
            setTerminalLog(prev => [...prev, 'Error: ' + (data.message || 'Create file failed')]);
          }
          setTreeReloadKey((k) => k + 1);
        } catch (err) { setTerminalLog(prev => [...prev, 'Error: ' + (err instanceof Error ? err.message : String(err))]); }
        break;
      }
      default:
        break;
    }
  }, [currentNodeName, handleDoubleClickFile, activeProjectId, activeLogRoot]);



  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '6px 16px', borderBottom: '1px solid var(--border)', backgroundColor: 'var(--bg-secondary)', flexShrink: 0 }}>
        <Server size={18} color="var(--accent)" />
        <h1 style={{ fontSize: '16px', fontWeight: 700 }}>Nodes</h1>
        {activeProject ? (
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: '4px' }} title={activeLogRoot || 'No log root set'}>
            {activeProject.project_number} — {activeProject.ship_name}
            {activeLogRoot && <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: '6px', fontFamily: 'var(--font-mono)' }}>({activeLogRoot})</span>}
          </span>
        ) : (
          <span style={{ fontSize: '11px', color: 'var(--warning)', marginLeft: '4px' }}>
            No project selected — go to Dashboard
          </span>
        )}
        <div style={{ flex: 1 }} />
        {activeProjectId && (
          <>
            <button
              className="btn btn-ghost"
              style={{ fontSize: '12px', padding: '4px 8px', display: 'flex', alignItems: 'center', gap: '6px' }}
              onClick={() => toolbarRef.current?.openFile()}
              title="Open existing nodes.json file"
            >
              <FolderOpen size={14} />
              Open File
            </button>
            <button
              className="btn btn-ghost"
              style={{ fontSize: '12px', padding: '4px 8px', display: 'flex', alignItems: 'center', gap: '6px' }}
              onClick={() => toolbarRef.current?.toggleImport()}
              title="Import nodes from .sys files"
            >
              <Upload size={14} />
              Import
            </button>
            <button
              className="btn btn-ghost"
              style={{ fontSize: '12px', padding: '4px 8px', display: 'flex', alignItems: 'center', gap: '6px' }}
              onClick={() => toolbarRef.current?.addNode()}
              title="Add a new node manually"
            >
              <Plus size={14} />
              Add Node
            </button>
            <button
              className="btn btn-primary"
              style={{ fontSize: '12px', padding: '4px 12px', display: 'flex', alignItems: 'center', gap: '6px' }}
              onClick={() => toolbarRef.current?.save()}
              disabled={toolbarRef.current?.isSaving() || false}
              title="Save all node changes"
            >
              <Save size={14} />
              Save Changes
            </button>
          </>
        )}
        <button
          className="btn btn-secondary"
          style={{ fontSize: '12px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '6px' }}
          onClick={handleScanNodes}
          disabled={scanning || !activeProjectId}
          title="Scan DIA for active nodes (print structure)"
        >
          {scanning ? <Loader2 size={12} className="spin" /> : <ScanLine size={12} />}
          Scan Nodes
        </button>
      </div>

      {/* No project state */}
      {!activeProjectId ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: '48px', textAlign: 'center' }}>
          <Server size={48} color="var(--text-muted)" style={{ marginBottom: '16px' }} />
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '16px' }}>
            No project selected. Select a project from the Dashboard to manage nodes.
          </p>
          <button className="btn btn-primary" onClick={() => navigate('/')}>
            Go to Dashboard
          </button>
        </div>
      ) : (
      <>
      <div style={{ display: 'flex', flex: 1, overflow: 'auto' }}>
        <div style={{ width: '40%', minWidth: '250px', borderRight: '1px solid var(--border)', overflow: 'auto' }}>
          <NodeTree key={treeReloadKey} projectId={activeProjectId} onSelectNode={handleSelectNode} onSelectToken={handleSelectToken} onContextAction={handleContextAction} onDoubleClickFile={handleDoubleClickFile} onQueueStatusChange={setQueueStatus} selectedFileKey={selectedFileKey} onCreateStructure={handleCreateStructure} onDeleteStructure={handleDeleteStructure} context="nodes" colorMode="nodes" onFileMove={handleFileMove} />
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
          <div style={{ flex: 1, overflow: 'auto' }}>
            <NodesTabContent projectId={activeProjectId} onNodesSaved={() => setTreeReloadKey((k) => k + 1)} onScanNodes={handleScanNodes} scanning={scanning} scanResult={scanResult} toolbarRef={toolbarRef} />
          </div>
        </div>
      </div>
      </>
      )}
      {/* File content modal overlay — always available */}
      {showFileModal && (
        <div
          style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200 }}
          onClick={(e) => { if (e.target === e.currentTarget) { setShowFileModal(false); setFileContent(''); } }}
        >
          <div style={{ width: '80%', maxWidth: '900px', maxHeight: '80vh', backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: '8px', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
              <FileText size={14} color="var(--accent)" />
              <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{fileViewName || 'No file selected'}</span>
              {fileViewPath && <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: 'auto' }} title={fileViewPath}>{fileViewPath}</span>}
              <button className="btn btn-ghost" style={{ fontSize: '14px', padding: '2px 8px', marginLeft: '8px' }} onClick={() => { setShowFileModal(false); setFileContent(''); }}>✕</button>
            </div>
            <div style={{ flex: 1, overflow: 'auto', padding: '12px' }}>
              {fileLoading ? (
                <div style={{ textAlign: 'center', padding: '24px' }}><Loader2 size={20} color="var(--accent)" className="spin" /><p style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '8px' }}>Loading file...</p></div>
              ) : fileContent ? <ColorizedLog content={fileContent} /> : (
                <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)', fontSize: '12px' }}>No content.</div>
              )}
            </div>
          </div>
        </div>
      )}
      <CommandQueueBar status={queueStatus} />
    </div>
  );
}


interface NodesTabContentProps {
  projectId: number | null;
  onNodesSaved: () => void;
  onScanNodes?: () => void;
  scanning?: boolean;
  scanResult?: { count: number; configs: NodeConfig[]; structure?: string } | null;
  toolbarRef?: React.MutableRefObject<{ save: () => void; addNode: () => void; openFile: () => void; toggleImport: () => void; isSaving: () => boolean; getSaveMsg: () => string | null } | null>;
}

function NodesTabContent({ projectId, onNodesSaved, toolbarRef }: NodesTabContentProps) {
  // Node config state (NodeConfig[] from nodesconfig API)
  const [nodes, setNodes] = useState<NodeConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingStation, setEditingStation] = useState<string | null>(null);
  const [editNodes, setEditNodes] = useState<NodeConfig[]>([]);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Open nodes.json file via file picker
  function handleOpenNodesFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const text = (ev.target?.result as string) || '';
        const configs = JSON.parse(text);
        if (Array.isArray(configs)) {
          setNodes(configs);
          setSaveMsg('Loaded ' + configs.length + ' nodes from ' + file.name);
          setTimeout(() => setSaveMsg(null), 5000);
        } else {
          setSaveMsg('Error: File is not a valid nodes.json array');
        }
      } catch (err) {
        setSaveMsg('Error parsing file: ' + (err instanceof Error ? err.message : String(err)));
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  }

  // Sys file import state
  const [importDir, setImportDir] = useState(localStorage.getItem('sysDir') || '');
  const [importScanning, setImportScanning] = useState(false);
  const [importResult, setImportResult] = useState<{ count: number; totalBefore: number; configs: NodeConfig[] } | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [selectedImports, setSelectedImports] = useState<Set<number>>(new Set());
  const [singleSysPath, setSingleSysPath] = useState('');
  const [showImport, setShowImport] = useState(false);
  const [showDirBrowser, setShowDirBrowser] = useState(false);
  const [multiFileUploading, setMultiFileUploading] = useState(false);
  const multiFileInputRef = useRef<HTMLInputElement>(null);

  // Load from project state
  const [, setAllProjects] = useState<Array<{ id: number; project_number: string; ship_name: string }>>([]);
  const [, setLoadProjectId] = useState<number | ''>('');

  // ─── Station grouping helpers ────────────────────────────────────
  function getStationName(name: string): string {
    // Extract base station name and append m (main) or r (reserve)
    // AP01 → AP01m, AP01 Main → AP01m, AP01_m2 → AP01m
    // AP02 Reserve → AP02r, AP02_r2 → AP02r
    // AL01 → AL01, A1OA OPS → A1OA (no m/r for non-PCS)
    // AP01m → AP01m (already has m suffix, don't double it)
    
    // Strip _mN or _rN suffix (e.g. _m2, _r3)
    let base = name.replace(/_m\d+$/, '').replace(/_r\d+$/, '');
    // Strip " Main" or " Reserve" suffix
    base = base.replace(/\s+Main$/, '').replace(/\s+Reserve$/, '');
    
    // If name already ends with 'm' or 'r' (e.g. AP01m, AP02r), it's already a station name
    if (/^[A-Z]+.*[mr]$/.test(base)) {
      return base;
    }
    
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
  // NOTE: allProjects, loadProjectId, handleLoadFromProject are retained for future
  // "Load from project" feature but currently unused in render. Suppressed via eslint.
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
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
  // Retained for future "Load from project" UI feature
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
  // Suppress unused warning — function is for future UI feature
  void handleLoadFromProject;

  // ─── Fetch nodes for active project ────────────────────────────
  const fetchNodes = useCallback(async () => {
    if (!projectId) {
      setNodes([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/nodesconfig?project_id=${projectId}`);
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

  // ─── Expose toolbar actions via ref ──────────────────────────────
  useEffect(() => {
    if (toolbarRef) {
      toolbarRef.current = {
        save: handleSaveAll,
        addNode: handleAddNode,
        openFile: () => fileInputRef.current?.click(),
        toggleImport: () => setShowImport(!showImport),
        isSaving: () => saving,
        getSaveMsg: () => saveMsg,
      };
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [saving, saveMsg, showImport]); // Update ref when closures change

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

  // ─── Import multiple .sys files via file picker ───────────────────
  async function handleMultiFileImport(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    setMultiFileUploading(true);
    setImportError(null);
    setImportResult(null);
    setSelectedImports(new Set());
    try {
      const formData = new FormData();
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }
      const res = await fetch('/api/v1/sysfiles/parse-multi', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ message: 'Parse failed' }));
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      const data = await res.json();
      const configs: NodeConfig[] = data.configs || [];
      if (configs.length === 0) {
        setImportError('No nodes found in uploaded files');
        return;
      }
      setImportResult({ count: configs.length, totalBefore: configs.length, configs });
      setSelectedImports(new Set(configs.map((_, i) => i)));
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Multi-file import failed');
    } finally {
      setMultiFileUploading(false);
      e.target.value = '';
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

  return (
    <div style={{ height: '100%', overflow: 'auto', backgroundColor: 'var(--bg-primary)' }}>
      {/* Hidden file input for Open File button (triggered from header) */}
      <input
        type="file"
        ref={fileInputRef}
        accept=".json"
        onChange={handleOpenNodesFile}
        style={{ display: 'none' }}
      />
      {/* Hidden file input for multi .sys file import */}
      <input
        type="file"
        ref={multiFileInputRef}
        accept=".sys"
        multiple
        onChange={handleMultiFileImport}
        style={{ display: 'none' }}
      />

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
            <button
              className="btn btn-secondary"
              style={{ fontSize: '12px', padding: '4px 8px', display: 'flex', alignItems: 'center', gap: '6px' }}
              onClick={() => setShowDirBrowser(true)}
              title="Browse for directory"
            >
              <FolderOpen size={14} />
              Browse
            </button>
            <input
              type="text"
              value={importDir}
              onChange={(e) => setImportDir(e.target.value)}
              placeholder="C:\dna\CA\bu or click Browse"
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

          {/* Select multiple .sys files via file picker */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginTop: '8px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Or select multiple .sys files:</span>
            <button
              className="btn btn-secondary"
              style={{ fontSize: '12px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '6px' }}
              onClick={() => multiFileInputRef.current?.click()}
              disabled={multiFileUploading}
              title="Select one or more .sys files from file explorer"
            >
              {multiFileUploading ? <Loader2 size={14} className="spin" /> : <FileText size={14} />}
              {multiFileUploading ? 'Parsing...' : 'Select .sys Files'}
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
                            if (slotNum === 1) return { ...n, name: newStationName };
                            // Strip existing m/r suffix before appending slot suffix
                            const base = newStationName.replace(/[mr]$/, '');
                            return { ...n, name: `${base}_m${slotNum}` };
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
                            padding: '4px 0',
                            borderBottom: '1px solid var(--border)',
                            fontSize: '12px',
                            fontFamily: 'var(--font-mono)',
                          }}
                        >
                          {/* Slot header row: Slot N + node name */}
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <span style={{ fontWeight: 600, color: 'var(--text-primary)', minWidth: '48px' }}>
                              Slot {slot.slotNumber}
                            </span>
                            <span style={{ color: 'var(--text-secondary)' }}>
                              {slot.node.name}
                            </span>
                          </div>
                          {/* Token badges stacked vertically below */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', marginTop: '3px', paddingLeft: '54px' }}>
                            {slot.node.tokens.map((t, ti) => (
                              <span key={ti} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <span style={{
                                  fontSize: '10px',
                                  fontWeight: 700,
                                  padding: '1px 6px',
                                  borderRadius: '8px',
                                  backgroundColor: (TOKEN_COLORS[t.token_type] || '#666') + '22',
                                  color: TOKEN_COLORS[t.token_type] || '#666',
                                  border: `1px solid ${TOKEN_COLORS[t.token_type] || '#666'}44`,
                                  flexShrink: 0,
                                }}>
                                  {t.token_type}
                                </span>
                                <span style={{ fontSize: '10px', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={t.token_id}>{t.token_id}</span>
                              </span>
                            ))}
                          </div>
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
      <DirBrowser
        open={showDirBrowser}
        onSelect={(path) => setImportDir(path)}
        onClose={() => setShowDirBrowser(false)}
        title="Select BU Directory"
        initialPath={importDir || 'C:\\dna\\CA\\bu'}
        selectLabel="Select Directory"
      />
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
