// @ts-nocheck

export function ColorizedLog({ content }: { content: string }) {
  const lines = content.split('\n');
  return (
    <pre style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0, lineHeight: '1.5' }}>
      {lines.map((line, i) => {
        const trimmed = line.trim();
        let color = '#22c55e';
        if (trimmed.startsWith('Error') || trimmed.startsWith('[ERROR') || trimmed.startsWith('ERROR') ||
            trimmed.includes('failed') || trimmed.includes('Failed') || trimmed.includes('FAILED') ||
            trimmed.includes('not found') || trimmed.includes('No such') || trimmed.includes('Unknown agent') ||
            trimmed.includes('[BEL]')) {
          color = '#ef4444';
        } else if (trimmed.startsWith('>') || trimmed.startsWith('[Connecting') || trimmed.startsWith('[Executing') ||
                   trimmed.startsWith('Getting') || trimmed.startsWith('%') || trimmed.includes('49s%') || trimmed.includes('64s%')) {
          color = '#f59e0b';
        } else if (trimmed.startsWith('[Connected') || trimmed.startsWith('[Done') || trimmed.startsWith('OK')) {
          color = '#10b981';
        } else if (trimmed === '' || trimmed === '(empty file)') {
          color = 'var(--text-muted)';
        }
        return <div key={i} style={{ color }}>{line || '\u00A0'}</div>;
      })}
    </pre>
  );
}

