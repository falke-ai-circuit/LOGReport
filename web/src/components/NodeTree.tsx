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
  RotateCcw,
  Search,
} from 'lucide-react';
import type { TreeNodeData, QueueStatusResponse } from '../types/api';
import { useActiveProject } from '../hooks/useActiveProject';

export interface NodeTreeProps {
  onSelectNode: (node: TreeNodeData) => void;
  onSelectToken: (token: TreeNodeData) => void;
  onContextAction: (action: string, node: TreeNodeData, parentNode?: TreeNodeData) => void;
  onBatchContextAction?: (action: string, nodes: TreeNodeData[]) => void;
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
  reloadKey?: number;
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

// File color based on file content (line count):
// - grey: file empty (0 lines) — no command executed yet, or command produced nothing
// - orange: file has content but too few lines — command executed but content is erroneous/insufficient
// - green: file has content with enough lines — command executed and content is correct
// Minimum line threshold: 3 lines (header takes 2-3 lines, so real content = 3+)
// Token type (not on disk) = grey — expected but not yet created
const MIN_CONTENT_LINES = 3;

function fileColor(node: TreeNodeData, _colorMode?: string): string {
  // Token type = expected file that doesn't exist on disk yet
  if (node.type === 'token') {
    return 'var(--text-muted)'; // grey — expected but not yet created
  }
  // File type = actually on disk, color by content
  if (node.type === 'file') {
    if (node.line_count === undefined || node.line_count === null) {
      return 'var(--text-muted)'; // grey — unknown status
    }
    if (node.line_count === 0) return 'var(--text-muted)'; // grey — empty, no command executed
    if (node.line_count < MIN_CONTENT_LINES) return '#f97316'; // orange — content too short (erroneous)
    return 'var(--success)'; // green — command executed, content is correct
  }
  return 'var(--text-muted)';
}

function filterTreeNodes(nodes: TreeNodeData[], filter: string): TreeNodeData[] {
  if (!filter) return nodes;
  const lower = filter.toLowerCase();
  return nodes.filter(node => {
    if (node.name.toLowerCase().includes(lower)) return true;
    if (node.children) {
      const filteredChildren = filterTreeNodes(node.children, filter);
      if (filteredChildren.length > 0) return true;
    }
    return false;
  });
}

export default function NodeTree({
  onSelectNode,
  onSelectToken,
  onContextAction,
  onBatchContextAction,
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
  reloadKey,
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
    isBatch?: boolean;
    batchNodes?: TreeNodeData[];
  } | null>(null);
  const [queueStatus, setQueueStatus] = useState<QueueStatusResponse | null>(null);
  const [lisMode, setLisMode] = useState<string>('rsu');
  const [filterText, setFilterText] = useState('');
  const [selectedNodes, setSelectedNodes] = useState<Set<string>>(new Set());
  const menuRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const expandedNodesRef = useRef<Set<string>>(new Set());
  const treeRef = useRef<TreeNodeData | null>(null);
  const hasAutoExpandedRef = useRef<boolean>(false);
  const selectedNodesRef = useRef<Set<string>>(new Set());
  const { activeLogRoot } = useActiveProject();

  // Fetch lis_mode from settings for context menu adaptation
  useEffect(() => {
    fetch('/api/v1/settings')
      .then(res => res.ok ? res.json() : null)
      .then(data => { if (data?.settings?.lis_mode) setLisMode(data.settings.lis_mode); })
      .catch(() => {});
  }, []);

  // Fetch tree (now includes log_root + project_id to get project-scoped tree)
  const fetchTree = useCallback(async () => {
    if (!projectId) {
      setTree(null);
      treeRef.current = null;
      setLoading(false);
      return;
    }
    // Save scroll position before re-fetching tree
    const savedScroll = scrollRef.current?.scrollTop ?? 0;
    // Only show loading spinner on first load (treeRef.current === null), not on subsequent refreshes
    if (treeRef.current === null) setLoading(true);
    setError(null);
    try {
      // Use activeLogRoot from hook instead of reading localStorage directly
      const params: string[] = [];
      if (activeLogRoot) params.push(`log_root=${encodeURIComponent(activeLogRoot)}`);
      params.push(`project_id=${projectId}`);
      // Commander mode: show all nodes (files on disk + expected token placeholders).
      // Backend hardcodes hideMissing=false — sending the param is harmless but unnecessary.
      // if (context === 'commander') {
      //   params.push('hide_missing=true');
      // }
      const queryStr = params.length > 0 ? `?${params.join('&')}` : '';
      const url = `/api/v1/nodesconfig/tree${queryStr}`;
      const res = await fetch(url);
      if (!res.ok) {
        const text = await res.text().catch(() => 'Unknown error');
        throw new Error(`HTTP ${res.status}: ${text}`);
      }
      const data = await res.json();
      setTree(data.tree);
      treeRef.current = data.tree;
      // Auto-expand root children ONLY on first load (hasAutoExpandedRef.current === false)
      // Don't reset expansion state on subsequent fetches (prevents scroll jump)
      if (data.tree?.children && !hasAutoExpandedRef.current) {
        const ids = new Set<string>(data.tree.children.map((c: TreeNodeData) => c.name));
        // Also auto-expand sections within each node
        for (const child of data.tree.children) {
          if (child.children) {
            for (const sec of child.children) {
              ids.add(sec.name);
            }
          }
        }
        expandedNodesRef.current = ids;
        setExpandedNodes(ids);
        hasAutoExpandedRef.current = true;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load node tree');
    } finally {
      setLoading(false);
      // Restore scroll position after tree update
      requestAnimationFrame(() => {
        if (scrollRef.current && savedScroll > 0) {
          scrollRef.current.scrollTop = savedScroll;
        }
      });
    }
  }, [projectId, context, activeLogRoot]);

  useEffect(() => {
    fetchTree();
  }, [fetchTree]);

  // Reload tree when reloadKey prop changes (replaces key remount)
  const prevReloadKeyRef = useRef<number | undefined>(undefined);
  useEffect(() => {
    if (prevReloadKeyRef.current !== undefined && reloadKey !== prevReloadKeyRef.current) {
      fetchTree();
    }
    prevReloadKeyRef.current = reloadKey;
  }, [reloadKey, fetchTree]);

  // Track previous queue state to detect transitions (e.g. running → done)
  const prevQueueStateRef = useRef<string | null>(null);
  const prevCurrentRef = useRef<number>(-1);

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
        // NOTE: Removed per-command reload during execution to prevent scroll stutter.
        // Tree now only refreshes when the entire queue finishes, not after each individual command.
        prevQueueStateRef.current = data.state;
        prevCurrentRef.current = data.current;
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
      expandedNodesRef.current = next;
      return next;
    });
  }

  // ─── Context menu (context-aware) ─────────────────────────────

  const handleSelectToggle = useCallback((node: TreeNodeData) => {
    setSelectedNodes(prev => {
      const next = new Set(prev);
      if (next.has(node.name)) {
        next.delete(node.name);
      } else {
        next.add(node.name);
      }
      selectedNodesRef.current = next;
      return next;
    });
  }, []);

  const handleClearSelection = useCallback(() => {
    setSelectedNodes(new Set());
    selectedNodesRef.current = new Set();
  }, []);

  function collectSelectedNodes(root: TreeNodeData | null): TreeNodeData[] {
    if (!root) return [];
    const result: TreeNodeData[] = [];
    function traverse(node: TreeNodeData) {
      if (selectedNodesRef.current.has(node.name)) {
        result.push(node);
      }
      if (node.children) {
        for (const child of node.children) {
          traverse(child);
        }
      }
    }
    if (root.children) {
      for (const child of root.children) {
        traverse(child);
      }
    }
    return result;
  }

  function handleContextMenu(e: React.MouseEvent, node: TreeNodeData, parentNode?: TreeNodeData) {
    e.preventDefault();
    e.stopPropagation();
    if (selectedNodesRef.current.has(node.name) && selectedNodesRef.current.size > 1) {
      const selectedData = collectSelectedNodes(tree);
      setContextMenu({ x: e.clientX, y: e.clientY, node, parentNode, isBatch: true, batchNodes: selectedData });
    } else {
      setContextMenu({ x: e.clientX, y: e.clientY, node, parentNode });
    }
  }

  function handleContextAction(action: string) {
    if (contextMenu) {
      if (contextMenu.isBatch && contextMenu.batchNodes) {
        onBatchContextAction?.(action, contextMenu.batchNodes);
      } else {
        onContextAction(action, contextMenu.node, contextMenu.parentNode);
      }
      setContextMenu(null);
    }
  }

  // ─── Build context menu items based on node type ──────────────

  function getBatchMenuItems() {
    const count = selectedNodesRef.current.size;
    return [
      { icon: <Printer size={14} />, label: `Queue FBC Print for ${count} selected`, action: 'batch_fbc_print' },
      { icon: <Printer size={14} />, label: `Queue RPC Print for ${count} selected`, action: 'batch_rpc_print' },
      { icon: <Server size={14} />, label: `Queue BsTool ErrLog for ${count} selected`, action: 'batch_bstool_errlog' },
    ];
  }

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
      const lisNodeLabel = lisMode === 'diaglis'
        ? `Import All DiagLis Files for ${node.name}`
        : lisMode === 'lisdiag'
        ? `Run All LisDiag Commands for ${node.name}`
        : `Print All RSU Traces for ${node.name}`;
      return [
        { icon: <Printer size={14} />, label: `Execute All Print Commands for ${node.name}`, action: 'print_all' },
        { icon: <Printer size={14} />, label: `Print All FBC Tokens for ${node.name}`, action: 'fbc_print_all' },
        { icon: <Printer size={14} />, label: `Print All RPC Tokens for ${node.name}`, action: 'rpc_print_all' },
        { icon: <Printer size={14} />, label: lisNodeLabel, action: 'lis_print_all' },
        { icon: <Server size={14} />, label: `Print All LOG Tokens for ${node.name}`, action: 'bstool_errlog' },
        { icon: <RotateCcw size={14} />, label: `Restart Queue`, action: 'queue_restart' },
        { icon: <Trash2 size={14} />, label: `Clear Queue`, action: 'queue_clear' },
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
      if (sectionType === 'LIS' || sectionType === 'RSU' || sectionType === 'DIA') {
        const lisGroupLabel = lisMode === 'diaglis'
          ? `Import All DiagLis Files for ${nodeName}`
          : lisMode === 'lisdiag'
          ? `Run All LisDiag Commands for ${nodeName}`
          : `Print All RSU Traces for ${nodeName}`;
        return [
          { icon: <Printer size={14} />, label: lisGroupLabel, action: 'lis_print_all' },
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
      if (sectionType === 'LIS' || sectionType === 'RSU' || sectionType === 'DIA') {
        // Parse exe number from filename (e.g. "AL01_192-168-1-171_102_exe3.lis" → 3)
        const exeMatch = node.name?.match(/exe(\d+)/i);
        const exeNum = exeMatch ? parseInt(exeMatch[1], 10) : 1;
        const tokenId = node.token_id?.split('_exe')[0] || '';
        if (lisMode === 'diaglis') {
          return [
            { icon: <FileText size={14} />, label: `Import DiagLis ${tokenId} exe${exeNum}`, action: 'diaglis_import' },
            ...fileMgmtItems,
          ];
        }
        if (lisMode === 'lisdiag') {
          return [
            { icon: <Play size={14} />, label: `Run LisDiag ${tokenId} exe${exeNum}`, action: 'lisdiag_run' },
            ...fileMgmtItems,
          ];
        }
        // rsu mode (default)
        return [
          { icon: <Printer size={14} />, label: `Print All RSU Traces for this node`, action: 'lis_print_all' },
          { icon: <Play size={14} />, label: `Print RSU Trace (rx+tx) ${tokenId} Exe${exeNum}`, action: 'rsu_trace' },
          { icon: <Server size={14} />, label: `Print RSU Status ${tokenId} Exe${exeNum}`, action: 'rsu_status' },
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

  const menuItems = contextMenu ? (contextMenu.isBatch ? getBatchMenuItems() : getContextmenuItems(contextMenu.node, contextMenu.parentNode)) : [];

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
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Search size={12} color="var(--text-muted)" />
          <input
            type="text"
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            placeholder="Filter..."
            style={{
              fontSize: '11px',
              padding: '4px 8px',
              width: '120px',
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border)',
              borderRadius: '4px',
              color: 'var(--text-primary)',
            }}
          />
        </div>
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
      <div ref={scrollRef} style={{ flex: 1, overflow: 'auto', padding: '4px 0' }}>
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
              filterTreeNodes(tree.children, filterText).map((child) => (
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
                  selectedNodes={selectedNodes}
                  onSelectToggle={handleSelectToggle}
                  onClearSelection={handleClearSelection}
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
  selectedNodes?: Set<string>;
  onSelectToggle?: (node: TreeNodeData) => void;
  onClearSelection?: () => void;
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
  selectedNodes,
  onSelectToggle,
  onClearSelection,
}: TreeBranchProps) {
  const isExpanded = expandedNodes.has(node.name);
  const hasChildren = node.children && node.children.length > 0;
  const indent = depth * 16 + 8;

  const statusColor = STATUS_COLORS[node.status || 'idle'] || 'var(--text-muted)';
  const isMultiSelected = !!(selectedNodes?.has(node.name) && (node.type === 'file' || node.type === 'token'));

  function handleClick(e: React.MouseEvent) {
    // Ctrl/Cmd+click = toggle multi-select on file/token nodes
    if ((e.ctrlKey || e.metaKey) && (node.type === 'file' || node.type === 'token')) {
      e.preventDefault();
      e.stopPropagation();
      onSelectToggle?.(node);
      return;
    }
    // Plain click on file/token clears multi-selection
    if (!e.ctrlKey && !e.metaKey && !e.shiftKey && (node.type === 'file' || node.type === 'token')) {
      if (selectedNodes && selectedNodes.size > 0) {
        onClearSelection?.();
      }
    }
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
    // Build the command key for this specific file/token node
    const stationMatch = (cmd: { node_name: string; token_id: string; type: string }) => {
      return parentNode?.name === cmd.node_name ||
        parentNode?.name?.startsWith(cmd.node_name) ||
        cmd.node_name.startsWith(parentNode?.name || '');
    };

    // Check if this file matches any completed command → green
    if (completedCommands) {
      // Build possible command keys for this file/token
      // Queue stores type as "fbc", "rpc", "bstool" — map bstool → log section
      const sectionLower = node.section_type?.toLowerCase() || '';
      const possibleTypes = sectionLower === 'log' ? ['bstool', 'log'] : [sectionLower];
      // Try matching with parentNode name (station) and also check if any
      // completed command has a node_name that starts with or matches the station
      const parentName = parentNode?.name || '';
      for (const ptype of possibleTypes) {
        const fileCmdKey = `${parentName}:${node.token_id}:${ptype}`;
        if (completedCommands.has(fileCmdKey)) {
          nodeColor = 'var(--success)';
        }
      }
      // Also try prefix matching — queue node_name might be "AP01_m2" while
      // tree station is "AP01m" (extractStationName strips suffix differently)
      if (nodeColor !== 'var(--success)') {
        completedCommands.forEach((key: string) => {
          const parts = key.split(':');
          if (parts.length >= 3 && parts[1] === node.token_id && parts[2] === possibleTypes[0]) {
            const cmdNodeName = parts[0];
            if (parentName === cmdNodeName ||
                parentName.startsWith(cmdNodeName) ||
                cmdNodeName.startsWith(parentName)) {
              nodeColor = 'var(--success)';
            }
          }
        });
      }
    }

    // Queue-based execution check — override with active command status
    if (activeCommand) {
      const nodeMatch = node.token_id === activeCommand.token_id && stationMatch(activeCommand);
      if (nodeMatch) {
        nodeColor = CMD_STATUS_COLORS[activeCommand.status] || 'var(--accent)';
        if (activeCommand.status === 'running') {
          isActive = true;
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
          backgroundColor: isMultiSelected ? 'rgba(99,102,241,0.20)' : isSelected ? 'rgba(99,102,241,0.15)' : isActive ? 'rgba(99,102,241,0.12)' : 'transparent',
          fontWeight: isActive || isSelected || isMultiSelected ? 600 : undefined,
          borderLeft: isSelected || isMultiSelected ? '3px solid var(--accent)' : '3px solid transparent',
        }}
        onMouseEnter={(e) => {
          if (!isSelected && !isActive && !isMultiSelected) (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-elevated)';
        }}
        onMouseLeave={(e) => {
          if (!isSelected && !isActive && !isMultiSelected) (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
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
                  backgroundColor: '#008a00',
                  flexShrink: 0,
                  marginLeft: '2px',
                  animation: 'pulse 1s ease-in-out infinite',
                  boxShadow: '0 0 6px #008a00',
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
              backgroundColor: '#008a00',
              flexShrink: 0,
              marginLeft: '2px',
              animation: 'pulse 1s ease-in-out infinite',
              boxShadow: '0 0 6px #008a00',
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

        {/* Extra info — only show IP on station-level nodes, not on files */}
        {node.ip && node.type === 'node' && (
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
              selectedNodes={selectedNodes}
              onSelectToggle={onSelectToggle}
              onClearSelection={onClearSelection}
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