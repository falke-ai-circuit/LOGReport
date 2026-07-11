import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LisDiagTab from '../LisDiagTab';

function mockFetchImpl(url: any, options?: any) {
  if (url?.includes('/commandqueue/add') && options?.method === 'POST') {
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}), text: () => Promise.resolve('') } as Response);
  }
  if (url?.includes('/commandqueue/start') && options?.method === 'POST') {
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}), text: () => Promise.resolve('') } as Response);
  }
  if (url?.includes('/commandqueue/status')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ current: 0, total: 0, state: 'idle', commands: [] }),
      text: () => Promise.resolve(''),
    } as Response);
  }
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}), text: () => Promise.resolve('') } as Response);
}

function renderComponent(props: Partial<Parameters<typeof LisDiagTab>[0]> = {}) {
  return render(
    <LisDiagTab
      targetIP="192.168.1.10"
      targetNode="AL01m"
      tokenID="102"
      password="secret"
      exeNum={1}
      commands={[]}
      {...props}
    />,
  );
}

describe('LisDiagTab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn(mockFetchImpl) as any;
  });

  it('tab is always interactive — IP and port fields visible', async () => {
    renderComponent();
    expect(screen.getByPlaceholderText('IP address')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Port')).toBeInTheDocument();
  });

  it('IP field is editable when disconnected', async () => {
    renderComponent();
    const ipInput = screen.getByPlaceholderText('IP address');
    expect(ipInput).not.toBeDisabled();
    await userEvent.clear(ipInput);
    await userEvent.type(ipInput, '10.0.0.1');
    expect(ipInput).toHaveValue('10.0.0.1');
  });

  it('port field is editable when disconnected', async () => {
    renderComponent();
    const portInput = screen.getByPlaceholderText('Port');
    expect(portInput).not.toBeDisabled();
    await userEvent.clear(portInput);
    await userEvent.type(portInput, '9999');
    expect(portInput).toHaveValue(9999);
  });

  it('connect button is present', async () => {
    renderComponent();
    expect(screen.getByText('Connect')).toBeInTheDocument();
  });

  it('command input field is present', async () => {
    renderComponent();
    expect(screen.getByPlaceholderText(/Enter LisDiag command/)).toBeInTheDocument();
  });

  it('password field is present', async () => {
    renderComponent();
    expect(screen.getByPlaceholderText('No Auth')).toBeInTheDocument();
  });

  it('shows terminal output area', async () => {
    renderComponent();
    // The terminal output area has dark background — check session log text appears
    await waitFor(() => {
      expect(screen.getByText(/LisDiag terminal ready|LisDiag session/)).toBeInTheDocument();
    });
  });

  it('shows connection status indicator', async () => {
    renderComponent();
    // The status indicator shows "Disconnected" initially
    await waitFor(() => {
      expect(screen.getByText('Disconnected')).toBeInTheDocument();
    });
  });

  it('shows send button', async () => {
    renderComponent();
    expect(screen.getByText('Send')).toBeInTheDocument();
  });

  it('shows token/node info in connection bar', async () => {
    renderComponent();
    expect(screen.getByText(/AL01m.*exe1.*102/)).toBeInTheDocument();
  });
});