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
} from 'lucide-react';
import type { TreeNodeData, QueueStatusResponse } from '../types/api';

export interface NodeTreeProps {
  onSelectNode: (node: TreeNodeData) => void;
  onSelectToken: (token: TreeNodeData) => void;
  onContextAction: (action: string, node: TreeNodeData) => void;
  onDoubleClickFile: (node: TreeNodeData) => void;
  onQueueStatusChange?: (status: QueueStatusResponse | null) => void;
  projectId?: number | null;
  selectedFileKey?: string | null; // "stationName:sectionType:fileName" for bidirectional highlight
  onCreateStructure?: () => void; // callback to create log folder structure
  context?: 'nodes' | 'commander'; // controls which menu items are available
}

// Command status colors for file nodes during queue execution
const CMD_STATUS_COLORS: Record<string, string> = {
  pending: 'var(--text-muted)',
  running: 'var(--accent)',
  completed: 'var(--success)',
  done: 'var(--success)',
  failed: 'var(--error)',
  error: 'var(--error)',
};

const STATUS_COLORS: Record<string, string> = {
  idle: 'var(--text-muted)',
  connected: 'var(--success)',
  error: 'var(--error)',
  running: 'var(--accent)',
  warning: '#f59e0b',
};

// File color by line count: red (empty), yellow (<10), green (>=10)
// Also checks status field from backend (error=red, warning=yellow, idle=green)
function fileColor(node: TreeNodeData): string {
  if (node.line_count === 0 || node.status === 'error') return 'var(--error)';
  if (node.line_count && node.line_count < 10 || node.status === 'warning') return '#f59e0b';
  if (node.line_count && node.line_count >= 10 || node.status === 'idle') return 'var(--success)';
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
  onCreateStructure,
  context = 'commander',
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
      const logRoot = localStorage.getItem('logRoot') || '';
      const params: string[] = [];
      if (logRoot) params.push(`log_root=${encodeURIComponent(logRoot)}`);
      params.push(`project_id=${projectId}`);
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
  }, [projectId]);

  useEffect(() => {
    fetchTree();
  }, [fetchTree]);

  // Poll queue status
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;

    async function pollStatus() {
      try {
        const res = await fetch('/api/v1/commandqueue/status');
        if (!res.ok) return;
        const data: QueueStatusResponse = await res.json();
        setQueueStatus(data);
        onQueueStatusChange?.(data);
      } catch {
        // ignore
      }
    }

    if (queueStatus && (queueStatus.state === 'running' || queueStatus.state === 'paused')) {
      interval = setInterval(pollStatus, 1000);
    } else {
      pollStatus();
    }

    return () => {
      if (interval) clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queueStatus?.state]);

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
      onContextAction(action, contextMenu.node);
      setContextMenu(null);
    }
  }

  // ─── Build context menu items based on node type ──────────────

  function getContextmenuItems(node: TreeNodeData, parentNode?: TreeNodeData) {
    // NODE type: "Execute All Print Commands for {node}"
    if (node.type === 'node') {
      return [
        { icon: <Printer size={14} />, label: `Execute All Print Commands for ${node.name}`, action: 'print_all' },
        { icon: <Printer size={14} />, label: `Print All FBC Tokens for ${node.name}`, action: 'fbc_print_all' },
        { icon: <Printer size={14} />, label: `Print All RPC Tokens for ${node.name}`, action: 'rpc_print_all' },
        { icon: <Server size={14} />, label: `Print All LOG Tokens for ${node.name}`, action: 'bstool_errlog' },
      ];
    }

    // GROUP/SECTION type (FBC/RPC/LOG): different actions per section
    if (node.type === 'group') {
      const sectionType = node.section_type || node.name;
      const nodeName = parentNode?.name || '';
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

      // Commander: "Erase File Content" (empty the file, keep it)
      // Nodes: "Delete File" (remove from disk entirely)
      const fileActionItem = context === 'nodes'
        ? { icon: <Trash2 size={14} />, label: 'Delete File', action: 'delete_file' }
        : { icon: <Trash2 size={14} />, label: 'Erase File Content', action: 'erase_file' };

      if (sectionType === 'FBC') {
        return [
          { icon: <Play size={14} />, label: `Print FieldBus Structure (Token ${tokenId})`, action: 'fbc_print' },
          { icon: <ScanLine size={14} />, label: `Scan FieldBus Structure (Token ${tokenId})`, action: 'fbc_scan' },
          { icon: <FileText size={14} />, label: 'Open File Content', action: 'open_file' },
          fileActionItem,
        ];
      }
      if (sectionType === 'RPC') {
        return [
          { icon: <Play size={14} />, label: `Print Rupi counters Token '${tokenId}'`, action: 'rpc_print' },
          { icon: <Play size={14} />, label: `Clear Rupi counters '${tokenId}'`, action: 'rpc_clear' },
          { icon: <ScanLine size={14} />, label: `Scan FieldBus Structure (Token ${tokenId})`, action: 'rpc_scan' },
          { icon: <FileText size={14} />, label: 'Open File Content', action: 'open_file' },
          fileActionItem,
        ];
      }
      if (sectionType === 'LOG') {
        return [
          { icon: <Server size={14} />, label: 'Run BsTool on this file', action: 'bstool_errlog' },
          { icon: <FileText size={14} />, label: 'Open File Content', action: 'open_file' },
          fileActionItem,
        ];
      }
      // LIS or unknown
      return [
        { icon: <FileText size={14} />, label: 'Open File Content', action: 'open_file' },
        fileActionItem,
      ];
    }

    // NOTE: 'token' type is handled together with 'file' above (line 229).
    // The standalone token block that was here was unreachable dead code — removed.

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
  completedCommands?: Set<string>; // Set of "node_name:token_id:type" for completed commands
  selectedFileKey?: string | null; // "stationName:sectionType:fileName" for bidirectional highlight
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
  let nodeColor = (node.type === 'file' || node.type === 'token') ? fileColor(node) : statusColor;
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

  // Check if this file/token matches the active command
  if (activeCommand && (node.type === 'file' || node.type === 'token')) {
    const cmdKey = `${activeCommand.node_name}:${activeCommand.token_id}:${activeCommand.type}`;
    const nodeMatch = node.token_id === activeCommand.token_id && parentNode?.name?.includes(activeCommand.node_name);
    if (nodeMatch) {
      nodeColor = CMD_STATUS_COLORS[activeCommand.status] || 'var(--accent)';
      if (activeCommand.status === 'running') {
        isActive = true;
      }
    }
    // Check completed commands
    if (completedCommands && completedCommands.has(cmdKey)) {
      if (nodeMatch) {
        nodeColor = 'var(--success)';
      }
    }
  }

  return (
    <div>
      <div
        onClick={handleClick}
        onDoubleClick={handleDoubleClick}
        onContextMenu={(e) => onContextMenu(e, node, parentNode)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: '3px 8px 3px ' + indent + 'px',
          cursor: 'pointer',
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
          <Circle
            size={8}
            fill={nodeColor}
            color={nodeColor}
            style={{ flexShrink: 0, marginLeft: '3px' }}
          />
        )}
        {node.type === 'file' && (
          <FileText
            size={12}
            color={nodeColor}
            style={{ flexShrink: 0, marginLeft: '1px' }}
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