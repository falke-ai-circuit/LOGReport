// @ts-nocheck
import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Server, Loader2, ScanLine, FolderOpen, Upload, Plus, Trash2, Save, FileText } from 'lucide-react';
import NodeTree from './NodeTree';
import CommandQueueBar from './CommandQueueBar';
import { useActiveProject, useProjects } from '../hooks/useActiveProject';
import type { TreeNodeData, QueueStatusResponse, NodeConfig } from '../types/api';
import { ColorizedLog } from './ColorizedLog';
import { NodesTabContent } from './NodesTabContent';

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
  const [terminalLog, setTerminalLog] = useState<string[]>([]);
  const [scanning, setScanning] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [scanResult, setScanResult] = useState<{ count: number; configs: NodeConfig[]; structure?: string } | null>(null);
  const [selectedFileKey, setSelectedFileKey] = useState<string | null>(null);

  // Scan Nodes: scan BU directory for .sys files, save to backend, reload tree
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
      // Save configs to backend so tree shows them
      if (configs.length > 0 && activeProjectId) {
        await fetch(`/api/v1/nodesconfig?project_id=${activeProjectId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(configs),
        });
      }
      // Reload tree with newly scanned nodes
      setTreeReloadKey((k) => k + 1);
    } catch (err) {
      setTerminalLog(prev => [...prev, 'Scan Error: ' + (err instanceof Error ? err.message : String(err))]);
    } finally {
      setScanning(false);
    }
  }, [activeProjectId]);

  // Clear Nodes: remove all node configs for the active project
  const handleClearNodes = useCallback(async () => {
    if (!activeProjectId) return;
    if (!window.confirm('Remove ALL detected nodes from this project? This cannot be undone.')) return;
    setClearing(true);
    try {
      // Save empty array to clear all node configs
      await fetch(`/api/v1/nodesconfig?project_id=${activeProjectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify([]),
      });
      setScanResult(null);
      setTreeReloadKey((k) => k + 1);
      setTerminalLog(prev => [...prev, '[All nodes cleared]']);
    } catch (err) {
      setTerminalLog(prev => [...prev, 'Error clearing nodes: ' + (err instanceof Error ? err.message : String(err))]);
    } finally {
      setClearing(false);
    }
  }, [activeProjectId]);

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
      case 'erase_file': {
        const filePath = node.file_path || '';
        const tokenId = node.token_id || '';
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
        const tokenId = node.token_id || '';
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
        const tokenId = node.token_id || '';
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
  }, [currentNodeName, handleDoubleClickFile]);



  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
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
              className="btn btn-ghost"
              style={{ fontSize: '12px', padding: '4px 8px', display: 'flex', alignItems: 'center', gap: '6px' }}
              onClick={handleClearNodes}
              disabled={clearing || !activeProjectId}
              title="Remove all detected nodes from the project"
            >
              {clearing ? <Loader2 size={14} className="spin" /> : <Trash2 size={14} />}
              Clear Nodes
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
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <div style={{ width: '40%', minWidth: '250px', borderRight: '1px solid var(--border)', overflow: 'hidden' }}>
          <NodeTree reloadKey={treeReloadKey} projectId={activeProjectId} onSelectNode={handleSelectNode} onSelectToken={handleSelectToken} onContextAction={handleContextAction} onDoubleClickFile={handleDoubleClickFile} onQueueStatusChange={setQueueStatus} selectedFileKey={selectedFileKey} onCreateStructure={handleCreateStructure} onDeleteStructure={handleDeleteStructure} context="nodes" colorMode="nodes" onFileMove={handleFileMove} />
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ flex: 1, overflow: 'hidden' }}>
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
