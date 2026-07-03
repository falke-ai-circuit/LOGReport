import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Server,
  Loader2,
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  Circle,
  Play,
  Printer,
  FileText,
  Trash2,
  ScanLine,
  RefreshCw,
  FolderPlus,
  Edit3,
} from 'lucide-react';
import type { TreeNodeData, QueueStatusResponse } from '../types/api';
import { useActiveProject } from '../hooks/useActiveProject';

export interface NodeTreeProps {
  onSelectNode: (node: TreeNodeData) => void;
  onSelectToken: (token: TreeNodeData) => void;
  onContextAction: (action: string, node: TreeNodeData, parentNode?: TreeNodeData) => void;
  onDoubleClickFile: (node: TreeNodeData) => void;
  onQueueStatusChange?: (status: QueueStatusResponse | null) => void;
  projectId?: number | null;
  selectedFileKey?: string | null;
  activeExecFile?: string | null;
  onCreateStructure?: () => void;
  onDeleteStructure?: () => void;
  context?: 'nodes' | 'commander';
  colorMode?: 'nodes' | 'commander';
  onFileMove?: (sourcePath: string, targetPath: string) => Promise<void>;
}

// Command status colors for file nodes during queue execution
const CMD_STATUS_COLORS: Record<string, string> = {
  pending: 'var(--text-muted)',
  running: 'var(--accent)',
  completed: 'var(--success)',
  done: 'var(--success)',
  failed: '#f97316', // orange — distinct from empty-file red
  error: '#f97316',  // orange — command error
  cancelled: '#6b7280', // gray
};

const STATUS_COLORS: Record<string, string> = {
  idle: 'var(--text-muted)',
  connected: 'var(--success)',
  error: 'var(--error)',
  running: 'var(--accent)',
  warning: '#f59e0b',
};

// File color based purely on file existence on disk:
// - green: file exists and has content (line_count > 0)
// - red: file doesn't exist on disk (token type = expected but not created yet)
// - red: file exists but empty (line_count === 0) — structure created but no data collected
// - yellow: file exists but has very low content (line_count < 10)
// - green: file exists with content (line_count >= 10)
// In "nodes" colorMode: token = expected file not on disk = red
// In "commander" colorMode: file = content-based, token = expected but not on disk = red
function fileColor(node: TreeNodeData, _colorMode?: string): string {
  // Token type = expected file that may or may not exist on disk
  if (node.type === 'token') {
    return 'var(--error)'; // red — file doesn't exist on disk yet
  }
  // File type = actually on disk, color by content
  if (node.type === 'file') {
    if (node.line_count === undefined || node.line_count === null) {
      return 'var(--text-muted)'; // gray — unknown status
    }
    if (node.line_count === 0) return 'var(--error)'; // red — exists but empty (no data collected)
    if (node.line_count < 10) return '#f59e0b'; // yellow — low content
    return 'var(--success)'; // green — has content
  }
  return 'var(--text-muted)';
}

