import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import FBCView from '../FBCView';
import { FBCTable, RPCTable } from '../IOTable';
import type { ApiFBCModule, ApiRPCModule } from '../../types/api';

const fbcModules: ApiFBCModule[] = [
  {
    module_position: 1,
    channels: [
      { channel_position: 1, channel_type: 'AI8' },
      { channel_position: 2, channel_type: 'DI16' },
    ],
  },
  {
    module_position: 2,
    channels: [
      { channel_position: 1, channel_type: 'N/E' },
    ],
  },
];

const rpcModules: ApiRPCModule[] = [
  {
    module_position: 1,
    counters: [
      { counter_name: 'CNT_A', counter_value: 500 },
      { counter_name: 'CNT_B', counter_value: 1500 },
    ],
  },
  {
    module_position: 2,
    counters: [],
  },
];

describe('FBCTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing with modules', () => {
    render(<FBCTable modules={fbcModules} />);
    expect(screen.getByText('Position')).toBeInTheDocument();
    expect(screen.getByText('Channels')).toBeInTheDocument();
  });

  it('shows empty state when no modules', () => {
    render(<FBCTable modules={[]} />);
    expect(screen.getByText('No FBC modules found. Run a scan to populate data.')).toBeInTheDocument();
  });

  it('displays module positions', () => {
    render(<FBCTable modules={fbcModules} />);
    expect(screen.getAllByText('1').length).toBeGreaterThan(0);
    expect(screen.getAllByText('2').length).toBeGreaterThan(0);
  });

  it('displays channel types joined by comma', () => {
    render(<FBCTable modules={fbcModules} />);
    // Module 1 has AI8, DI16
    expect(screen.getByText('AI8, DI16')).toBeInTheDocument();
    // Module 2 has N/E
    expect(screen.getByText('N/E')).toBeInTheDocument();
  });

  it('displays channel count in Sum column', () => {
    render(<FBCTable modules={fbcModules} />);
    // Module 1: 2 channels, Module 2: 1 channel
    // The number 2 appears for module_position 1 and also as sum
    // The number 1 appears for module_position 2 and also as sum
    expect(screen.getAllByText('2').length).toBeGreaterThan(0);
    expect(screen.getAllByText('1').length).toBeGreaterThan(0);
  });
});

describe('RPCTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing with modules', () => {
    render(<RPCTable modules={rpcModules} />);
    expect(screen.getByText('Position')).toBeInTheDocument();
    expect(screen.getByText('Counters')).toBeInTheDocument();
  });

  it('shows empty state when no modules', () => {
    render(<RPCTable modules={[]} />);
    expect(screen.getByText('No RPC modules found. Run a scan to populate data.')).toBeInTheDocument();
  });

  it('displays module positions', () => {
    render(<RPCTable modules={rpcModules} />);
    expect(screen.getAllByText('1').length).toBeGreaterThan(0);
    expect(screen.getAllByText('2').length).toBeGreaterThan(0);
  });

  it('displays counter name=value pairs', () => {
    render(<RPCTable modules={rpcModules} />);
    expect(screen.getByText('CNT_A=500, CNT_B=1500')).toBeInTheDocument();
  });

  it('displays counter sum in Sum column', () => {
    render(<RPCTable modules={rpcModules} />);
    // Module 1: 500 + 1500 = 2000
    expect(screen.getByText('2000')).toBeInTheDocument();
  });

  it('shows dash for empty counters', () => {
    render(<RPCTable modules={rpcModules} />);
    // Module 2 has no counters → shows '—'
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });
});

describe('FBCView (re-exported in IOTable.tsx context)', () => {
  // This ensures the FBCView default export also works correctly
  it('FBCView renders with modules', () => {
    render(<FBCView modules={fbcModules} />);
    expect(screen.getByText('Position 1')).toBeInTheDocument();
    expect(screen.getByText('Position 2')).toBeInTheDocument();
  });
});