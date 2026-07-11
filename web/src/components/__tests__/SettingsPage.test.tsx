import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SettingsPage from '../SettingsPage';

const mockSettings = {
  dia_host: '127.0.0.1',
  dia_port: 1234,
  bstool_host: '127.0.0.1',
  bstool_port: 1516,
  log_root: 'C:\\temp\\logs',
  logroot_name: '_LOG',
  bstool_path: 'C:\\dna\\CA\\bstool\\BsTool.exe',
  communication_line: 'AB01',
  output_dir: 'C:\\temp\\reports',
  lis_mode: 'rsu',
  lis_exe_count: 6,
  lisdiag_password: 'secret',
  scan_method: 'remote_bu',
  node_filter: 'AP,AL',
};

let savedSettings = { ...mockSettings };

function mockFetchImpl(url: any, options?: any) {
  if (url === '/api/v1/settings' && options?.method === 'POST') {
    savedSettings = JSON.parse(options.body);
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}), text: () => Promise.resolve('') } as Response);
  }
  if (url === '/api/v1/settings') {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ settings: savedSettings }),
      text: () => Promise.resolve(''),
    } as Response);
  }
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}), text: () => Promise.resolve('') } as Response);
}

function renderComponent() {
  return render(<SettingsPage />);
}

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    savedSettings = { ...mockSettings };
    global.fetch = vi.fn(mockFetchImpl) as any;
  });

  it('renders Settings title', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });
  });

  it('renders DIA Host field with current value', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByDisplayValue('127.0.0.1')).toBeInTheDocument();
    });
  });

  it('renders DIA Port field with current value', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByDisplayValue('1234')).toBeInTheDocument();
    });
  });

  it('renders BU IP Address field', async () => {
    renderComponent();
    await waitFor(() => {
      // bstool_host has same value as dia_host — check the label
      expect(screen.getByText('BU IP Address')).toBeInTheDocument();
    });
  });

  it('renders BU TCP Port field', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('BU TCP Port')).toBeInTheDocument();
    });
  });

  it('renders BsTool Path field', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('BsTool Path')).toBeInTheDocument();
    });
  });

  it('renders Communication Line field', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Communication Line')).toBeInTheDocument();
    });
  });

  it('renders Scan Method field', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Scan Method')).toBeInTheDocument();
    });
  });

  it('renders Node Filter field', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Node Filter')).toBeInTheDocument();
    });
  });

  it('renders LIS Capture Method select field', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('LIS Capture Method')).toBeInTheDocument();
    });
  });

  it('renders LIS Exe Count field', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('LIS Exe Count')).toBeInTheDocument();
    });
  });

  it('renders LisDiag Password field', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('LisDiag Password')).toBeInTheDocument();
    });
  });

  it('renders Log Root Directory field', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Log Root Directory')).toBeInTheDocument();
    });
  });

  it('renders Log Root Folder Name field', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Log Root Folder Name')).toBeInTheDocument();
    });
  });

  it('renders Report Output Directory field', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Report Output Directory')).toBeInTheDocument();
    });
  });

  it('dia_host field change updates value', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByDisplayValue('127.0.0.1')).toBeInTheDocument();
    });
    const diaHostInput = screen.getByDisplayValue('127.0.0.1');
    await userEvent.clear(diaHostInput);
    await userEvent.type(diaHostInput, '10.0.0.99');
    expect(diaHostInput).toHaveValue('10.0.0.99');
  });

  it('lis_mode select can change to lisdiag', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('LIS Capture Method')).toBeInTheDocument();
    });
    const lisModeSelect = screen.getByDisplayValue(/RSU6 via DIA/);
    await userEvent.selectOptions(lisModeSelect, 'lisdiag');
    expect((lisModeSelect as HTMLSelectElement).value).toBe('lisdiag');
  });

  it('lis_mode select can change to diaglis', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('LIS Capture Method')).toBeInTheDocument();
    });
    const lisModeSelect = screen.getByDisplayValue(/RSU6 via DIA/);
    await userEvent.selectOptions(lisModeSelect, 'diaglis');
    expect((lisModeSelect as HTMLSelectElement).value).toBe('diaglis');
  });

  it('lis_exe_count input can change value', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByDisplayValue('6')).toBeInTheDocument();
    });
    const exeCountInput = screen.getByDisplayValue('6');
    await userEvent.clear(exeCountInput);
    await userEvent.type(exeCountInput, '8');
    expect(exeCountInput).toHaveValue(8);
  });

  it('save button calls POST /settings', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Save Settings')).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText('Save Settings'));
    await waitFor(() => {
      const postCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => c[0] === '/api/v1/settings' && (c[1] as any)?.method === 'POST',
      );
      expect(postCalls.length).toBeGreaterThan(0);
    });
  });

  it('save persistence — save then reload shows saved values', async () => {
    const { unmount } = renderComponent();
    await waitFor(() => {
      expect(screen.getByDisplayValue('127.0.0.1')).toBeInTheDocument();
    });
    // Change dia_host
    const diaHostInput = screen.getByDisplayValue('127.0.0.1');
    await userEvent.clear(diaHostInput);
    await userEvent.type(diaHostInput, '10.0.0.55');
    // Save
    await userEvent.click(screen.getByText('Save Settings'));
    await waitFor(() => {
      const postCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => c[0] === '/api/v1/settings' && (c[1] as any)?.method === 'POST',
      );
      expect(postCalls.length).toBeGreaterThan(0);
    });
    // Unmount and re-render — the mock fetch will return savedSettings
    unmount();
    renderComponent();
    await waitFor(() => {
      expect(screen.getByDisplayValue('10.0.0.55')).toBeInTheDocument();
    });
  });

  it('shows Saved confirmation after successful save', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Save Settings')).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText('Save Settings'));
    await waitFor(() => {
      expect(screen.getByText('Saved')).toBeInTheDocument();
    });
  });
});