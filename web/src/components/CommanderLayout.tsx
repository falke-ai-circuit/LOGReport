import { useState, useCallback } from 'react';
import { Terminal, Server, ScanLine, Settings } from 'lucide-react';
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

      switch (action) {
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
          // Strip suffix from current node name for BsTool
          setPendingServerName(stripNodeSuffix(currentNodeName));
          break;
        case 'copy_to_log':
          // This is handled by the TelnetTerminal's own Copy to Log button
          // But we can trigger it via a state signal
          break;
      }
    },
    [currentNodeName],
  );

  // ─── Tab bar ─────────────────────────────────────────────────

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
              <ScanTab selectedNode={selectedNode} />
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