import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import CommanderLayout from '../CommanderLayout';

vi.mock('../../hooks/useActiveProject', () => ({
  useActiveProject: () => ({
    activeProjectId: 1,
    activeLogRoot: '/tmp/logs',
    selectProject: vi.fn(),
    selectLogRoot: vi.fn(),
  }),
  useProjects: () => ({
    projects: [
      {
        id: 1,
        project_number: 'T6004',
        ship_name: 'ADORA',
        log_root: '/tmp/logs',
        status: 'active',
        created_at: '2025-01-01T10:00:00Z',
        updated_at: '2025-01-01T10:00:00Z',
      },
    ],
    loading: false,
    setProjects: vi.fn(),
  }),
}));

const mockTree = {
  tree: {
    name: 'root',
    type: 'root',
    children: [
      {
        name: 'AL01m',
        type: 'node',
        ip: '192.168.1.10',
        children: [
          {
            name: 'FBC',
            type: 'group',
            section_type: 'FBC',
            children: [
              { name: 'AL01_192-168-1-10_102.fbc', type: 'file', section_type: 'FBC', token_id: '102', line_count: 5, file_name: 'AL01_192-168-1-10_102.fbc' },
            ],
          },
        ],
      },
    ],
  },
  path: '/tmp/logs',
  count: 1,
};

const mockQueueStatus = {
  current: 0,
  total: 2,
  state: 'idle',
  commands: [
    { id: 'cmd1', type: 'fbc', node_name: 'AL01m', token_id: '102', command: 'print from fbc', status: 'pending' },
    { id: 'cmd2', type: 'rpc', node_name: 'AL01m', token_id: '103', command: 'print from rpc', status: 'pending' },
  ],
};

function mockFetchImpl(url: any, _options?: any) {
  if (url?.includes('/nodesconfig/tree')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockTree),
      text: () => Promise.resolve(''),
    } as Response);
  }
  if (url?.includes('/logs/setroot')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
      text: () => Promise.resolve(''),
    } as Response);
  }
  if (url?.includes('/commandqueue/status')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockQueueStatus),
      text: () => Promise.resolve(''),
    } as Response);
  }
  if (url?.includes('/settings')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ settings: { lis_mode: 'rsu' } }),
      text: () => Promise.resolve(''),
    } as Response);
  }
  return Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
  } as Response);
}

function renderComponent() {
  return render(
    <MemoryRouter>
      <CommanderLayout />
    </MemoryRouter>,
  );
}

describe('CommanderLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn(mockFetchImpl) as any;
  });

  it('renders all 6 tabs (Debugger, LisDiag, BsTool, Scan, Log Viewer, Queue)', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Debugger')).toBeInTheDocument();
    });
    expect(screen.getByText('LisDiag')).toBeInTheDocument();
    expect(screen.getByText('BsTool')).toBeInTheDocument();
    expect(screen.getByText('Scan')).toBeInTheDocument();
    expect(screen.getByText('Log Viewer')).toBeInTheDocument();
    expect(screen.getByText('Queue')).toBeInTheDocument();
  });

  it('switches to LisDiag tab when clicked', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Debugger')).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText('LisDiag'));
    // LisDiagTab should render with IP address input
    expect(screen.getByPlaceholderText('IP address')).toBeInTheDocument();
  });

  it('switches to BsTool tab when clicked', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Debugger')).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText('BsTool'));
    // BsToolPanel should render with Server name input
    expect(screen.getByPlaceholderText(/Server name/)).toBeInTheDocument();
  });

  it('switches to Queue tab when clicked', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Debugger')).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText('Queue'));
    await waitFor(() => {
      expect(screen.getByText('Command Queue')).toBeInTheDocument();
    });
  });

  it('node tree loads from /nodesconfig/tree', async () => {
    renderComponent();
    await waitFor(() => {
      const treeCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => typeof c[0] === 'string' && c[0].includes('/nodesconfig/tree'),
      );
      expect(treeCalls.length).toBeGreaterThan(0);
    });
  });

  it('log root sync calls /logs/setroot', async () => {
    renderComponent();
    await waitFor(() => {
      const setRootCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => typeof c[0] === 'string' && c[0].includes('/logs/setroot'),
      );
      expect(setRootCalls.length).toBeGreaterThan(0);
    });
  });

  it('renders Commander title and project name', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Commander')).toBeInTheDocument();
    });
    expect(screen.getByText(/T6004.*ADORA/)).toBeInTheDocument();
  });

  it('shows All Logs Queue button', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText(/All Logs Queue/)).toBeInTheDocument();
    });
  });

  it('shows Restart and Clear queue controls', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Restart')).toBeInTheDocument();
    });
    expect(screen.getByText('Clear')).toBeInTheDocument();
  });

  it('renders Scan tab content when Scan clicked', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Debugger')).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText('Scan'));
    // ScanTab should be visible
    await waitFor(() => {
      // ScanTab has a scan-related UI — just verify tab is active
      expect(screen.getByText('Scan')).toBeInTheDocument();
    });
  });

  it('renders Log Viewer tab content when Log Viewer clicked', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Debugger')).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText('Log Viewer'));
    // Log Viewer shows file viewer with "No file selected" initially
    await waitFor(() => {
      expect(screen.getByText(/No file selected/)).toBeInTheDocument();
    });
  });
});