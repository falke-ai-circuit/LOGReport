import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import NodeDetail from '../NodeDetail';

const nodeDetailData = {
  node: {
    id: 1,
    address: '192.168.1.10',
    port: 23,
    name: 'Test Node',
    node_type: 'ACN',
    token: 'abc123',
    status: 'connected',
    last_connected: '2025-01-01T10:00:00Z',
    created_at: '2025-01-01T09:00:00Z',
    updated_at: '2025-01-01T10:00:00Z',
  },
  io_summary: {
    fbc_modules: 3,
    rpc_modules: 2,
    total_io_points: 48,
    last_scan: '2025-01-01T10:00:00Z',
  },
};

const fbcData = {
  node_address: '192.168.1.10',
  fbc_modules: [
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
  ],
  total_modules: 2,
};

const rpcData = {
  node_address: '192.168.1.10',
  rpc_modules: [
    {
      module_position: 1,
      counters: [
        { counter_name: 'CNT_A', counter_value: 500 },
        { counter_name: 'CNT_B', counter_value: 1500 },
      ],
    },
  ],
  total_modules: 1,
};

const scanResponse = {
  node_address: '192.168.1.10',
  scanned_at: '2025-01-01T11:00:00Z',
  fbc_modules: fbcData.fbc_modules,
  rpc_modules: rpcData.rpc_modules,
  io_points_total: 48,
};

function mockFetchImpl(url: any, options?: any) {
  if (options?.method === 'POST' && url.includes('/scan')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(scanResponse),
      text: () => Promise.resolve(''),
    } as Response);
  }
  if (url.includes('/fbc')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(fbcData),
      text: () => Promise.resolve(''),
    } as Response);
  }
  if (url.includes('/rpc')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(rpcData),
      text: () => Promise.resolve(''),
    } as Response);
  }
  // Node detail
  return Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve(nodeDetailData),
    text: () => Promise.resolve(''),
  } as Response);
}

