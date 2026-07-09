import type { ApiRPCModule } from '../types/api';

interface RPCViewProps {
  modules: ApiRPCModule[];
}

// Counter value color thresholds
function counterColor(value: number): string {
  if (value === 0) return 'var(--text-muted)';
  if (value < 100) return '#3b82f6';   // blue — low
  if (value < 1000) return '#f59e0b';  // amber — medium
  if (value < 10000) return '#ef4444'; // red — high
  return '#dc2626';                     // deep red — very high
}

export default function RPCView({ modules }: RPCViewProps) {
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

  // Compute totals
  const totalCounters = modules.reduce((sum, m) => sum + m.counters.length, 0);
  const totalValue = modules.reduce(
    (sum, m) => sum + m.counters.reduce((s, c) => s + c.counter_value, 0),
    0,
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* Module columns */}
      {modules.map((mod) => {
        const isEmpty = mod.counters.length === 0;
        const modSum = mod.counters.reduce((s, c) => s + c.counter_value, 0);

        return (
          <div
            key={mod.module_position}
            className="card"
            style={{
              padding: '12px',
              opacity: isEmpty ? 0.4 : 1,
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
                {mod.counters.length} counter{mod.counters.length !== 1 ? 's' : ''}
              </span>
              {!isEmpty && (
                <span
                  style={{
                    color: counterColor(modSum),
                    fontWeight: 600,
                    marginLeft: '8px',
                  }}
                >
                  Σ {modSum.toLocaleString()}
                </span>
              )}
            </div>

            {/* Counter values */}
            {!isEmpty && (
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '8px',
                }}
              >
                {mod.counters.map((ctr, idx) => {
                  const color = counterColor(ctr.counter_value);

                  return (
                    <div
                      key={idx}
                      title={`${ctr.counter_name}: ${ctr.counter_value.toLocaleString()}`}
                      style={{
                        minWidth: '80px',
                        padding: '8px 10px',
                        borderRadius: '6px',
                        backgroundColor: `${color}15`,
                        border: `1px solid ${color}44`,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '2px',
                        cursor: 'default',
                        transition: 'all 0.15s ease',
                      }}
                      onMouseEnter={(e) => {
                        (e.currentTarget as HTMLElement).style.backgroundColor = `${color}28`;
                      }}
                      onMouseLeave={(e) => {
                        (e.currentTarget as HTMLElement).style.backgroundColor = `${color}15`;
                      }}
                    >
                      <span
                        style={{
                          fontSize: '10px',
                          fontFamily: 'var(--font-mono)',
                          color: 'var(--text-muted)',
                          textTransform: 'uppercase',
                          letterSpacing: '0.3px',
                        }}
                      >
                        {ctr.counter_name}
                      </span>
                      <span
                        style={{
                          fontSize: '16px',
                          fontFamily: 'var(--font-mono)',
                          fontWeight: 700,
                          color,
                        }}
                      >
                        {ctr.counter_value.toLocaleString()}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}

            {isEmpty && (
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                No counters
              </div>
            )}
          </div>
        );
      })}

      {/* Totals footer */}
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
            {totalCounters} counter{totalCounters !== 1 ? 's' : ''}
          </span>
        </div>
        <span
          style={{
            fontSize: '18px',
            fontFamily: 'var(--font-mono)',
            fontWeight: 700,
            color: counterColor(totalValue),
          }}
        >
          Σ {totalValue.toLocaleString()}
        </span>
      </div>
    </div>
  );
}
