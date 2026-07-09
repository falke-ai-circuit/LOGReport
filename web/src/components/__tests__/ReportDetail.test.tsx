import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ReportDetail from '../ReportDetail';

const completedReport = {
  report_id: 'rpt-001',
  status: 'completed',
  format: 'docx',
  template: 'default',
  node_addresses: ['192.168.1.10'],
  file_path: '/reports/rpt-001.docx',
  file_size: 45678,
  created_at: '2025-01-01T10:00:00Z',
  completed_at: '2025-01-01T10:05:00Z',
};

const pendingReport = {
  report_id: 'rpt-002',
  status: 'pending',
  format: 'json',
  template: '',
  node_addresses: ['192.168.1.20'],
  created_at: '2025-01-01T11:00:00Z',
};

const failedReport = {
  report_id: 'rpt-003',
  status: 'failed',
  format: 'json',
  template: '',
  node_addresses: ['192.168.1.30'],
  created_at: '2025-01-01T12:00:00Z',
  error_message: 'Node unreachable',
};

function renderComponent(id = 'rpt-001') {
  return render(
    <MemoryRouter initialEntries={[`/reports/${id}`]}>
      <Routes>
        <Route path="/reports/:id" element={<ReportDetail />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('ReportDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state on mount', () => {
    vi.mocked(global.fetch).mockReturnValue(new Promise(() => {}));
    renderComponent();
    expect(screen.getByText('Loading report...')).toBeInTheDocument();
  });

  it('fetches /api/v1/reports/:id on mount', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(completedReport),
      text: () => Promise.resolve(''),
      headers: { get: () => 'application/octet-stream' },
    } as any);

    renderComponent('rpt-001');

    await waitFor(() => {
      expect(
        vi.mocked(global.fetch).mock.calls.some((c) => c[0] === '/api/v1/reports/rpt-001'),
      ).toBe(true);
    });
  });

  it('displays report detail after successful fetch', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(completedReport),
      text: () => Promise.resolve(''),
      headers: { get: () => null },
    } as any);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('rpt-001')).toBeInTheDocument();
    });
    expect(screen.getByText('192.168.1.10')).toBeInTheDocument();
    expect(screen.getAllByText(/docx/i).length).toBeGreaterThan(0);
  });

  it('shows Download button for completed reports', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(completedReport),
      text: () => Promise.resolve(''),
      headers: { get: () => null },
    } as any);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Download')).toBeInTheDocument();
    });
  });

  it('shows "Report is still being generated" for pending reports', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(pendingReport),
      text: () => Promise.resolve(''),
      headers: { get: () => null },
    } as any);

    renderComponent('rpt-002');

    await waitFor(() => {
      expect(screen.getByText('Report is still being generated. Check back shortly.')).toBeInTheDocument();
    });
  });

  it('shows error_message for failed reports', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(failedReport),
      text: () => Promise.resolve(''),
      headers: { get: () => null },
    } as any);

    renderComponent('rpt-003');

    await waitFor(() => {
      expect(screen.getByText('Node unreachable')).toBeInTheDocument();
    });
  });

  it('shows error state when fetch fails', async () => {
    vi.mocked(global.fetch).mockRejectedValue(new Error('Network error'));
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
    expect(screen.getByText('Back to Reports')).toBeInTheDocument();
  });

  it('shows error state when response is not ok', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ message: 'Report not found' }),
      text: () => Promise.resolve(''),
    } as any);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Report not found')).toBeInTheDocument();
    });
  });

  it('displays file size for completed reports with file_size', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(completedReport),
      text: () => Promise.resolve(''),
      headers: { get: () => null },
    } as any);

    renderComponent();

    await waitFor(() => {
      // 45678 bytes = 44.6 KB
      expect(screen.getByText('44.6 KB')).toBeInTheDocument();
    });
  });

  it('displays template name when present', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(completedReport),
      text: () => Promise.resolve(''),
      headers: { get: () => null },
    } as any);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('default')).toBeInTheDocument();
    });
  });

  it('shows Report Detail header', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(completedReport),
      text: () => Promise.resolve(''),
      headers: { get: () => null },
    } as any);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Report Detail')).toBeInTheDocument();
    });
  });

  it('shows Preview section for completed reports', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(completedReport),
      text: () => Promise.resolve(''),
      headers: { get: () => null },
    } as any);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Preview')).toBeInTheDocument();
    });
  });

  it('shows DOCX download message for completed docx reports', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(completedReport),
      text: () => Promise.resolve(''),
      headers: { get: () => null },
    } as any);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText(/DOCX reports cannot be previewed/)).toBeInTheDocument();
    });
    expect(screen.getByText('Download DOCX')).toBeInTheDocument();
  });
});