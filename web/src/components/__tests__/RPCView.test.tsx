import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import RPCView from '../RPCView';
import type { ApiRPCModule } from '../../types/api';

const modules: ApiRPCModule[] = [
  {
    module_position: 1,
    counters: [
      { counter_name: 'CNT_A', counter_value: 50 },
      { counter_name: 'CNT_B', counter_value: 500 },
    ],
  },
  {
    module_position: 2,
    counters: [
      { counter_name: 'CNT_C', counter_value: 5000 },
      { counter_name: 'CNT_D', counter_value: 50000 },
    ],
  },
  {
    module_position: 3,
    counters: [],
  },
];

describe('RPCView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing with modules', () => {
    render(<RPCView modules={modules} />);
    expect(screen.getByText('Position 1')).toBeInTheDocument();
  });

  it('shows empty state when no modules', () => {
    render(<RPCView modules={[]} />);
    expect(screen.getByText('No RPC modules found. Run a scan to populate data.')).toBeInTheDocument();
  });

  it('displays module positions for all modules', () => {
    render(<RPCView modules={modules} />);
    expect(screen.getByText('Position 1')).toBeInTheDocument();
    expect(screen.getByText('Position 2')).toBeInTheDocument();
    expect(screen.getByText('Position 3')).toBeInTheDocument();
  });

  it('shows counter names', () => {
    render(<RPCView modules={modules} />);
    expect(screen.getByText('CNT_A')).toBeInTheDocument();
    expect(screen.getByText('CNT_B')).toBeInTheDocument();
    expect(screen.getByText('CNT_C')).toBeInTheDocument();
    expect(screen.getByText('CNT_D')).toBeInTheDocument();
  });

  it('shows counter values formatted with locale strings', () => {
    render(<RPCView modules={modules} />);
    // Values: 50, 500, 5000, 50000
    // 50000 may display as "50,000" depending on locale
    expect(screen.getByText('50')).toBeInTheDocument();
    expect(screen.getByText('500')).toBeInTheDocument();
  });

  it('shows counter count per module', () => {
    render(<RPCView modules={modules} />);
    expect(screen.getAllByText('2 counters').length).toBeGreaterThan(0);
    expect(screen.getByText('0 counters')).toBeInTheDocument();
  });

  it('shows Σ sum per module', () => {
    render(<RPCView modules={modules} />);
    // Module 1: 50 + 500 = 550
    expect(screen.getByText('Σ 550')).toBeInTheDocument();
    // Module 2: 5000 + 50000 = 55000
    expect(screen.getByText('Σ 55,000')).toBeInTheDocument();
  });

  it('shows No counters for empty modules', () => {
    render(<RPCView modules={modules} />);
    expect(screen.getByText('No counters')).toBeInTheDocument();
  });

  it('shows Totals footer with module and counter counts', () => {
    render(<RPCView modules={modules} />);
    expect(screen.getByText('Totals')).toBeInTheDocument();
    expect(screen.getByText('3 modules')).toBeInTheDocument();
    // Total counters: 2 + 2 + 0 = 4
    expect(screen.getByText('4 counters')).toBeInTheDocument();
  });

  it('shows total Σ sum in footer', () => {
    render(<RPCView modules={modules} />);
    // Total: 50 + 500 + 5000 + 50000 = 55,550
    expect(screen.getByText('Σ 55,550')).toBeInTheDocument();
  });

  it('renders counter cells with title tooltips', () => {
    const { container } = render(<RPCView modules={modules} />);
    const titledElements = container.querySelectorAll('[title]');
    expect(titledElements.length).toBeGreaterThan(0);
    const cntTooltip = Array.from(titledElements).find((el) =>
      el.getAttribute('title')?.includes('CNT_A'),
    );
    expect(cntTooltip).toBeTruthy();
  });

  it('handles modules with a single counter', () => {
    const singleMod: ApiRPCModule[] = [
      {
        module_position: 1,
        counters: [{ counter_name: 'SOLO', counter_value: 100 }],
      },
    ];
    render(<RPCView modules={singleMod} />);
    expect(screen.getByText('SOLO')).toBeInTheDocument();
    expect(screen.getAllByText('1 counter').length).toBeGreaterThan(0);
  });

  it('handles zero value counters', () => {
    const zeroMod: ApiRPCModule[] = [
      {
        module_position: 1,
        counters: [{ counter_name: 'ZERO', counter_value: 0 }],
      },
    ];
    render(<RPCView modules={zeroMod} />);
    expect(screen.getByText('ZERO')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
  });
});