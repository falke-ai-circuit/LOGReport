import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import QueueTab from '../QueueTab';

const mockCommands = [
  { id: 'cmd1', type: 'fbc', node_name: 'AL01m', token_id: '102', command: 'print from fbc 102', status: 'pending' },
  { id: 'cmd2', type: 'rpc', node_name: 'AL01m', token_id: '201', command: 'print from rpc 201', status: 'pending' },
  { id: 'cmd3', type: 'fbc', node_name: 'AL02m', token_id: '103', command: 'print from fbc 103', status: 'completed' },
];

const mockStatusWithCommands = {
  current: 1,
  total: 3,
  state: 'idle',
  commands: mockCommands,
};

const mockStatusEmpty = {
  current: 0,
  total: 0,
  state: 'idle',
  commands: [],
};

const mockStatusWithFailures = {
  current: 3,
  total: 3,
  state: 'done',
  commands: [
    { id: 'cmd1', type: 'fbc', node_name: 'AL01m', token_id: '102', command: 'print from fbc 102', status: 'completed' },
    { id: 'cmd2', type: 'rpc', node_name: 'AL01m', token_id: '201', command: 'print from rpc 201', status: 'failed', error: 'timeout' },
    { id: 'cmd3', type: 'fbc', node_name: 'AL02m', token_id: '103', command: 'print from fbc 103', status: 'completed' },
  ],
};

function mockFetchImpl(url: any, options?: any) {
  if (url?.includes('/commandqueue/clear') && options?.method === 'POST') {
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}), text: () => Promise.resolve('') } as Response);
  }
  if (url?.includes('/commandqueue/restart') && options?.method === 'POST') {
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}), text: () => Promise.resolve('') } as Response);
  }
  if (url?.includes('/commandqueue/retry-failed') && options?.method === 'POST') {
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}), text: () => Promise.resolve('') } as Response);
  }
  if (url?.includes('/commandqueue/status')) {
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(mockStatusWithCommands), text: () => Promise.resolve('') } as Response);
  }
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}), text: () => Promise.resolve('') } as Response);
}

function renderComponent(statusOverride: any = mockStatusWithCommands) {
  global.fetch = vi.fn((url: any, options?: any) => {
    if (url?.includes('/commandqueue/status')) {
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(statusOverride), text: () => Promise.resolve('') } as Response);
    }
    return mockFetchImpl(url, options);
  }) as any;
  return render(<QueueTab />);
}

describe('QueueTab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn(mockFetchImpl) as any;
  });

  it('renders commands from API', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('print from fbc 102')).toBeInTheDocument();
    });
    expect(screen.getByText('print from rpc 201')).toBeInTheDocument();
    expect(screen.getByText('print from fbc 103')).toBeInTheDocument();
  });

  it('shows empty state when no commands', async () => {
    renderComponent(mockStatusEmpty);
    await waitFor(() => {
      expect(screen.getByText(/No commands queued/i)).toBeInTheDocument();
    });
  });

  it('renders Command Queue title', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Command Queue')).toBeInTheDocument();
    });
  });

  it('renders Add button', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Add')).toBeInTheDocument();
    });
  });

  it('clear button calls /commandqueue/clear', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('print from fbc 102')).toBeInTheDocument();
    });
    const clearButton = screen.getByText('Clear');
    await userEvent.click(clearButton);
    await waitFor(() => {
      const clearCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => typeof c[0] === 'string' && c[0].includes('/commandqueue/clear') && (c[1] as any)?.method === 'POST',
      );
      expect(clearCalls.length).toBeGreaterThan(0);
    });
  });

  it('restart button calls /commandqueue/restart', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('print from fbc 102')).toBeInTheDocument();
    });
    const restartButton = screen.getByText('Restart');
    await userEvent.click(restartButton);
    await waitFor(() => {
      const restartCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => typeof c[0] === 'string' && c[0].includes('/commandqueue/restart') && (c[1] as any)?.method === 'POST',
      );
      expect(restartCalls.length).toBeGreaterThan(0);
    });
  });

  it('retry failed button visible when failures exist', async () => {
    renderComponent(mockStatusWithFailures);
    await waitFor(() => {
      expect(screen.getByText(/Retry Failed/)).toBeInTheDocument();
    });
  });

  it('retry failed button hidden when no failures', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('print from fbc 102')).toBeInTheDocument();
    });
    expect(screen.queryByText(/Retry Failed/)).not.toBeInTheDocument();
  });

  it('retry failed calls /commandqueue/retry-failed', async () => {
    renderComponent(mockStatusWithFailures);
    await waitFor(() => {
      expect(screen.getByText(/Retry Failed/)).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText(/Retry Failed/));
    await waitFor(() => {
      const retryCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => typeof c[0] === 'string' && c[0].includes('/commandqueue/retry-failed') && (c[1] as any)?.method === 'POST',
      );
      expect(retryCalls.length).toBeGreaterThan(0);
    });
  });

  it('does NOT render a Config button', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Command Queue')).toBeInTheDocument();
    });
    expect(screen.queryByText('Config')).not.toBeInTheDocument();
  });

  it('shows type badges (FBC, RPC)', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('FBC')).toBeInTheDocument();
    });
    expect(screen.getByText('RPC')).toBeInTheDocument();
  });

  it('shows sort options', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('print from fbc 102')).toBeInTheDocument();
    });
    // Sort select exists
    const sortSelect = screen.getByDisplayValue('Order');
    expect(sortSelect).toBeInTheDocument();
  });

  it('sorts by type when sort changed', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('print from fbc 102')).toBeInTheDocument();
    });
    const sortSelect = screen.getByDisplayValue('Order');
    await userEvent.selectOptions(sortSelect, 'type');
    // Commands should still be visible, just reordered
    expect(screen.getByText('print from fbc 102')).toBeInTheDocument();
    expect(screen.getByText('print from rpc 201')).toBeInTheDocument();
  });

  it('sorts by status when sort changed', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('print from fbc 102')).toBeInTheDocument();
    });
    const sortSelect = screen.getByDisplayValue('Order');
    await userEvent.selectOptions(sortSelect, 'status');
    expect(screen.getByText('print from fbc 102')).toBeInTheDocument();
  });

  it('shows bottom summary with counts', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText(/Total:/)).toBeInTheDocument();
    });
    expect(screen.getByText(/Pending:/)).toBeInTheDocument();
    expect(screen.getByText(/Completed:/)).toBeInTheDocument();
  });
});