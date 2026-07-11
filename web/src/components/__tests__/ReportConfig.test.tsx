import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ReportConfig from '../ReportConfig';

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
      last_connected: '',
      created_at: '',
      updated_at: '',
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
      created_at: '',
      updated_at: '',
    },
  ],
  total: 2,
  limit: 100,
  offset: 0,
};

function mockNodesAndReport() {
  vi.mocked(global.fetch).mockImplementation((url: any, options?: any) => {
    if (options?.method === 'POST' && url === '/api/v1/reports/generate') {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          report_id: 'rpt-new-123',
          status: 'pending',
          format: 'docx',
          template: 'default',
          node_addresses: ['192.168.1.10'],
          created_at: '2025-01-01T13:00:00Z',
        }),
        text: () => Promise.resolve(''),
      } as Response);
    }
    if (url === '/api/v1/nodes') {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockNodes),
        text: () => Promise.resolve(''),
      } as Response);
    }
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
      text: () => Promise.resolve(''),
    } as Response);
  });
}

function renderComponent(
  onSuccess = vi.fn(),
  onCancel = vi.fn(),
) {
  return render(
    <ReportConfig onSuccess={onSuccess} onCancel={onCancel} />,
  );
}

describe('ReportConfig', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    mockNodesAndReport();
    renderComponent();
    expect(screen.getByRole('heading', { name: 'Generate Report' })).toBeInTheDocument();
  });

  it('fetches /api/v1/nodes on mount', async () => {
    mockNodesAndReport();
    renderComponent();

    await waitFor(() => {
      expect(
        vi.mocked(global.fetch).mock.calls.some((c) => c[0] === '/api/v1/nodes'),
      ).toBe(true);
    });
  });

  it('shows Loading nodes... while fetching nodes', () => {
    vi.mocked(global.fetch).mockReturnValue(new Promise(() => {}));
    renderComponent();
    expect(screen.getByText('Loading nodes...')).toBeInTheDocument();
  });

  it('shows node dropdown with nodes after successful fetch', async () => {
    mockNodesAndReport();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Select a node...')).toBeInTheDocument();
    });
    // Select a node to see options
    const select = screen.getAllByRole('combobox')[1];
    expect(select).toBeInTheDocument();
  });

  it('shows format radio buttons for docx and json', async () => {
    mockNodesAndReport();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText(/docx/i)).toBeInTheDocument();
      expect(screen.getByText(/json/i)).toBeInTheDocument();
    });
  });

  it('shows template, title, and author optional fields', async () => {
    mockNodesAndReport();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Template (optional)')).toBeInTheDocument();
      expect(screen.getByText('Title (optional)')).toBeInTheDocument();
      expect(screen.getByText('Author (optional)')).toBeInTheDocument();
    });
  });

  it('shows Cancel and Generate Report buttons', async () => {
    mockNodesAndReport();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: 'Generate Report' })).toBeInTheDocument();
  });

  it('calls onCancel when Cancel is clicked', async () => {
    mockNodesAndReport();
    const onCancel = vi.fn();
    renderComponent(vi.fn(), onCancel);

    await waitFor(() => {
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText('Cancel'));
    expect(onCancel).toHaveBeenCalled();
  });

  it('shows node error when node fetch fails', async () => {
    vi.mocked(global.fetch).mockRejectedValue(new Error('Failed to load nodes'));
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Failed to load nodes')).toBeInTheDocument();
    });
  });

  it('validates that node is required', async () => {
    mockNodesAndReport();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Select a node...')).toBeInTheDocument();
    });

    // Submit without selecting a node
    await userEvent.click(screen.getByRole('button', { name: 'Generate Report' }));

    await waitFor(() => {
      expect(screen.getByText('Node is required')).toBeInTheDocument();
    });
  });

  it('submits report generation with correct body and calls onSuccess', async () => {
    mockNodesAndReport();
    const onSuccess = vi.fn();
    renderComponent(onSuccess);

    await waitFor(() => {
      expect(screen.getByText('Select a node...')).toBeInTheDocument();
    });

    // Select a node
    const select = screen.getAllByRole('combobox')[1];
    await userEvent.selectOptions(select, '192.168.1.10');

    // Submit
    await userEvent.click(screen.getByRole('button', { name: 'Generate Report' }));

    await waitFor(() => {
      const generateCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => c[0] === '/api/v1/reports/generate' && c[1]?.method === 'POST',
      );
      expect(generateCalls.length).toBe(1);
    });

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith('rpt-new-123');
    });
  });

  it('shows Generating... during submission', async () => {
    let resolvePost: (value: any) => void;
    vi.mocked(global.fetch).mockImplementation((url: any, options?: any) => {
      if (options?.method === 'POST' && url === '/api/v1/reports/generate') {
        return new Promise((resolve) => {
          resolvePost = resolve;
        }) as Promise<Response>;
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
      expect(screen.getByText('Select a node...')).toBeInTheDocument();
    });

    const select = screen.getAllByRole('combobox')[1];
    await userEvent.selectOptions(select, '192.168.1.10');

    await userEvent.click(screen.getByRole('button', { name: 'Generate Report' }));

    await waitFor(() => {
      expect(screen.getByText('Generating...')).toBeInTheDocument();
    });

    resolvePost!({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ report_id: 'rpt-x', status: 'pending', format: 'docx', template: '', node_addresses: [], created_at: '' }),
      text: () => Promise.resolve(''),
    } as Response);
  });

  it('shows submit error when report generation fails', async () => {
    vi.mocked(global.fetch).mockImplementation((url: any, options?: any) => {
      if (options?.method === 'POST' && url === '/api/v1/reports/generate') {
        return Promise.resolve({
          ok: false,
          status: 500,
          json: () => Promise.resolve({ message: 'Generation failed' }),
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
      expect(screen.getByText('Select a node...')).toBeInTheDocument();
    });

    const select = screen.getAllByRole('combobox')[1];
    await userEvent.selectOptions(select, '192.168.1.10');

    await userEvent.click(screen.getByRole('button', { name: 'Generate Report' }));

    await waitFor(() => {
      expect(screen.getByText('Generation failed')).toBeInTheDocument();
    });
  });

  it('disables Generate Report button when no nodes available', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ nodes: [], total: 0, limit: 100, offset: 0 }),
      text: () => Promise.resolve(''),
    } as Response);

    renderComponent();

    await waitFor(() => {
      const btn = screen.getByRole('button', { name: 'Generate Report' });
      expect(btn).toBeDisabled();
    });
  });
});