function renderComponent(addr = '192.168.1.10') {
  return render(
    <MemoryRouter initialEntries={[`/nodes/${addr}`]}>
      <Routes>
        <Route path="/nodes/:addr" element={<NodeDetail />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('NodeDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state on mount', () => {
    vi.mocked(global.fetch).mockReturnValue(new Promise(() => {}));
    renderComponent();
    expect(screen.getByText('Loading node...')).toBeInTheDocument();
  });

  it('fetches /api/v1/nodes/:addr on mount', async () => {
    vi.mocked(global.fetch).mockImplementation(mockFetchImpl);
    renderComponent('192.168.1.10');

    await waitFor(() => {
      expect(
        vi.mocked(global.fetch).mock.calls.some((c) => c[0] === '/api/v1/nodes/192.168.1.10'),
      ).toBe(true);
    });
  });

  it('displays node name and info after successful fetch', async () => {
    vi.mocked(global.fetch).mockImplementation(mockFetchImpl);
    renderComponent();

    await waitFor(() => {
      expect(screen.getAllByText('Test Node').length).toBeGreaterThan(0);
    });
    expect(screen.getByText('ACN')).toBeInTheDocument();
    expect(screen.getByText('192.168.1.10:23')).toBeInTheDocument();
    expect(screen.getByText('connected')).toBeInTheDocument();
  });

  it('displays IO summary on the info tab', async () => {
    vi.mocked(global.fetch).mockImplementation(mockFetchImpl);
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument();
    });
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('48')).toBeInTheDocument();
  });

  it('shows error state when fetch fails', async () => {
    vi.mocked(global.fetch).mockRejectedValue(new Error('Failed to load'));
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Failed to load')).toBeInTheDocument();
    });
    expect(screen.getByText('Back to Nodes')).toBeInTheDocument();
  });

  it('shows error state when response is not ok', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ message: 'Node not found' }),
      text: () => Promise.resolve(''),
    } as Response);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Node not found')).toBeInTheDocument();
    });
  });

  it('has Info, FBC, and RPC tabs', async () => {
    vi.mocked(global.fetch).mockImplementation(mockFetchImpl);
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Info')).toBeInTheDocument();
    });
    expect(screen.getByText('FBC')).toBeInTheDocument();
    expect(screen.getByText('RPC')).toBeInTheDocument();
  });

  it('shows Scan and Generate Report buttons', async () => {
    vi.mocked(global.fetch).mockImplementation(mockFetchImpl);
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Scan')).toBeInTheDocument();
    });
    expect(screen.getByText('Generate Report')).toBeInTheDocument();
  });

  it('triggers POST scan when Scan button is clicked', async () => {
    vi.mocked(global.fetch).mockImplementation(mockFetchImpl);
    renderComponent();

    await waitFor(() => {
      expect(screen.getAllByText('Test Node').length).toBeGreaterThan(0);
    });

    await userEvent.click(screen.getByText('Scan'));

    await waitFor(() => {
      const scanCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => typeof c[1] === 'object' && c[1]?.method === 'POST' && (c[0] as string).includes('/scan'),
      );
      expect(scanCalls.length).toBeGreaterThan(0);
    });
  });

  it('shows scan result after successful scan', async () => {
    vi.mocked(global.fetch).mockImplementation(mockFetchImpl);
    renderComponent();

    await waitFor(() => {
      expect(screen.getAllByText('Test Node').length).toBeGreaterThan(0);
    });

    await userEvent.click(screen.getByText('Scan'));

    await waitFor(() => {
      expect(screen.getByText(/Scan complete/)).toBeInTheDocument();
    });
  });

  it('fetches and displays FBC data when FBC tab is clicked', async () => {
    vi.mocked(global.fetch).mockImplementation(mockFetchImpl);
    renderComponent();

    await waitFor(() => {
      expect(screen.getAllByText('Test Node').length).toBeGreaterThan(0);
    });

    await userEvent.click(screen.getByText('FBC'));

    await waitFor(() => {
      expect(
        vi.mocked(global.fetch).mock.calls.some((c) => (c[0] as string).includes('/fbc')),
      ).toBe(true);
    });

    // FBCView should show module positions
    await waitFor(() => {
      expect(screen.getByText('Position 1')).toBeInTheDocument();
    });
  });

  it('fetches and displays RPC data when RPC tab is clicked', async () => {
    vi.mocked(global.fetch).mockImplementation(mockFetchImpl);
    renderComponent();

    await waitFor(() => {
      expect(screen.getAllByText('Test Node').length).toBeGreaterThan(0);
    });

    await userEvent.click(screen.getByText('RPC'));

    await waitFor(() => {
      expect(
        vi.mocked(global.fetch).mock.calls.some((c) => (c[0] as string).includes('/rpc')),
      ).toBe(true);
    });

    await waitFor(() => {
      expect(screen.getByText('CNT_A')).toBeInTheDocument();
    });
  });

  it('shows Scanning... state during scan', async () => {
    let resolveScan: (value: any) => void;
    vi.mocked(global.fetch).mockImplementation((url: any, options?: any) => {
      if (options?.method === 'POST' && url.includes('/scan')) {
        return new Promise((resolve) => {
          resolveScan = resolve;
        }) as Promise<Response>;
      }
      return mockFetchImpl(url, options);
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getAllByText('Test Node').length).toBeGreaterThan(0);
    });

    await userEvent.click(screen.getByText('Scan'));

    await waitFor(() => {
      expect(screen.getByText('Scanning...')).toBeInTheDocument();
    });

    resolveScan!({
      ok: true,
      status: 200,
      json: () => Promise.resolve(scanResponse),
      text: () => Promise.resolve(''),
    } as Response);
  });

  it('shows scan error when scan POST fails', async () => {
    vi.mocked(global.fetch).mockImplementation((url: any, options?: any) => {
      if (options?.method === 'POST' && url.includes('/scan')) {
        return Promise.resolve({
          ok: false,
          status: 500,
          json: () => Promise.resolve({ message: 'Scan timeout' }),
          text: () => Promise.resolve(''),
        } as Response);
      }
      return mockFetchImpl(url, options);
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getAllByText('Test Node').length).toBeGreaterThan(0);
    });

    await userEvent.click(screen.getByText('Scan'));

    await waitFor(() => {
      expect(screen.getByText('Scan timeout')).toBeInTheDocument();
    });
  });
});