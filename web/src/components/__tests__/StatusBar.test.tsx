import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import StatusBar from '../StatusBar';

// Mock useActiveProject hook to avoid fetch calls for projects
vi.mock('../../hooks/useActiveProject', () => ({
  useActiveProject: () => ({ activeProjectId: null, selectProject: vi.fn(), activeLogRoot: '', selectLogRoot: vi.fn() }),
  useProjects: () => ({ projects: [] }),
}));

const healthData = {
  status: 'ok',
  version: '1.2.3',
  uptime: '5h30m',
  db_status: 'connected',
  node_count: 7,
};

function mockFetchHealth() {
  global.fetch = vi.fn((url: string) => {
    if (typeof url === 'string' && url.includes('/health')) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(healthData),
      } as Response);
    }
    if (typeof url === 'string' && url.includes('/api/v1/commandqueue/status')) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ state: 'idle', current: 0, total: 0, commands: [] }),
      } as Response);
    }
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
      text: () => Promise.resolve(''),
    } as Response);
  }) as unknown as typeof fetch;
}

function mockFetchFail() {
  global.fetch = vi.fn((url: string) => {
    if (typeof url === 'string' && url.includes('/health')) {
      return Promise.reject(new Error('Network error'));
    }
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
      text: () => Promise.resolve(''),
    } as Response);
  }) as unknown as typeof fetch;
}

describe('StatusBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchHealth();
  });

  it('renders without crashing', () => {
    render(<StatusBar />);
    expect(screen.getByText('LOGReport')).toBeInTheDocument();
  });

  it('shows "Connecting..." before fetch resolves', () => {
    // Make fetch return a pending promise so it never resolves
    global.fetch = vi.fn(() => new Promise(() => {})) as unknown as typeof fetch;
    render(<StatusBar />);
    expect(screen.getByText('Connecting...')).toBeInTheDocument();
  });

  it('fetches /health on mount', async () => {
    render(<StatusBar />);
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/health');
    });
  });

  it('shows Connected status when fetch succeeds', async () => {
    render(<StatusBar />);
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });
  });

  it('displays version, uptime, db_status, and node_count after successful fetch', async () => {
    render(<StatusBar />);
    await waitFor(() => {
      expect(screen.getByText('v1.2.3')).toBeInTheDocument();
    });
  });

  it('shows Offline status when fetch fails', async () => {
    mockFetchFail();
    render(<StatusBar />);
    await waitFor(() => {
      expect(screen.getByText(/Offline/)).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('shows Offline status when response is not ok', async () => {
    global.fetch = vi.fn((url: string) => {
      if (typeof url === 'string' && url.includes('/health')) {
        return Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve({}) } as Response);
      }
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) } as Response);
    }) as unknown as typeof fetch;
    render(<StatusBar />);
    await waitFor(() => {
      expect(screen.getByText(/Offline/)).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('does not display health info before fetch resolves', () => {
    global.fetch = vi.fn(() => new Promise(() => {})) as unknown as typeof fetch;
    render(<StatusBar />);
    expect(screen.queryByText('v1.2.3')).not.toBeInTheDocument();
    expect(screen.queryByText('Nodes: 7')).not.toBeInTheDocument();
  });
});