import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import NodeTree from '../NodeTree';
import type { TreeNodeData } from '../../types/api';

vi.mock('../../hooks/useActiveProject', () => ({
  useActiveProject: () => ({
    activeProjectId: 1,
    activeLogRoot: '/tmp/logs',
    selectProject: vi.fn(),
    selectLogRoot: vi.fn(),
  }),
}));

const mockTree: TreeNodeData = {
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
            { name: 'AL01_192-168-1-10_103.fbc', type: 'file', section_type: 'FBC', token_id: '103', line_count: 0, file_name: 'AL01_192-168-1-10_103.fbc', file_path: '/tmp/logs/AL01m/FBC/empty.fbc' },
            { name: 'AL01_192-168-1-10_104.fbc', type: 'file', section_type: 'FBC', token_id: '104', line_count: 5, file_name: 'AL01_192-168-1-10_104.fbc', file_path: '/tmp/logs/AL01m/FBC/low.fbc' },
            { name: 'token_105', type: 'token', section_type: 'FBC', token_id: '105' },
          ],
        },
        {
          name: 'RPC',
          type: 'group',
          section_type: 'RPC',
          children: [
            { name: 'AL01_192-168-1-10_201.rpc', type: 'file', section_type: 'RPC', token_id: '201', line_count: 20, file_name: 'AL01_192-168-1-10_201.rpc', file_path: '/tmp/logs/AL01m/RPC/test.rpc' },
          ],
        },
        {
          name: 'LOG',
          type: 'group',
          section_type: 'LOG',
          children: [
            { name: 'AL01_192-168-1-10_errlog.log', type: 'file', section_type: 'LOG', token_id: 'errlog', line_count: 15, file_name: 'AL01_192-168-1-10_errlog.log', file_path: '/tmp/logs/AL01m/LOG/test.log' },
          ],
        },
        {
          name: 'LIS',
          type: 'group',
          section_type: 'LIS',
          children: [
            { name: 'AL01_192-168-1-10_301_exe1.lis', type: 'file', section_type: 'LIS', token_id: '301', line_count: 10, file_name: 'AL01_192-168-1-10_301_exe1.lis', file_path: '/tmp/logs/AL01m/LIS/test.lis' },
          ],
        },
      ],
    },
  ],
};

const mockQueueStatus = {
  current: 0,
  total: 0,
  state: 'idle',
  commands: [],
};

function mockFetchImpl(url: any) {
  if (url?.includes('/nodesconfig/tree')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ tree: mockTree, path: '/tmp/logs', count: 1 }),
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

const mockHandlers = {
  onSelectNode: vi.fn(),
  onSelectToken: vi.fn(),
  onContextAction: vi.fn(),
  onDoubleClickFile: vi.fn(),
};

function renderComponent(props: Partial<Parameters<typeof NodeTree>[0]> = {}) {
  return render(
    <NodeTree
      onSelectNode={mockHandlers.onSelectNode}
      onSelectToken={mockHandlers.onSelectToken}
      onContextAction={mockHandlers.onContextAction}
      onDoubleClickFile={mockHandlers.onDoubleClickFile}
      projectId={1}
      context="commander"
      {...props}
    />,
  );
}

