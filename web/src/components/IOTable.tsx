import type { ApiFBCModule, ApiRPCModule } from '../types/api';

interface FBCProps {
  modules: ApiFBCModule[];
}

interface RPCProps {
  modules: ApiRPCModule[];
}

const thStyle: React.CSSProperties = {
  padding: '8px 12px',
  textAlign: 'left',
  fontSize: '12px',
  fontWeight: 600,
  color: 'var(--accent)',
  borderBottom: '1px solid var(--border)',
  fontFamily: 'var(--font-mono)',
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
};

const tdStyle: React.CSSProperties = {
  padding: '6px 12px',
  fontSize: '13px',
  fontFamily: 'var(--font-mono)',
  color: 'var(--text-primary)',
  borderBottom: '1px solid var(--border)',
};

const dimTdStyle: React.CSSProperties = {
  ...tdStyle,
  color: 'var(--text-muted)',
  opacity: 0.5,
};

export function FBCTable({ modules }: FBCProps) {
  if (modules.length === 0) {
    return (
      <div
        className="card"
        style={{ textAlign: 'center', padding: '32px', color: 'var(--text-secondary)' }}
      >
        No FBC modules found. Run a scan to populate data.
      </div>
    );
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          backgroundColor: 'var(--bg-card)',
          borderRadius: '8px',
          overflow: 'hidden',
        }}
      >
        <thead>
          <tr>
            <th style={thStyle}>Position</th>
            <th style={thStyle}>Channels</th>
            <th style={{ ...thStyle, textAlign: 'right' }}>Sum</th>
          </tr>
        </thead>
        <tbody>
          {modules.map((mod) => {
            const channelTypes = mod.channels.map((ch) => ch.channel_type).join(', ');
            const sum = mod.channels.length;
            const isNotExists = mod.channels.length === 1 && mod.channels[0].channel_type === 'N/E';

            return (
              <tr
                key={mod.module_position}
                style={{
                  backgroundColor: isNotExists ? 'transparent' : undefined,
                }}
              >
                <td style={isNotExists ? dimTdStyle : tdStyle}>
                  {mod.module_position}
                </td>
                <td style={isNotExists ? dimTdStyle : tdStyle}>
                  {channelTypes || '—'}
                </td>
                <td style={{ ...(isNotExists ? dimTdStyle : tdStyle), textAlign: 'right' }}>
                  {sum}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function RPCTable({ modules }: RPCProps) {
  if (modules.length === 0) {
    return (
      <div
        className="card"
        style={{ textAlign: 'center', padding: '32px', color: 'var(--text-secondary)' }}
      >
        No RPC modules found. Run a scan to populate data.
      </div>
    );
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          backgroundColor: 'var(--bg-card)',
          borderRadius: '8px',
          overflow: 'hidden',
        }}
      >
        <thead>
          <tr>
            <th style={thStyle}>Position</th>
            <th style={thStyle}>Counters</th>
            <th style={{ ...thStyle, textAlign: 'right' }}>Sum</th>
          </tr>
        </thead>
        <tbody>
          {modules.map((mod) => {
            const counterNames = mod.counters.map((c) => `${c.counter_name}=${c.counter_value}`).join(', ');
            const sum = mod.counters.reduce((acc, c) => acc + c.counter_value, 0);
            const isNotExists = mod.counters.length === 0;

            return (
              <tr
                key={mod.module_position}
                style={{
                  backgroundColor: isNotExists ? 'transparent' : undefined,
                }}
              >
                <td style={isNotExists ? dimTdStyle : tdStyle}>
                  {mod.module_position}
                </td>
                <td style={isNotExists ? dimTdStyle : tdStyle}>
                  {counterNames || '—'}
                </td>
                <td style={{ ...(isNotExists ? dimTdStyle : tdStyle), textAlign: 'right' }}>
                  {sum}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
