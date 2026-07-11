import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import NodesPage from '../NodesPage';

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
              { name: 'AL01_192-168-1-10_102.fbc', type: 'file', section_type: 'FBC', token_id: '102', line_count: 50, file_name: 'AL01_192-168-1-10_102.fbc', file_path: '/tmp/logs/AL01m/FBC/test.fbc' },
            ],
          },
        ],
      },
    ],
  },
  path: '/tmp/logs',
  count: 1,
};

function mockFetchImpl(url: any, options?: any) {
  if (url?.includes('/nodesconfig/tree')) {
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(mockTree), text: () => Promise.resolve('') } as Response);
  }
  if (url?.includes('/commandqueue/status')) {
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ current: 0, total: 0, state: 'idle', commands: [] }), text: () => Promise.resolve('') } as Response);
  }
  if (url?.includes('/settings')) {
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ settings: { lis_mode: 'rsu' } }), text: () => Promise.resolve('') } as Response);
  }
  if (url?.includes('/logs/setroot')) {
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}), text: () => Promise.resolve('') } as Response);
  }
  if (url?.includes('/nodesconfig/create-structure') && options?.method === 'POST') {
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ created_dirs: 10, created_files: 5, log_root: '/tmp/logs' }), text: () => Promise.resolve('') } as Response);
  }
  if (url?.includes('/sysfiles/scan-nodes') && options?.method === 'POST') {
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ configs: [], structure_raw: '' }), text: () => Promise.resolve('') } as Response);
  }
  if (url?.includes('/parse/sysfile') && options?.method === 'POST') {
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ configs: [] }), text: () => Promise.resolve('') } as Response);
  }
  if (url?.includes('/nodes/') && url?.includes('/scan') && options?.method === 'POST') {
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ node_address: '192.168.1.10', scanned_at: '2025-01-01T11:00:00Z', fbc_modules: [], rpc_modules: [], io_points_total: 0 }), text: () => Promise.resolve('') } as Response);
  }
  if (url?.includes('/nodesconfig') && options?.method === 'POST') {
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}), text: () => Promise.resolve('') } as Response);
  }
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}), text: () => Promise.resolve('') } as Response);
}

function renderComponent() {
  return render(
    <MemoryRouter>
      <NodesPage />
    </MemoryRouter>,
  );
}

describe('NodesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn(mockFetchImpl) as any;
  });

  it('renders Nodes title', async () => {
    renderComponent();
    expect(screen.getByText('Nodes')).toBeInTheDocument();
  });

  it('renders active project name', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText(/T6004.*ADORA/)).toBeInTheDocument();
    });
  });

  it('renders Scan Nodes button', async () => {
    renderComponent();
    expect(screen.getByText('Scan Nodes')).toBeInTheDocument();
  });

  it('renders Open File button', async () => {
    renderComponent();
    expect(screen.getByText('Open File')).toBeInTheDocument();
  });

  it('renders Import button', async () => {
    renderComponent();
    expect(screen.getByText('Import')).toBeInTheDocument();
  });

  it('renders Add Node button', async () => {
    renderComponent();
    expect(screen.getByText('Add Node')).toBeInTheDocument();
  });

  it('renders Save Changes button', async () => {
    renderComponent();
    expect(screen.getByText('Save Changes')).toBeInTheDocument();
  });

  it('renders Clear Nodes button', async () => {
    renderComponent();
    expect(screen.getByText('Clear Nodes')).toBeInTheDocument();
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

  it('renders tree nodes from API', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('AL01m')).toBeInTheDocument();
    });
  });

  it('scan nodes calls POST /sysfiles/scan-nodes', async () => {
    renderComponent();
    const scanBtn = screen.getByText('Scan Nodes');
    await userEvent.click(scanBtn);
    await waitFor(() => {
      const scanCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => typeof c[0] === 'string' && c[0].includes('/sysfiles/scan-nodes') && (c[1] as any)?.method === 'POST',
      );
      expect(scanCalls.length).toBeGreaterThan(0);
    });
  });

  it('log root sync calls /logs/setroot on mount', async () => {
    renderComponent();
    await waitFor(() => {
      const setRootCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => typeof c[0] === 'string' && c[0].includes('/logs/setroot'),
      );
      expect(setRootCalls.length).toBeGreaterThan(0);
    });
  });

  it('shows Create Structure button in tree toolbar', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Create Structure')).toBeInTheDocument();
    });
  });

  it('create structure calls POST /nodesconfig/create-structure', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Create Structure')).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText('Create Structure'));
    await waitFor(() => {
      const createCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => typeof c[0] === 'string' && c[0].includes('/nodesconfig/create-structure') && (c[1] as any)?.method === 'POST',
      );
      expect(createCalls.length).toBeGreaterThan(0);
    });
  });

  it('shows context menu with file management on right-click of file', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('AL01m')).toBeInTheDocument();
    });
    const fileEl = screen.getByText('AL01_192-168-1-10_102.fbc');
    await userEvent.pointer({ keys: '[MouseRight]', target: fileEl });
    await waitFor(() => {
      // In nodes context, file management options appear
      expect(screen.getByText('Open File Content')).toBeInTheDocument();
      expect(screen.getByText('Delete File')).toBeInTheDocument();
    });
  });

  it('shows context menu with folder creation on right-click of node', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('AL01m')).toBeInTheDocument();
    });
    const nodeEl = screen.getByText('AL01m');
    await userEvent.pointer({ keys: '[MouseRight]', target: nodeEl });
    await waitFor(() => {
      expect(screen.getByText(/Create New Folder/)).toBeInTheDocument();
      expect(screen.getByText(/Create New File/)).toBeInTheDocument();
    });
  });

  it('renders No commands queued in queue bar when idle', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText(/No commands queued/i)).toBeInTheDocument();
    });
  });
});