describe('NodeTree', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn(mockFetchImpl) as any;
  });

  it('renders tree from API data', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('AL01m')).toBeInTheDocument();
    });
  });

  it('renders Refresh button', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });
  });

  it('renders Create Structure button when onCreateStructure provided', async () => {
    renderComponent({ onCreateStructure: vi.fn() });
    await waitFor(() => {
      expect(screen.getByText('Create Structure')).toBeInTheDocument();
    });
  });

  it('shows file with green color for line_count >= 10', async () => {
    const { container } = renderComponent();
    await waitFor(() => {
      expect(screen.getByText('AL01m')).toBeInTheDocument();
    });
    // The file with line_count=50 should have green color (var(--success))
    const fileElements = container.querySelectorAll('[style*="var(--success)"]');
    expect(fileElements.length).toBeGreaterThan(0);
  });

  it('shows file with red color for line_count = 0', async () => {
    const { container } = renderComponent();
    await waitFor(() => {
      expect(screen.getByText('AL01m')).toBeInTheDocument();
    });
    // The file with line_count=0 should have red color (var(--error))
    const errorElements = container.querySelectorAll('[style*="var(--error)"]');
    expect(errorElements.length).toBeGreaterThan(0);
  });

  it('shows file with yellow color for line_count < 10', async () => {
    const { container } = renderComponent();
    await waitFor(() => {
      expect(screen.getByText('AL01m')).toBeInTheDocument();
    });
    // The file with line_count=5 should have yellow color (#f59e0b)
    // Check the span element that has the file name text with the color
    const allSpans = container.querySelectorAll('span');
    const yellowFound = Array.from(allSpans).some(el => {
      const style = el.getAttribute('style') || '';
      return style.includes('#f59e0b') || style.includes('f59e0b');
    });
    expect(yellowFound).toBe(true);
  });

  it('shows token (missing file) with muted/gray color', async () => {
    const { container } = renderComponent();
    await waitFor(() => {
      expect(screen.getByText('AL01m')).toBeInTheDocument();
    });
    // Token type should have var(--text-muted) color
    const mutedElements = container.querySelectorAll('[style*="var(--text-muted)"]');
    expect(mutedElements.length).toBeGreaterThan(0);
  });

  it('shows line count annotation on file nodes', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('[50L]')).toBeInTheDocument();
    });
    expect(screen.getByText('[0L]')).toBeInTheDocument();
  });

  it('expands/collapses tree nodes on click', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('AL01m')).toBeInTheDocument();
    });
    // FBC group should be visible (auto-expanded)
    expect(screen.getByText('FBC')).toBeInTheDocument();
    // Click FBC to collapse
    await userEvent.click(screen.getByText('FBC'));
    // Click again to expand
    await userEvent.click(screen.getByText('FBC'));
    expect(screen.getByText('FBC')).toBeInTheDocument();
  });

  it('calls onSelectNode when a node is clicked', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('AL01m')).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText('AL01m'));
    expect(mockHandlers.onSelectNode).toHaveBeenCalled();
  });

  it('shows context menu with FBC print option on right-click of FBC file', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('AL01m')).toBeInTheDocument();
    });
    const fileEl = screen.getByText('AL01_192-168-1-10_102.fbc');
    await userEvent.pointer({ keys: '[MouseRight]', target: fileEl });
    await waitFor(() => {
      expect(screen.getByText(/Print FieldBus Structure/)).toBeInTheDocument();
    });
  });

  it('context menu shows RPC print option for RPC files', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('AL01m')).toBeInTheDocument();
    });
    // Expand RPC group
    const fileEl = screen.getByText('AL01_192-168-1-10_201.rpc');
    await userEvent.pointer({ keys: '[MouseRight]', target: fileEl });
    await waitFor(() => {
      expect(screen.getByText(/Print Rupi counters/)).toBeInTheDocument();
    });
  });

  it('context menu shows BsTool option for LOG files', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('AL01m')).toBeInTheDocument();
    });
    const fileEl = screen.getByText('AL01_192-168-1-10_errlog.log');
    await userEvent.pointer({ keys: '[MouseRight]', target: fileEl });
    await waitFor(() => {
      expect(screen.getByText(/Run BsTool/)).toBeInTheDocument();
    });
  });

  it('context menu shows LisDiag/RSU option for LIS files', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('AL01m')).toBeInTheDocument();
    });
    const fileEl = screen.getByText('AL01_192-168-1-10_301_exe1.lis');
    await userEvent.pointer({ keys: '[MouseRight]', target: fileEl });
    await waitFor(() => {
      // In rsu mode, shows RSU trace option
      expect(screen.getByText(/RSU Trace/)).toBeInTheDocument();
    });
  });

  it('context menu shows file management options (Open, Erase)', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('AL01m')).toBeInTheDocument();
    });
    const fileEl = screen.getByText('AL01_192-168-1-10_102.fbc');
    await userEvent.pointer({ keys: '[MouseRight]', target: fileEl });
    await waitFor(() => {
      expect(screen.getByText('Open File Content')).toBeInTheDocument();
      expect(screen.getByText('Erase File Content')).toBeInTheDocument();
    });
  });

  it('context menu shows node-level print all options', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('AL01m')).toBeInTheDocument();
    });
    const nodeEl = screen.getByText('AL01m');
    await userEvent.pointer({ keys: '[MouseRight]', target: nodeEl });
    await waitFor(() => {
      expect(screen.getByText(/Execute All Print Commands/)).toBeInTheDocument();
      expect(screen.getByText(/Print All FBC Tokens/)).toBeInTheDocument();
      expect(screen.getByText(/Print All RPC Tokens/)).toBeInTheDocument();
    });
  });
});