export default function NodeTree({
  onSelectNode,
  onSelectToken,
  onContextAction,
  onDoubleClickFile,
  onQueueStatusChange,
  projectId,
  selectedFileKey,
  activeExecFile,
  onCreateStructure,
  onDeleteStructure,
  context = 'commander',
  colorMode,
  onFileMove,
}: NodeTreeProps) {
  const [tree, setTree] = useState<TreeNodeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    node: TreeNodeData;
    parentNode?: TreeNodeData;
  } | null>(null);
  const [queueStatus, setQueueStatus] = useState<QueueStatusResponse | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const { activeLogRoot } = useActiveProject();

  // Fetch tree (now includes log_root + project_id to get project-scoped tree)
  const fetchTree = useCallback(async () => {
    if (!projectId) {
      setTree(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      // Use activeLogRoot from hook instead of reading localStorage directly
      const params: string[] = [];
      if (activeLogRoot) params.push(`log_root=${encodeURIComponent(activeLogRoot)}`);
      params.push(`project_id=${projectId}`);
      // Commander mode: hide missing files (only show what's on disk)
      if (context === 'commander') {
        params.push('hide_missing=true');
      }
      const queryStr = params.length > 0 ? `?${params.join('&')}` : '';
      const url = `/api/v1/nodesconfig/tree${queryStr}`;
      const res = await fetch(url);
      if (!res.ok) {
        const text = await res.text().catch(() => 'Unknown error');
        throw new Error(`HTTP ${res.status}: ${text}`);
      }
      const data = await res.json();
      setTree(data.tree);
      // Auto-expand root children
      if (data.tree?.children) {
        const ids = new Set<string>(data.tree.children.map((c: TreeNodeData) => c.name));
        // Also auto-expand sections within each node
        for (const child of data.tree.children) {
          if (child.children) {
            for (const sec of child.children) {
              ids.add(sec.name);
            }
          }
        }
        setExpandedNodes(ids);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load node tree');
    } finally {
      setLoading(false);
    }
  }, [projectId, context, activeLogRoot]);

  useEffect(() => {
    fetchTree();
  }, [fetchTree]);

  // Track previous queue state to detect transitions (e.g. running → done)
  const prevQueueStateRef = useRef<string | null>(null);

  // Poll queue status — always poll at 1s when queue has commands,
  // so color changes and pulse markers update in real time.
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;

    async function pollStatus() {
      try {
        const res = await fetch('/api/v1/commandqueue/status');
        if (!res.ok) return;
        const data: QueueStatusResponse = await res.json();
        setQueueStatus(data);
        onQueueStatusChange?.(data);

        // Detect transition to 'done' → reload tree to pick up new files
        const prevState = prevQueueStateRef.current;
        if (prevState === 'running' && data.state === 'done') {
          // Queue just finished — reload tree to show new file colors
          setTimeout(() => fetchTree(), 500);
        }
        // Also reload on transition from running → idle (cancel)
        if (prevState === 'running' && data.state === 'idle') {
          setTimeout(() => fetchTree(), 500);
        }
        prevQueueStateRef.current = data.state;
      } catch {
        // ignore
      }
    }

    // Always poll if there are commands in the queue or queue is active
    const hasActivity = queueStatus && (queueStatus.total > 0 || queueStatus.state === 'running' || queueStatus.state === 'paused');
    if (hasActivity) {
      interval = setInterval(pollStatus, 1000);
    }
    // Also do an initial poll on mount
    pollStatus();

    return () => {
      if (interval) clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queueStatus?.state, queueStatus?.total]);

  // Close context menu on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setContextMenu(null);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // ─── Tree expansion ───────────────────────────────────────────

  function toggleExpand(id: string) {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  // ─── Context menu (context-aware) ─────────────────────────────

  function handleContextMenu(e: React.MouseEvent, node: TreeNodeData, parentNode?: TreeNodeData) {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu({ x: e.clientX, y: e.clientY, node, parentNode });
  }

  function handleContextAction(action: string) {
    if (contextMenu) {
      onContextAction(action, contextMenu.node, contextMenu.parentNode);
      setContextMenu(null);
    }
  }

  // ─── Build context menu items based on node type ──────────────

  function getContextmenuItems(node: TreeNodeData, parentNode?: TreeNodeData) {
    // NODE type: station folder
    if (node.type === 'node') {
      // Nodes mode: folder structure creation commands + node management
      if (context === 'nodes') {
        return [
          { icon: <FolderPlus size={14} />, label: `Create New Folder under ${node.name}`, action: 'create_folder' },
          { icon: <FileText size={14} />, label: `Create New File under ${node.name}`, action: 'create_file' },
          { icon: <Edit3 size={14} />, label: `Rename Node "${node.name}"`, action: 'rename_node' },
          { icon: <Trash2 size={14} />, label: `Delete Node "${node.name}"`, action: 'delete_node' },
        ];
      }
      // Commander mode: print commands
      return [
        { icon: <Printer size={14} />, label: `Execute All Print Commands for ${node.name}`, action: 'print_all' },
        { icon: <Printer size={14} />, label: `Print All FBC Tokens for ${node.name}`, action: 'fbc_print_all' },
        { icon: <Printer size={14} />, label: `Print All RPC Tokens for ${node.name}`, action: 'rpc_print_all' },
        { icon: <Server size={14} />, label: `Print All LOG Tokens for ${node.name}`, action: 'bstool_errlog' },
      ];
    }

    // GROUP/SECTION type (FBC/RPC/LOG)
    if (node.type === 'group') {
      const sectionType = node.section_type || node.name;
      const nodeName = parentNode?.name || '';
      // Nodes mode: folder/file creation commands
      if (context === 'nodes') {
        return [
          { icon: <FileText size={14} />, label: `Create New File in ${sectionType}`, action: 'create_file_in_group' },
          { icon: <FolderPlus size={14} />, label: `Create New Subfolder`, action: 'create_folder' },
        ];
      }
      // Commander mode: print commands
      if (sectionType === 'LOG') {
        return [
          { icon: <Server size={14} />, label: `Print All LOG Tokens for ${nodeName}`, action: 'bstool_errlog' },
          { icon: <Trash2 size={14} />, label: `Clear All LOG Files for ${nodeName}`, action: 'clear_logs' },
        ];
      }
      return [
        { icon: <Printer size={14} />, label: `Print All ${sectionType} Tokens for ${nodeName}`, action: sectionType === 'FBC' ? 'fbc_print_all' : 'rpc_print_all' },
        { icon: <Trash2 size={14} />, label: `Clear All ${sectionType} Files for ${nodeName}`, action: 'clear_logs' },
      ];
    }

    // FILE type (actual .fbc/.rpc/.log file in the tree)
    if (node.type === 'file' || node.type === 'token') {
      const sectionType = node.section_type || '';
      const tokenId = node.token_id || '';

      // Nodes mode: file management only (no print commands)
      if (context === 'nodes') {
        const items = [
          { icon: <FileText size={14} />, label: 'Open File Content', action: 'open_file' },
          { icon: <Trash2 size={14} />, label: 'Delete File', action: 'delete_file' },
          { icon: <FolderPlus size={14} />, label: 'Create File Here', action: 'create_file' },
          { icon: <FolderOpen size={14} />, label: 'Move to Subfolder...', action: 'move_file' },
        ];
        // For tokens (not yet on disk), offer Create New File
        if (node.type === 'token') {
          items.push({ icon: <FileText size={14} />, label: 'Create New File', action: 'create_file' });
        }
        return items;
      }

      // Commander mode: print commands + erase
      const fileMgmtItems = [
        { icon: <FileText size={14} />, label: 'Open File Content', action: 'open_file' },
        { icon: <Trash2 size={14} />, label: 'Erase File Content', action: 'erase_file' },
      ];

      if (sectionType === 'FBC') {
        return [
          { icon: <Play size={14} />, label: `Print FieldBus Structure (Token ${tokenId})`, action: 'fbc_print' },
          { icon: <ScanLine size={14} />, label: `Scan FieldBus Structure (Token ${tokenId})`, action: 'fbc_scan' },
          ...fileMgmtItems,
        ];
      }
      if (sectionType === 'RPC') {
        return [
          { icon: <Play size={14} />, label: `Print Rupi counters Token '${tokenId}'`, action: 'rpc_print' },
          { icon: <Play size={14} />, label: `Clear Rupi counters '${tokenId}'`, action: 'rpc_clear' },
          { icon: <ScanLine size={14} />, label: `Scan FieldBus Structure (Token ${tokenId})`, action: 'rpc_scan' },
          ...fileMgmtItems,
        ];
      }
      if (sectionType === 'LOG') {
        return [
          { icon: <Server size={14} />, label: 'Run BsTool on this file', action: 'bstool_errlog' },
          ...fileMgmtItems,
        ];
      }
      if (sectionType === 'LIS') {
        // Parse exe number from filename (e.g. "AL01_192-168-1-171_102_exe3.lis" → 3)
        const exeMatch = node.name?.match(/exe(\d+)/i);
        const exeNum = exeMatch ? parseInt(exeMatch[1], 10) : 1;
        const channel = exeNum - 1; // Exe1→chn0, Exe2→chn1, etc.
        // RSU6 agent ID = tokenID << 16 (hw_addr << 16, 4 hex zeros appended)
        const rsuid = tokenId ? tokenId + '0000' : '';
        return [
          { icon: <Play size={14} />, label: `Print RSU Trace (rx+tx) Exe${exeNum}`, action: 'rsu_trace' },
          { icon: <Server size={14} />, label: `Print RSU Status Exe${exeNum}`, action: 'rsu_status' },
          ...fileMgmtItems,
        ];
      }
      return fileMgmtItems;
    }

    // NOTE: 'token' type is handled together with 'file' above.
    // 'node' and 'group' types are handled at the top with context checks.

    return [];
  }

  // ─── Render ────────────────────────────────────────────────────

  const menuItems = contextMenu ? getContextmenuItems(contextMenu.node, contextMenu.parentNode) : [];

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: 'var(--bg-secondary)',
      }}
    >
      {/* Toolbar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: '8px',
          borderBottom: '1px solid var(--border)',
          flexWrap: 'wrap',
        }}
      >
        <button
          className="btn btn-secondary"
          style={{ fontSize: '11px', padding: '4px 8px' }}
          onClick={fetchTree}
          title="Reload node tree from nodes.json + log files"
        >
          <RefreshCw size={11} style={{ display: 'inline', marginRight: '4px' }} />
          Refresh
        </button>
        {onCreateStructure && (
          <button
            className="btn btn-primary"
            style={{ fontSize: '11px', padding: '4px 8px' }}
            onClick={onCreateStructure}
            title="Create folder and file structure at log root"
          >
            <FolderPlus size={11} style={{ display: 'inline', marginRight: '4px' }} />
            Create Structure
          </button>
        )}
        {onDeleteStructure && (
          <button
            className="btn btn-danger"
            style={{ fontSize: '11px', padding: '4px 8px', marginLeft: '4px' }}
            onClick={() => {
              if (window.confirm('Delete the entire _LOG folder structure? This will remove all log files. Nodes.json will need to be re-imported.')) {
                onDeleteStructure();
              }
            }}
            title="Delete the _LOG folder structure so it can be recreated"
          >
            <Trash2 size={11} style={{ display: 'inline', marginRight: '4px' }} />
            Delete Structure
          </button>
        )}
      </div>





      {/* Tree body */}
      <div style={{ flex: 1, overflow: 'auto', padding: '4px 0' }}>
        {loading && (
          <div style={{ textAlign: 'center', padding: '24px' }}>
            <Loader2
              size={20}
              color="var(--accent)"
              style={{ animation: 'spin 1s linear infinite' }}
            />
            <p style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '8px' }}>
              Loading tree...
            </p>
          </div>
        )}

        {!loading && error && (
          <div style={{ padding: '16px', textAlign: 'center' }}>
            <p style={{ color: 'var(--error)', fontSize: '12px', marginBottom: '8px' }}>{error}</p>
            <button className="btn btn-secondary" style={{ fontSize: '11px' }} onClick={fetchTree}>
              Retry
            </button>
          </div>
        )}

        {!loading && !error && tree && (
          <div style={{ fontSize: '13px', fontFamily: 'var(--font-mono)' }}>
            {tree.children && tree.children.length > 0 ? (
              tree.children.map((child) => (
                <TreeBranch
                  key={child.name}
                  node={child}
                  depth={0}
                  expandedNodes={expandedNodes}
                  onToggle={toggleExpand}
                  onSelectNode={onSelectNode}
                  onSelectToken={onSelectToken}
                  onContextMenu={handleContextMenu}
                  onDoubleClickFile={onDoubleClickFile}
                  activeCommand={queueStatus?.commands?.[queueStatus.current] || null}
                  completedCommands={queueStatus?.commands ? new Set(queueStatus.commands.slice(0, queueStatus.current).map((c) => `${c.node_name}:${c.token_id}:${c.type}`)) : undefined}
                  selectedFileKey={selectedFileKey}
                  activeExecFile={activeExecFile}
                  colorMode={colorMode}
                  onFileMove={onFileMove}
                  onReloadTree={fetchTree}
                />
              ))
            ) : (
              <div
                style={{
                  padding: '16px',
                  textAlign: 'center',
                  color: 'var(--text-muted)',
                  fontSize: '12px',
                }}
              >
                {projectId ? (
                  <>
                    No nodes configured.
                    <br />
                    Load nodes from BU directory or scan via debugger.
                  </>
                ) : (
                  <>
                    Select a project to view nodes.
                    <br />
                    Create a project from the Dashboard.
                  </>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Context menu */}
      {contextMenu && menuItems.length > 0 && (
        <div
          ref={menuRef}
          style={{
            position: 'fixed',
            top: contextMenu.y,
            left: contextMenu.x,
            backgroundColor: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            borderRadius: '6px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            padding: '4px',
            zIndex: 1000,
            minWidth: '180px',
          }}
        >
          {menuItems.map((item, i) => (
            <ContextMenuItem
              key={i}
              icon={item.icon}
              label={item.label}
              onClick={() => handleContextAction(item.action)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── TreeBranch (recursive) ───────────────────────────────────────
interface TreeBranchProps {
  node: TreeNodeData;
  depth: number;
  expandedNodes: Set<string>;
  onToggle: (id: string) => void;
  onSelectNode: (node: TreeNodeData) => void;
  onSelectToken: (token: TreeNodeData) => void;
  onContextMenu: (e: React.MouseEvent, node: TreeNodeData, parentNode?: TreeNodeData) => void;
  onDoubleClickFile: (node: TreeNodeData) => void;
  parentNode?: TreeNodeData;
  activeCommand?: { node_name: string; token_id: string; type: string; status: string } | null;
  completedCommands?: Set<string>;
  selectedFileKey?: string | null;
  activeExecFile?: string | null;
  colorMode?: string;
  onFileMove?: (sourcePath: string, targetPath: string) => Promise<void>;
  onReloadTree?: () => void;
}

function TreeBranch({
  node,
  depth,
  expandedNodes,
  onToggle,
  onSelectNode,
  onSelectToken,
  onContextMenu,
  onDoubleClickFile,
  parentNode,
  activeCommand,
  completedCommands,
  selectedFileKey,
  activeExecFile,
  colorMode,
  onFileMove,
  onReloadTree,
}: TreeBranchProps) {
  const isExpanded = expandedNodes.has(node.name);
  const hasChildren = node.children && node.children.length > 0;
  const indent = depth * 16 + 8;

  const statusColor = STATUS_COLORS[node.status || 'idle'] || 'var(--text-muted)';

  function handleClick() {
    if (node.type === 'node') {
      onSelectNode(node);
      if (hasChildren) onToggle(node.name);
    } else if (node.type === 'group') {
      onToggle(node.name);
    } else if (node.type === 'token' || node.type === 'file') {
      onSelectToken(node);
    }
  }

  function handleDoubleClick() {
    if (node.type === 'file' || node.type === 'token') {
      onDoubleClickFile(node);
    } else if (node.type === 'node' && hasChildren) {
      onToggle(node.name);
    }
  }

  // Color for file nodes based on line count or command status
  let nodeColor = (node.type === 'file' || node.type === 'token') ? fileColor(node, colorMode) : statusColor;
  let isActive = false;
  let isSelected = false;

  // Check if this file/token matches the selected file (bidirectional highlight)
  if (selectedFileKey && (node.type === 'file' || node.type === 'token')) {
    const stationName = parentNode?.name || '';
    const sectionType = node.section_type || parentNode?.section_type || '';
    const fileName = node.file_name || node.name;
    const fileKey = `${stationName}:${sectionType}:${fileName}`;
    if (fileKey === selectedFileKey) {
      isSelected = true;
    }
  }
  // Also highlight node-level if selectedFileKey station matches
  if (selectedFileKey && node.type === 'node') {
    const station = selectedFileKey.split(':')[0];
    if (node.name === station) {
      isSelected = true;
    }
  }

  // Check if this file/token matches the active command (from queue or single exec)
  if (node.type === 'file' || node.type === 'token') {
    // Queue-based execution check
    if (activeCommand) {
      const cmdKey = `${activeCommand.node_name}:${activeCommand.token_id}:${activeCommand.type}`;
      const stationMatch = parentNode?.name === activeCommand.node_name ||
        parentNode?.name?.startsWith(activeCommand.node_name) ||
        activeCommand.node_name.startsWith(parentNode?.name || '');
      const nodeMatch = node.token_id === activeCommand.token_id && stationMatch;
      if (nodeMatch) {
        nodeColor = CMD_STATUS_COLORS[activeCommand.status] || 'var(--accent)';
        if (activeCommand.status === 'running') {
          isActive = true;
        }
      }
      if (completedCommands && completedCommands.has(cmdKey)) {
        if (nodeMatch) {
          nodeColor = 'var(--success)';
        }
      }
    }
    // Single-command execution check (from CommanderLayout)
    if (activeExecFile) {
      const execKey = `${parentNode?.name || ''}:${node.token_id}:${node.section_type?.toLowerCase() || ''}`;
      const fbcKey = `${parentNode?.name || ''}:${node.token_id}:fbc`;
      const rpcKey = `${parentNode?.name || ''}:${node.token_id}:rpc`;
      if (activeExecFile === execKey || activeExecFile === fbcKey || activeExecFile === rpcKey) {
        isActive = true;
        nodeColor = 'var(--accent)';
      }
    }
  }

  // Pulsing marker for actively executing file
  const showPulse = isActive;

  // Drag-and-drop: file nodes are draggable, group/node folders are drop targets
  const isDraggable = !!(node.type === 'file' || node.type === 'token') && !!node.file_path && !!onFileMove;
  const isDropTarget = (node.type === 'group' || node.type === 'node') && !!onFileMove;

  function handleDragStart(e: React.DragEvent) {
    if (isDraggable && node.file_path) {
      e.dataTransfer.setData('text/plain', node.file_path);
      e.dataTransfer.effectAllowed = 'move';
    }
  }

  function handleDragOver(e: React.DragEvent) {
    if (isDropTarget) {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      (e.currentTarget as HTMLElement).style.backgroundColor = 'rgba(245,166,35,0.15)';
    }
  }

  function handleDragLeave(e: React.DragEvent) {
    if (isDropTarget) {
      (e.currentTarget as HTMLElement).style.backgroundColor = isSelected ? 'rgba(99,102,241,0.15)' : 'transparent';
    }
  }

  async function handleDrop(e: React.DragEvent) {
    if (isDropTarget) {
      e.preventDefault();
      e.stopPropagation();
      (e.currentTarget as HTMLElement).style.backgroundColor = isSelected ? 'rgba(99,102,241,0.15)' : 'transparent';
      const sourcePath = e.dataTransfer.getData('text/plain');
      if (!sourcePath || !onFileMove) return;
      // Build target path: drop on group → move to that subfolder, drop on node → move to station root
      let targetPath = '';
      if (node.type === 'group') {
        // Group = FBC/RPC/LOG subfolder — move file into this subfolder
        const station = parentNode?.name || '';
        const subfolder = node.section_type || node.name || '';
        const fileName = sourcePath.split('/').pop()?.split('\\').pop() || '';
        if (station && subfolder && fileName) {
          // Build path using the same log root from source path
          const sourceParts = sourcePath.replace(/\\/g, '/').split('/');
          // source: logRoot/station/oldSubfolder/file → target: logRoot/station/newSubfolder/file
          const logRoot = sourceParts.slice(0, -3).join('/');
          targetPath = logRoot + '/' + station + '/' + subfolder.toLowerCase() + '/' + fileName;
        }
      } else if (node.type === 'node') {
        // Node = station folder — move file into station root (keep subfolder)
        const station = node.name;
        const sourceParts = sourcePath.replace(/\\/g, '/').split('/');
        const fileName = sourceParts.pop() || '';
        const oldSubfolder = sourceParts.pop() || '';
        const logRoot = sourceParts.slice(0, -1).join('/');
        if (station && oldSubfolder && fileName) {
          targetPath = logRoot + '/' + station + '/' + oldSubfolder + '/' + fileName;
        }
      }
      if (targetPath && targetPath !== sourcePath) {
        try {
          await onFileMove(sourcePath, targetPath);
          onReloadTree?.();
        } catch (err) {
          console.error('drag-drop move failed:', err);
        }
      }
    }
  }

  return (
    <div>
      <div
        onClick={handleClick}
        onDoubleClick={handleDoubleClick}
        onContextMenu={(e) => onContextMenu(e, node, parentNode)}
        draggable={isDraggable}
        onDragStart={isDraggable ? handleDragStart : undefined}
        onDragOver={isDropTarget ? handleDragOver : undefined}
        onDragLeave={isDropTarget ? handleDragLeave : undefined}
        onDrop={isDropTarget ? handleDrop : undefined}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: '3px 8px 3px ' + indent + 'px',
          cursor: isDraggable ? 'grab' : 'pointer',
          borderRadius: '4px',
          transition: 'background-color 0.1s ease',
          backgroundColor: isSelected ? 'rgba(99,102,241,0.15)' : isActive ? 'rgba(99,102,241,0.12)' : 'transparent',
          fontWeight: isActive || isSelected ? 600 : undefined,
          borderLeft: isSelected ? '3px solid var(--accent)' : '3px solid transparent',
        }}
        onMouseEnter={(e) => {
          if (!isSelected && !isActive) (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-elevated)';
        }}
        onMouseLeave={(e) => {
          if (!isSelected && !isActive) (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
        }}
      >
        {/* Expand icon */}
        {hasChildren ? (
          isExpanded ? (
            <ChevronDown size={14} color="var(--text-muted)" style={{ flexShrink: 0 }} />
          ) : (
            <ChevronRight size={14} color="var(--text-muted)" style={{ flexShrink: 0 }} />
          )
        ) : (
          <span style={{ width: 14, flexShrink: 0 }} />
        )}

        {/* Node icon by type */}
        {node.type === 'node' && <Server size={14} color="var(--accent)" style={{ flexShrink: 0 }} />}
        {node.type === 'group' && (
          isExpanded ? (
            <FolderOpen size={14} color="var(--text-secondary)" style={{ flexShrink: 0 }} />
          ) : (
            <Folder size={14} color="var(--text-secondary)" style={{ flexShrink: 0 }} />
          )
        )}
        {node.type === 'token' && (
          <>
            <Circle
              size={8}
              fill={nodeColor}
              color={nodeColor}
              style={{ flexShrink: 0, marginLeft: '3px' }}
            />
            {showPulse && (
              <span
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--accent)',
                  flexShrink: 0,
                  marginLeft: '2px',
                  animation: 'pulse 1s ease-in-out infinite',
                  boxShadow: '0 0 4px var(--accent)',
                }}
              />
            )}
          </>
        )}
        {node.type === 'file' && (
          <FileText
            size={12}
            color={nodeColor}
            style={{ flexShrink: 0, marginLeft: '1px' }}
          />
        )}

        {/* Pulsing marker for actively executing file */}
        {showPulse && (
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: 'var(--accent)',
              flexShrink: 0,
              marginLeft: '2px',
              animation: 'pulse 1s ease-in-out infinite',
              boxShadow: '0 0 4px var(--accent)',
            }}
          />
        )}

        {/* Name */}
        <span
          style={{
            fontSize: '12px',
            fontWeight: node.type === 'node' ? 600 : 400,
            color: node.type === 'node' ? 'var(--text-primary)' : (node.type === 'file' || node.type === 'token') ? nodeColor : 'var(--text-secondary)',
          }}
        >
          {node.name}
        </span>

        {/* Extra info */}
        {node.ip && (
          <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: '4px' }}>
            ({node.ip})
          </span>
        )}
        {node.type === 'file' && node.line_count !== undefined && (
          <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: '4px' }}>
            [{node.line_count}L]
          </span>
        )}
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div>
          {node.children!.map((child) => (
            <TreeBranch
              key={child.name + depth}
              node={child}
              depth={depth + 1}
              expandedNodes={expandedNodes}
              onToggle={onToggle}
              onSelectNode={onSelectNode}
              onSelectToken={onSelectToken}
              onContextMenu={onContextMenu}
              onDoubleClickFile={onDoubleClickFile}
              parentNode={node}
              activeCommand={activeCommand}
              completedCommands={completedCommands}
              selectedFileKey={selectedFileKey}
              activeExecFile={activeExecFile}
              colorMode={colorMode}
              onFileMove={onFileMove}
              onReloadTree={onReloadTree}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── ContextMenuItem ───────────────────────────────────────────────

function ContextMenuItem({
  icon,
  label,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '6px 10px',
        cursor: 'pointer',
        borderRadius: '4px',
        fontSize: '12px',
        color: 'var(--text-primary)',
        transition: 'background-color 0.1s ease',
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-secondary)';
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
      }}
    >
      {icon}
      {label}
    </div>
  );
}