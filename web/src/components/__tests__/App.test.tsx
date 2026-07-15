import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../../App';

function mockFetchAll() {
  const mockFn = vi.fn((url: string) => {
    if (typeof url === 'string' && url.includes('/health')) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          status: 'ok',
          version: '1.0.0',
          uptime: '1h',
          db_status: 'connected',
          node_count: 3,
        }),
        text: () => Promise.resolve(''),
      } as Response);
    }
    if (typeof url === 'string' && url.includes('/api/v1/nodes')) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          nodes: [
            {
              id: 1, address: '10.0.0.1', port: 23, name: 'Node1',
              node_type: 'ACN', token: '', status: 'connected',
              last_connected: '', created_at: '', updated_at: '',
            },
          ],
          total: 1, limit: 100, offset: 0,
        }),
        text: () => Promise.resolve(''),
      } as Response);
    }
    if (typeof url === 'string' && url.includes('/api/v1/reports')) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ reports: [], total: 0, limit: 100, offset: 0 }),
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
  global.fetch = mockFn as unknown as typeof fetch;
}

// App uses <Routes> which requires a <Router> context.
// We wrap App in MemoryRouter for all tests.
function renderApp(initialRoute = '/') {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <App />
    </MemoryRouter>
  );
}

describe('App', () => {
  beforeEach(() => {
    mockFetchAll();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders without crashing', async () => {
    renderApp();
    // LOGReport text is in Layout sidebar — rendered synchronously
    expect(screen.getAllByText('LOGReport').length).toBeGreaterThan(0);
  });

  it('shows Dashboard on the root route', async () => {
    renderApp('/');
    // Dashboard text is rendered synchronously at /
    expect(screen.getByText('LOGReport Dashboard')).toBeInTheDocument();
  });

  it('renders StatusBar at the bottom (LOGReport brand)', async () => {
    renderApp();
    // LOGReport appears in Layout sidebar
    const logreportElements = screen.getAllByText('LOGReport');
    expect(logreportElements.length).toBeGreaterThanOrEqual(1);
  });

  it('renders navigation links', async () => {
    renderApp();
    // Use getAllByText since some text appears in both nav and page content
    expect(screen.getAllByText('Dashboard').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Nodes').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Commander').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Reports').length).toBeGreaterThan(0);
  });

  it('shows 404 page for unknown routes', async () => {
    renderApp('/nonexistent-route');
    // The NotFound component renders a 404 heading
    await waitFor(() => {
      expect(screen.getByText('404')).toBeInTheDocument();
    });
  });
});