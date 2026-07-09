import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import ReportList from '../ReportList';

const mockReports = {
  reports: [
    {
      report_id: 'rpt-001',
      status: 'completed',
      format: 'docx',
      template: 'default',
      node_addresses: ['192.168.1.10'],
      file_path: '/reports/rpt-001.docx',
      file_size: 45678,
      created_at: '2025-01-01T10:00:00Z',
      completed_at: '2025-01-01T10:05:00Z',
    },
    {
      report_id: 'rpt-002',
      status: 'pending',
      format: 'json',
      template: '',
      node_addresses: ['192.168.1.20'],
      created_at: '2025-01-01T11:00:00Z',
    },
    {
      report_id: 'rpt-003',
      status: 'failed',
      format: 'json',
      template: '',
      node_addresses: ['192.168.1.30'],
      created_at: '2025-01-01T12:00:00Z',
      error_message: 'Node unreachable',
    },
  ],
  total: 3,
  limit: 100,
  offset: 0,
};

function mockFetchSuccess(data = mockReports) {
  vi.mocked(global.fetch).mockImplementation((url: any, options?: any) => {
    if (options?.method === 'POST') {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          report_id: 'rpt-new',
          status: 'pending',
          format: 'docx',
          template: 'default',
          node_addresses: ['10.0.0.1'],
          created_at: '2025-01-01T13:00:00Z',
        }),
        text: () => Promise.resolve(''),
      } as Response);
    }
    // GET /api/v1/nodes for ReportConfig dropdown
    if (url === '/api/v1/nodes') {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          nodes: [
            {
              id: 1,
              address: '10.0.0.1',
              port: 23,
              name: 'Node1',
              node_type: 'ACN',
              token: '',
              status: 'connected',
              last_connected: '',
              created_at: '',
              updated_at: '',
            },
          ],
          total: 1,
          limit: 100,
          offset: 0,
        }),
        text: () => Promise.resolve(''),
      } as Response);
    }
    // GET /api/v1/reports
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(data),
      text: () => Promise.resolve(''),
    } as Response);
  });
}

function renderComponent() {
  return render(
    <MemoryRouter>
      <ReportList />
    </MemoryRouter>,
  );
}

describe('ReportList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    mockFetchSuccess();
    renderComponent();
    expect(screen.getByText('Reports')).toBeInTheDocument();
  });

  it('shows loading state on mount', () => {
    vi.mocked(global.fetch).mockReturnValue(new Promise(() => {}));
    renderComponent();
    expect(screen.getByText('Loading reports...')).toBeInTheDocument();
  });

  it('fetches /api/v1/reports on mount', async () => {
    mockFetchSuccess();
    renderComponent();

    await waitFor(() => {
      expect(
        vi.mocked(global.fetch).mock.calls.some((c) => c[0] === '/api/v1/reports'),
      ).toBe(true);
    });
  });

  it('displays reports after successful fetch', async () => {
    mockFetchSuccess();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('rpt-001')).toBeInTheDocument();
    });
    expect(screen.getByText('rpt-002')).toBeInTheDocument();
    expect(screen.getByText('rpt-003')).toBeInTheDocument();
  });

  it('shows status badges for reports', async () => {
    mockFetchSuccess();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Completed')).toBeInTheDocument();
    });
    expect(screen.getByText('Pending')).toBeInTheDocument();
    expect(screen.getByText('Failed')).toBeInTheDocument();
  });

  it('shows format labels', async () => {
    mockFetchSuccess();
    renderComponent();

    await waitFor(() => {
      expect(screen.getAllByText('docx').length).toBeGreaterThan(0);
      expect(screen.getAllByText('json').length).toBeGreaterThan(0);
    });
  });

  it('displays node addresses in report cards', async () => {
    mockFetchSuccess();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('192.168.1.10')).toBeInTheDocument();
    });
  });

  it('shows empty state when no reports are returned', async () => {
    mockFetchSuccess({ reports: [], total: 0, limit: 100, offset: 0 });
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('No reports generated. Create your first report to get started.')).toBeInTheDocument();
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

  it('renders Generate New Report button', async () => {
    mockFetchSuccess();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Generate New Report')).toBeInTheDocument();
    });
  });

  it('opens ReportConfig modal when Generate New Report is clicked', async () => {
    mockFetchSuccess();
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('rpt-001')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText('Generate New Report'));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Generate New Report/i })).toBeInTheDocument();
    });
  });
});