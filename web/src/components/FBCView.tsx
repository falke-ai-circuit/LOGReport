import type { ApiFBCModule } from '../types/api';

interface FBCViewProps {
  modules: ApiFBCModule[];
}

// Channel type → color mapping (AXON industrial palette)
const CHANNEL_COLORS: Record<string, string> = {
  AI8: '#3b82f6',   // blue — analog input
  AO4: '#10b981',   // green — analog output
  DI16: '#f59e0b',  // amber/yellow — digital input
  DO16: '#ef4444',  // red — digital output
  AI16: '#6366f1',  // indigo
  AO8: '#14b8a6',   // teal
  DI8: '#eab308',   // yellow
  DO8: '#dc2626',   // red
  'N/E': '#6a6a7a', // muted gray — not equipped
};

const CHANNEL_LABELS: Record<string, string> = {
  AI8: 'AI',
  AO4: 'AO',
  DI16: 'DI',
  DO16: 'DO',
  AI16: 'AI',
  AO8: 'AO',
  DI8: 'DI',
  DO8: 'DO',
  'N/E': '—',
};

export default function FBCView({ modules }: FBCViewProps) {
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

  // Compute totals
  const totalChannels = modules.reduce((sum, m) => sum + m.channels.length, 0);
  const typeCounts: Record<string, number> = {};
  for (const mod of modules) {
    for (const ch of mod.channels) {
      typeCounts[ch.channel_type] = (typeCounts[ch.channel_type] || 0) + 1;
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* Module grid */}
      {modules.map((mod) => {
        const isNotExists =
          mod.channels.length === 1 && mod.channels[0].channel_type === 'N/E';

        return (
          <div
            key={mod.module_position}
            className="card"
            style={{
              padding: '12px',
              opacity: isNotExists ? 0.4 : 1,
            }}
          >
            {/* Module position label */}
            <div
              style={{
                fontSize: '11px',
                fontWeight: 600,
                color: 'var(--accent)',
                fontFamily: 'var(--font-mono)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '8px',
              }}
            >
              Position {mod.module_position}
              <span style={{ color: 'var(--text-muted)', fontWeight: 400, marginLeft: '8px' }}>
                {mod.channels.length} channel{mod.channels.length !== 1 ? 's' : ''}
              </span>
            </div>

            {/* Channel cells */}
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '6px',
              }}
            >
              {mod.channels.map((ch, idx) => {
                const color = CHANNEL_COLORS[ch.channel_type] || 'var(--text-muted)';
                const label = CHANNEL_LABELS[ch.channel_type] || ch.channel_type;

                return (
                  <div
                    key={idx}
                    title={`Ch ${ch.channel_position}: ${ch.channel_type}`}
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '6px',
                      backgroundColor: `${color}22`,
                      border: `1.5px solid ${color}`,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '10px',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 600,
                      color,
                      cursor: 'default',
                      transition: 'all 0.15s ease',
                    }}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLElement).style.backgroundColor = `${color}44`;
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLElement).style.backgroundColor = `${color}22`;
                    }}
                  >
                    <span style={{ fontSize: '12px', lineHeight: 1 }}>{label}</span>
                    <span style={{ fontSize: '9px', opacity: 0.7 }}>{ch.channel_position}</span>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}

      {/* Totals card */}
      <div
        className="card-elevated"
        style={{
          padding: '14px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
            Totals
          </span>
          <span
            style={{
              fontSize: '13px',
              color: 'var(--text-secondary)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {modules.length} module{modules.length !== 1 ? 's' : ''}
          </span>
          <span
            style={{
              fontSize: '13px',
              color: 'var(--text-secondary)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {totalChannels} channel{totalChannels !== 1 ? 's' : ''}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {Object.entries(typeCounts)
            .sort(([, a], [, b]) => b - a)
            .map(([type, count]) => {
              const color = CHANNEL_COLORS[type] || 'var(--text-muted)';
              return (
                <span
                  key={type}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '11px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 500,
                    color,
                    backgroundColor: `${color}18`,
                    padding: '2px 8px',
                    borderRadius: '4px',
                    border: `1px solid ${color}44`,
                  }}
                >
                  <span
                    style={{
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      backgroundColor: color,
                    }}
                  />
                  {type}: {count}
                </span>
              );
            })}
        </div>
      </div>
    </div>
  );
}
