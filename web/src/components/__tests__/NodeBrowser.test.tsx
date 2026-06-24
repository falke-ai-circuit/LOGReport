import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import NodeBrowser from '../NodeBrowser';

const mockNodes = {
  nodes: [
    {
      id: 1,
      address: '192.168.1.10',
      port: 23,
      name: 'Node Alpha',
      node_type: 'ACN',
      token: 'tok1',
      status: 'connected',
      last_connected: '2025-01-01T10:00:00Z',
      created_at: '2025-01-01T09:00:00Z',
      updated_at: '2025-01-01T10:00:00Z',
    },
    {
      id: 2,
      address: '192.168.1.20',
      port: 23,
      name: 'Node Beta',
      node_type: 'CIS',
      token: 'tok2',
      status: 'disconnected',
      last_connected: '',
      created_at: '2025-01-01T09:00:00Z',
      updated_at: '2025-01-01T09:00:00Z',
    },
  ],
  total: 2,
  limit: 100,
  offset: 0,
};

function mockFetchSuccess(data = mockNodes) {
  vi.mocked(global.fetch).mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(''),
  } as Response);
}

function renderComponent() {
  return render(
    <MemoryRouter>
      <NodeBrowser />
    </MemoryRouter>,
  );
}

describe('NodeBrowser', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    mockFetchSuccess();
    renderComponent();
    expect(screen.getByText('Node Browser')).toBeInTheDocument();
  });

  it('shows loading state on mount', () => {
    vi.mocked(global.fetch).mockReturnValue(new Promise(() => {}));
    renderComponent();
    expect(screen.getByText('Loading nodes...')).toBeInTheDocument();
  });

  it('fetches /api/v1/nodes on mount', async () => {
    mockFetchSuccess();
    renderComponent();

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/nodes');
    });
  });

  it('displays nodes after successful fetch', async () => {
    mockFetchSuccess();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Node Alpha')).toBeInTheDocument();
    });
    expect(screen.getByText('Node Beta')).toBeInTheDocument();
    expect(screen.getByText('192.168.1.10:23')).toBeInTheDocument();
    expect(screen.getByText('192.168.1.20:23')).toBeInTheDocument();
    expect(screen.getByText('ACN')).toBeInTheDocument();
    expect(screen.getByText('CIS')).toBeInTheDocument();
  });

  it('shows empty state when no nodes are returned', async () => {
    mockFetchSuccess({ nodes: [], total: 0, limit: 100, offset: 0 });
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('No nodes configured. Add a node to get started.')).toBeInTheDocument();
    });
  });

  it('shows error state when fetch fails', async () => {
    vi.mocked(global.fetch).mockRejectedValue(new Error('Network error'));
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('shows error state when response is not ok', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({}),
      text: () => Promise.resolve('Server error'),
    } as Response);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText(/HTTP 500/)).toBeInTheDocument();
    });
  });

  it('renders Add Node button', async () => {
    mockFetchSuccess();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Add Node')).toBeInTheDocument();
    });
  });

  it('opens connect form modal when Add Node is clicked', async () => {
    mockFetchSuccess();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Node Alpha')).toBeInTheDocument();
    });

    // There are two "Add Node" buttons (header + empty state is hidden since we have nodes)
    const addButtons = screen.getAllByText('Add Node');
    await userEvent.click(addButtons[0]);

    expect(screen.getByText('Connect Node')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('e.g. 192.168.1.100')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Node display name')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('e.g. ACN, CIS')).toBeInTheDocument();
  });

  it('shows search filter input', async () => {
    mockFetchSuccess();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search by name, address, or type...')).toBeInTheDocument();
    });
  });

  it('filters nodes by search text', async () => {
    mockFetchSuccess();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Node Alpha')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search by name, address, or type...');
    await userEvent.type(searchInput, 'Alpha');

    expect(screen.getByText('Node Alpha')).toBeInTheDocument();
    expect(screen.queryByText('Node Beta')).not.toBeInTheDocument();
  });

  it('shows no-match message when search has no results', async () => {
    mockFetchSuccess();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Node Alpha')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search by name, address, or type...');
    await userEvent.type(searchInput, 'NonExistent');

    expect(screen.getByText(/No nodes match/)).toBeInTheDocument();
  });

  it('can fill out and submit the connect form', async () => {
    mockFetchSuccess();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Node Alpha')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText('Add Node'));

    // Fill the form
    await userEvent.type(screen.getByPlaceholderText('e.g. 192.168.1.100'), '10.0.0.5');
    await userEvent.type(screen.getByPlaceholderText('Node display name'), 'New Node');

    // Submit
    const connectButton = screen.getByRole('button', { name: /Connect/i });
    await userEvent.click(connectButton);

    // Should have called fetch with POST /api/v1/connect
    await waitFor(() => {
      const postCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => c[0] === '/api/v1/connect',
      );
      expect(postCalls.length).toBeGreaterThan(0);
    });
  });

  it('can close the connect form modal with the X button', async () => {
    mockFetchSuccess();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Node Alpha')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText('Add Node'));
    expect(screen.getByText('Connect Node')).toBeInTheDocument();

    // Click the X button (btn-ghost inside modal)
    const closeButton = screen.getByRole('button', { name: '' });
    // Find the X button — it's the ghost button with X icon
    const xButtons = screen.getAllByRole('button');
    // The X button is the one with no text content except the svg
    const xBtn = xButtons.find((b) => b.className.includes('btn-ghost'));
    expect(xBtn).toBeTruthy();
    await userEvent.click(xBtn!);

    await waitFor(() => {
      expect(screen.queryByText('Connect Node')).not.toBeInTheDocument();
    });
  });

  it('shows connecting state during form submission', async () => {
    // Make the POST return a pending promise
    let resolvePost: (value: any) => void;
    vi.mocked(global.fetch).mockImplementation((url: any) => {
      if (url === '/api/v1/connect') {
        return new Promise((resolve) => {
          resolvePost = resolve;
        }) as Promise<Response>;
      }
      // Initial nodes fetch + refresh
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockNodes),
        text: () => Promise.resolve(''),
      } as Response);
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Node Alpha')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText('Add Node'));
    await userEvent.type(screen.getByPlaceholderText('e.g. 192.168.1.100'), '10.0.0.5');
    await userEvent.type(screen.getByPlaceholderText('Node display name'), 'New');

    const connectButton = screen.getByRole('button', { name: /Connect/i });
    await userEvent.click(connectButton);

    await waitFor(() => {
      expect(screen.getByText('Connecting...')).toBeInTheDocument();
    });

    // Cleanup: resolve the pending promise
    resolvePost!({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
      text: () => Promise.resolve(''),
    } as Response);
  });

  it('shows connect error when POST fails', async () => {
    vi.mocked(global.fetch).mockImplementation((url: any) => {
      if (url === '/api/v1/connect') {
        return Promise.resolve({
          ok: false,
          status: 400,
          json: () => Promise.resolve({ message: 'Connection refused' }),
          text: () => Promise.resolve(''),
        } as Response);
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockNodes),
        text: () => Promise.resolve(''),
      } as Response);
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Node Alpha')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText('Add Node'));
    await userEvent.type(screen.getByPlaceholderText('e.g. 192.168.1.100'), '10.0.0.5');
    await userEvent.type(screen.getByPlaceholderText('Node display name'), 'New');

    await userEvent.click(screen.getByRole('button', { name: /Connect/i }));

    await waitFor(() => {
      expect(screen.getByText('Connection refused')).toBeInTheDocument();
    });
  });
});