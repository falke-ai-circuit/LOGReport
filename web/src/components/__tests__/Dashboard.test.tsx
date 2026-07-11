import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import Dashboard from '../Dashboard';

const mockSelectProject = vi.fn();
const mockSelectLogRoot = vi.fn();

vi.mock('../../hooks/useActiveProject', () => ({
  useActiveProject: () => ({
    activeProjectId: 1,
    activeLogRoot: '/tmp/logs',
    selectProject: mockSelectProject,
    selectLogRoot: mockSelectLogRoot,
  }),
}));

const mockProjects = {
  projects: [
    {
      id: 1,
      project_number: 'T6004',
      ship_name: 'ADORA',
      log_root: 'C:\\dna\\CA\\bu',
      status: 'active',
      created_at: '2025-01-01T10:00:00Z',
      updated_at: '2025-01-01T10:00:00Z',
    },
    {
      id: 2,
      project_number: 'T7001',
      ship_name: 'BLUESTAR',
      log_root: 'C:\\dna\\CA\\bu2',
      status: 'active',
      created_at: '2025-02-01T10:00:00Z',
      updated_at: '2025-02-01T10:00:00Z',
    },
  ],
  total: 2,
};

const mockHealth = {
  status: 'ok',
  version: 'v3.9.43',
  uptime: '5h30m',
  db_status: 'healthy',
  node_count: 7,
};

function mockFetchImpl(url: any, options?: any) {
  if (url === '/api/v1/projects' && options?.method === 'POST') {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ id: 3, log_root: 'C:\\new\\path' }),
      text: () => Promise.resolve(''),
    } as Response);
  }
  if (url === '/api/v1/projects' && options?.method === 'DELETE') {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
      text: () => Promise.resolve(''),
    } as Response);
  }
  if (url?.startsWith('/api/v1/projects/') && options?.method === 'PUT') {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ project: { id: 1, log_root: 'C:\\new\\root' } }),
      text: () => Promise.resolve(''),
    } as Response);
  }
  if (url === '/api/v1/projects') {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockProjects),
      text: () => Promise.resolve(''),
    } as Response);
  }
  if (url === '/api/v1/health') {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockHealth),
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
      <Dashboard />
    </MemoryRouter>,
  );
}

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn(mockFetchImpl) as any;
  });

  it('renders projects from API', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText(/T6004.*ADORA/)).toBeInTheDocument();
    });
    expect(screen.getByText(/T7001.*BLUESTAR/)).toBeInTheDocument();
  });

  it('renders health status', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText(/v3\.9\.43/)).toBeInTheDocument();
    });
    expect(screen.getByText(/5h30m/)).toBeInTheDocument();
  });

  it('shows empty projects state', async () => {
    global.fetch = vi.fn((url: any) => {
      if (url === '/api/v1/projects') {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ projects: [], total: 0 }),
          text: () => Promise.resolve(''),
        } as Response);
      }
      return mockFetchImpl(url);
    }) as any;
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText(/No projects yet/)).toBeInTheDocument();
    });
  });

  it('opens create form when New Project clicked', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText(/T6004.*ADORA/)).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText(/New Project/));
    expect(screen.getByPlaceholderText('T6004')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('ADORA_MEDITERANNEA')).toBeInTheDocument();
  });

  it('create project validation - requires project number and ship name', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText(/T6004.*ADORA/)).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText(/New Project/));
    // Click Create without filling in required fields
    await userEvent.click(screen.getByText('Create'));
    expect(screen.getByText(/Project number and ship name are required/)).toBeInTheDocument();
  });

  it('creates project via POST /projects', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText(/T6004.*ADORA/)).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText(/New Project/));
    await userEvent.type(screen.getByPlaceholderText('T6004'), 'T9999');
    await userEvent.type(screen.getByPlaceholderText('ADORA_MEDITERANNEA'), 'NEWSHIP');
    await userEvent.click(screen.getByText('Create'));
    await waitFor(() => {
      const postCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => c[0] === '/api/v1/projects' && (c[1] as any)?.method === 'POST',
      );
      expect(postCalls.length).toBeGreaterThan(0);
    });
  });

  it('selects project and navigates to /nodes on card click', async () => {
    mockSelectProject.mockClear();
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText(/T6004.*ADORA/)).toBeInTheDocument();
    });
    // Click the project card — the ProjectCard div has cursor:pointer
    const projectText = screen.getByText(/T6004.*ADORA/);
    const card = projectText.closest('div');
    expect(card).toBeTruthy();
    await userEvent.click(card!);
    await waitFor(() => {
      expect(mockSelectProject).toHaveBeenCalled();
    });
  });

  it('opens edit dialog when Edit clicked', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText(/T6004.*ADORA/)).toBeInTheDocument();
    });
    const editButtons = screen.getAllByText('Edit');
    await userEvent.click(editButtons[0]);
    expect(screen.getByText(/Edit Project/)).toBeInTheDocument();
  });

  it('edit project saves via PUT /projects/{id}', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText(/T6004.*ADORA/)).toBeInTheDocument();
    });
    const editButtons = screen.getAllByText('Edit');
    await userEvent.click(editButtons[0]);
    // Change log root
    const logRootInput = screen.getByPlaceholderText('C:\\dna\\CA\\bu');
    await userEvent.clear(logRootInput);
    await userEvent.type(logRootInput, 'C:\\new\\root');
    // Click Save Changes
    await userEvent.click(screen.getByText('Save Changes'));
    await waitFor(() => {
      const putCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => typeof c[0] === 'string' && c[0].startsWith('/api/v1/projects/') && (c[1] as any)?.method === 'PUT',
      );
      expect(putCalls.length).toBeGreaterThan(0);
    });
  });

  it('deletes project via DELETE when confirmed', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText(/T6004.*ADORA/)).toBeInTheDocument();
    });
    const deleteButtons = screen.getAllByText('Delete');
    await userEvent.click(deleteButtons[0]);
    await waitFor(() => {
      const deleteCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => typeof c[0] === 'string' && c[0].startsWith('/api/v1/projects/') && (c[1] as any)?.method === 'DELETE',
      );
      expect(deleteCalls.length).toBeGreaterThan(0);
    });
    confirmSpy.mockRestore();
  });

  it('does not delete project when confirm is cancelled', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText(/T6004.*ADORA/)).toBeInTheDocument();
    });
    const deleteButtons = screen.getAllByText('Delete');
    await userEvent.click(deleteButtons[0]);
    const deleteCalls = vi.mocked(global.fetch).mock.calls.filter(
      (c) => typeof c[0] === 'string' && c[0].startsWith('/api/v1/projects/') && (c[1] as any)?.method === 'DELETE',
    );
    expect(deleteCalls.length).toBe(0);
    confirmSpy.mockRestore();
  });
});