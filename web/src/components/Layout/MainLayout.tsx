import { NodeTree } from '../NodeTree/NodeTree'
import { TabContainer } from '../Tabs/TabContainer'

export function MainLayout() {
  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Left pane — node tree */}
      <div style={{
        width: 300,
        minWidth: 200,
        maxWidth: 400,
        background: '#141414',
        borderRight: '1px solid #2a2a2a',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{
          padding: '10px 12px',
          background: '#0f0f0f',
          borderBottom: '1px solid #2a2a2a',
          fontSize: 14,
          fontWeight: 600,
          color: '#e0e0e0',
          letterSpacing: 0.5
        }}>
          Commander LogCreator v2.0
        </div>
        <div style={{ flex: 1, overflow: 'auto' }}>
          <NodeTree />
        </div>
      </div>

      {/* Right pane — tabs */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <TabContainer />
      </div>
    </div>
  )
}
