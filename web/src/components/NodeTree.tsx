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
} from 'lucide-react';
import type { TreeNodeData, QueueStatusResponse } from '../types/api';

export interface NodeTreeProps {
  onSelectNode: (node: TreeNodeData) => void;
  onSelectToken: (token: TreeNodeData) => void;
  onContextAction: (action: string, token: TreeNodeData) => void;
  onQueueStatusChange?: (status: QueueStatusResponse | null) => void;
}

const STATUS_COLORS: Record<string, string> = {
  idle: 'var(--text-muted)',
  connected: 'var(--success)',
  error: 'var(--error)',
  running: 'var(--accent)',
  warning: '#f59e0b',
};

export default function NodeTree({
  onSelectNode,
  onSelectToken,
  onContextAction,
  onQueueStatusChange,
}: NodeTreeProps) {
  const [tree, setTree] = useState<TreeNodeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    node: TreeNodeData;
  } | null>(null);
  const [queueStatus, setQueueStatus] = useState<QueueStatusResponse | null>(null);
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchError, setBatchError] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // Fetch tree
  const fetchTree = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/nodesconfig/tree');
      if (!res.ok) {
        const text = await res.text().catch(() => 'Unknown error');
        throw new Error(`HTTP ${res.status}: ${text}`);
      }
      const data = await res.json();
      setTree(data.tree);
      // Auto-expand root children
      if (data.tree?.children) {
        const ids = new Set<string>(data.tree.children.map((c: TreeNodeData) => c.name));
        setExpandedNodes(ids);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load node tree');
    } finally {
      setLoading(false);
    }
  }, []);

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

    // Poll every 1s when queue is active
    if (queueStatus && (queueStatus.state === 'running' || queueStatus.state === 'paused')) {
      interval = setInterval(pollStatus, 1000);
    } else {
      // One-shot poll on mount
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

  // ─── Queue controls ───────────────────────────────────────────

  async function handlePrintAllNodes() {
    setBatchLoading(true);
    setBatchError(null);
    try {
      // First add batch
      const batchRes = await fetch('/api/v1/commandqueue/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (!batchRes.ok) {
        const data = await batchRes.json().catch(() => ({ message: 'Batch failed' }));
        throw new Error(data.message || `HTTP ${batchRes.status}`);
      }

      // Then start queue
      const startRes = await fetch('/api/v1/commandqueue/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!startRes.ok) {
        const data = await startRes.json().catch(() => ({ message: 'Start failed' }));
        throw new Error(data.message || `HTTP ${startRes.status}`);
      }

      // Immediately poll status
      const statusRes = await fetch('/api/v1/commandqueue/status');
      if (statusRes.ok) {
        const data: QueueStatusResponse = await statusRes.json();
        setQueueStatus(data);
        onQueueStatusChange?.(data);
      }
    } catch (err) {
      setBatchError(err instanceof Error ? err.message : 'Print All Nodes failed');
    } finally {
      setBatchLoading(false);
    }
  }

  async function handleQueueAction(action: 'pause' | 'resume' | 'cancel') {
    try {
      await fetch(`/api/v1/commandqueue/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      // Refresh status
      const res = await fetch('/api/v1/commandqueue/status');
      if (res.ok) {
        const data: QueueStatusResponse = await res.json();
        setQueueStatus(data);
        onQueueStatusChange?.(data);
      }
    } catch {
      // ignore
    }
  }

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

  // ─── Context menu ─────────────────────────────────────────────

  function handleContextMenu(e: React.MouseEvent, node: TreeNodeData) {
    e.preventDefault();
    e.stopPropagation();
    if (node.type === 'token') {
      setContextMenu({ x: e.clientX, y: e.clientY, node });
    }
  }

  function handleContextAction(action: string) {
    if (contextMenu) {
      onContextAction(action, contextMenu.node);
      setContextMenu(null);
    }
  }

  // ─── Render ────────────────────────────────────────────────────

  const queueActive =
    queueStatus && (queueStatus.state === 'running' || queueStatus.state === 'paused');

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
          title="Reload node tree from nodes.json"
        >
          Load Nodes
        </button>
        <button
          className="btn btn-primary"
          style={{ fontSize: '11px', padding: '4px 8px' }}
          onClick={handlePrintAllNodes}
          disabled={batchLoading}
          title="Generate FBC+RPC+LOG commands for all nodes and start queue"
        >
          {batchLoading ? (
            <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />
          ) : (
            <Printer size={12} />
          )}
          Print All
        </button>
        {queueActive && (
          <>
            {queueStatus?.state === 'running' && (
              <button
                className="btn btn-secondary"
                style={{ fontSize: '11px', padding: '4px 8px' }}
                onClick={() => handleQueueAction('pause')}
              >
                Pause
              </button>
            )}
            {queueStatus?.state === 'paused' && (
              <button
                className="btn btn-secondary"
                style={{ fontSize: '11px', padding: '4px 8px' }}
                onClick={() => handleQueueAction('resume')}
              >
                Resume
              </button>
            )}
            <button
              className="btn btn-secondary"
              style={{ fontSize: '11px', padding: '4px 8px', color: 'var(--error)' }}
              onClick={() => handleQueueAction('cancel')}
            >
              Cancel
            </button>
          </>
        )}
      </div>

      {/* Batch error */}
      {batchError && (
        <div
          style={{
            padding: '6px 8px',
            fontSize: '11px',
            color: 'var(--error)',
            backgroundColor: 'rgba(239,68,68,0.1)',
          }}
        >
          {batchError}
        </div>
      )}

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
                No nodes configured.
                <br />
                Load nodes.json to see the tree.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Context menu */}
      {contextMenu && (
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
            minWidth: '160px',
          }}
        >
          <ContextMenuItem icon={<Printer size={14} />} label="FBC Print" onClick={() => handleContextAction('fbc_print')} />
          <ContextMenuItem icon={<Printer size={14} />} label="RPC Print" onClick={() => handleContextAction('rpc_print')} />
          <ContextMenuItem icon={<Server size={14} />} label="BsTool ErrLog" onClick={() => handleContextAction('bstool_errlog')} />
          <ContextMenuItem icon={<Play size={14} />} label="Copy to Log" onClick={() => handleContextAction('copy_to_log')} />
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
  onContextMenu: (e: React.MouseEvent, node: TreeNodeData) => void;
}

function TreeBranch({
  node,
  depth,
  expandedNodes,
  onToggle,
  onSelectNode,
  onSelectToken,
  onContextMenu,
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
    } else if (node.type === 'token') {
      onSelectToken(node);
    }
  }

  return (
    <div>
      <div
        onClick={handleClick}
        onContextMenu={(e) => onContextMenu(e, node)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: '3px 8px 3px ' + indent + 'px',
          cursor: 'pointer',
          borderRadius: '4px',
          transition: 'background-color 0.1s ease',
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--bg-elevated)';
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent';
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

        {/* Node icon */}
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
            fill={statusColor}
            color={statusColor}
            style={{ flexShrink: 0, marginLeft: '3px' }}
          />
        )}

        {/* Name */}
        <span
          style={{
            fontSize: '12px',
            fontWeight: node.type === 'node' ? 600 : 400,
            color: node.type === 'node' ? 'var(--text-primary)' : 'var(--text-secondary)',
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
        {node.token_id && (
          <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: '4px' }}>
            :{node.port}/{node.protocol}
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