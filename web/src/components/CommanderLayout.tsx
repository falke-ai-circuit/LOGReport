import { useState, useCallback } from 'react';
import { Terminal, Server, ScanLine, Settings, FolderOpen, Loader2 } from 'lucide-react';
import NodeTree from './NodeTree';
import TelnetTerminal from './TelnetTerminal';
import BsToolPanel from './BsToolPanel';
import ScanTab from './ScanTab';
import CommandQueueBar from './CommandQueueBar';
import NodeConfigDialog from './NodeConfigDialog';
import type { TreeNodeData, QueueStatusResponse } from '../types/api';

type Tab = 'telnet' | 'bstool' | 'scan';

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

  // ─── Node tree callbacks ─────────────────────────────────────

  const handleSelectNode = useCallback((node: TreeNodeData) => {
    setSelectedNode(node);
    setCurrentNodeName(node.name);
  }, []);

  const handleSelectToken = useCallback((token: TreeNodeData) => {
    setSelectedToken(token);
    setCurrentToken(token.token_id || '');
    // Determine token type from parent group — we infer from the token's context
    // The tree structure is node → group (FBC/RPC/LOG) → token
    // We don't have the parent here, so default to FBC
    setCurrentTokenType('FBC');
  }, []);

  // ─── Context menu actions ───────────────────────────────────

  const handleContextAction = useCallback(
    (action: string, token: TreeNodeData) => {
      const tokenId = token.token_id || '';
      const nodeName = token.name || currentNodeName;

      switch (action) {
        case 'print_all': {
          // Execute all print commands for this node (FBC + RPC + LOG)
          // Uses the batch-node API endpoint
          setActiveTab('commander');
          fetch('/api/v1/commandqueue/batch-node', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ node_name: nodeName }),
          }).then(res => res.json()).then(data => {
            // Start queue execution
            fetch('/api/v1/commandqueue/start', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: '{}',
            });
          }).catch(err => console.error('batch-node error:', err));
          break;
        }
        case 'fbc_print_all': {
          setActiveTab('commander');
          fetch('/api/v1/commandqueue/batch-node', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ node_name: nodeName, token_type: 'FBC' }),
          }).then(res => res.json()).then(data => {
            fetch('/api/v1/commandqueue/start', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: '{}',
            });
          }).catch(err => console.error('fbc_batch error:', err));
          break;
        }
        case 'rpc_print_all': {
          setActiveTab('commander');
          fetch('/api/v1/commandqueue/batch-node', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ node_name: nodeName, token_type: 'RPC' }),
          }).then(res => res.json()).then(data => {
            fetch('/api/v1/commandqueue/start', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: '{}',
            });
          }).catch(err => console.error('rpc_batch error:', err));
          break;
        }
        case 'fbc_print':
          setActiveTab('telnet');
          setPendingCommand(`fis ${tokenId}`);
          break;
        case 'rpc_print':
          setActiveTab('telnet');
          setPendingCommand(`rc ${tokenId}`);
          break;
        case 'bstool_errlog':
          setActiveTab('bstool');
          setPendingServerName(stripNodeSuffix(nodeName));
          break;
        case 'copy_to_log':
          break;
      }
    },
    [currentNodeName],
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
      // Also verify the path lists files
      const listRes = await fetch(`/api/v1/logs/files?path=${encodeURIComponent(logRootInput)}&type=fbc`);
      let fileCount = 0;
      if (listRes.ok) {
        const listData = await listRes.json();
        fileCount = listData.count || 0;
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

  // ─── Tab bar ────────────────────────────────────────────────────

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'telnet', label: 'Telnet', icon: <Terminal size={14} /> },
    { id: 'bstool', label: 'BsTool', icon: <Server size={14} /> },
    { id: 'scan', label: 'Scan', icon: <ScanLine size={14} /> },
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
          onClick={() => setShowConfigDialog(true)}
          title="Configure nodes and tokens"
        >
          <Settings size={14} />
          Config
        </button>
      </div>

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
              <TelnetTerminal
                currentToken={currentToken}
                currentTokenType={currentTokenType}
                currentNodeName={currentNodeName}
                pendingCommand={pendingCommand}
                onCommandSent={() => setPendingCommand(null)}
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