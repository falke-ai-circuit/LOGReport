import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import StatusBar from '../StatusBar';

const healthData = {
  status: 'ok',
  version: '1.2.3',
  uptime: '5h30m',
  db_status: 'connected',
  node_count: 7,
};

describe('StatusBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(<StatusBar />);
    expect(screen.getByText('LOGReport')).toBeInTheDocument();
  });

  it('shows "Connecting..." before fetch resolves', () => {
    // Make fetch return a pending promise so it never resolves
    vi.mocked(global.fetch).mockReturnValueOnce(new Promise(() => {}));

    render(<StatusBar />);
    expect(screen.getByText('Connecting...')).toBeInTheDocument();
  });

  it('fetches /health on mount', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(healthData),
    } as Response);

    render(<StatusBar />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/health');
    });
  });

  it('shows Connected status when fetch succeeds', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(healthData),
    } as Response);

    render(<StatusBar />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });
  });

  it('displays version, uptime, db_status, and node_count after successful fetch', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(healthData),
    } as Response);

    render(<StatusBar />);

    await waitFor(() => {
      expect(screen.getByText('v1.2.3')).toBeInTheDocument();
    });
    expect(screen.getByText('5h30m')).toBeInTheDocument();
    expect(screen.getByText('connected')).toBeInTheDocument();
    expect(screen.getByText('Nodes: 7')).toBeInTheDocument();
  });

  it('shows Offline status when fetch fails', async () => {
    vi.mocked(global.fetch).mockRejectedValueOnce(new Error('Network error'));

    render(<StatusBar />);

    await waitFor(() => {
      expect(screen.getByText(/Offline/)).toBeInTheDocument();
    });
  });

  it('shows Offline status when response is not ok', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.resolve({}),
    } as Response);

    render(<StatusBar />);

    await waitFor(() => {
      expect(screen.getByText(/Offline/)).toBeInTheDocument();
    });
  });

  it('does not display health info before fetch resolves', () => {
    vi.mocked(global.fetch).mockReturnValueOnce(new Promise(() => {}));

    render(<StatusBar />);

    expect(screen.queryByText('v1.2.3')).not.toBeInTheDocument();
    expect(screen.queryByText('Nodes: 7')).not.toBeInTheDocument();
  });
});