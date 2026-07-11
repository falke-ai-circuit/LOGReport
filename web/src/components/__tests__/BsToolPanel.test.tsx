import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BsToolPanel from '../BsToolPanel';

function mockFetchImpl(url: any, options?: any) {
  if (url?.includes('/bstool/errlog') && options?.method === 'POST') {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ raw_output: 'BsTool output line 1\nBsTool output line 2', exit_code: 0 }),
      text: () => Promise.resolve(''),
    } as Response);
  }
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}), text: () => Promise.resolve('') } as Response);
}

function renderComponent(props: Partial<Parameters<typeof BsToolPanel>[0]> = {}) {
  return render(
    <BsToolPanel
      currentNodeName="AL01m"
      {...props}
    />,
  );
}

describe('BsToolPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn(mockFetchImpl) as any;
  });

  it('renders server name input', async () => {
    renderComponent();
    expect(screen.getByPlaceholderText(/Server name/)).toBeInTheDocument();
  });

  it('renders Execute button', async () => {
    renderComponent();
    expect(screen.getByText('Execute')).toBeInTheDocument();
  });

  it('renders BsTool Path input', async () => {
    renderComponent();
    expect(screen.getByPlaceholderText('/path/to/BsTool.exe')).toBeInTheDocument();
  });

  it('renders COMMUNICATION_LINE input', async () => {
    renderComponent();
    expect(screen.getByText('COMMUNICATION_LINE:')).toBeInTheDocument();
  });

  it('shows output display area with placeholder text', async () => {
    renderComponent();
    expect(screen.getByText(/BsTool output will appear here/)).toBeInTheDocument();
  });

  it('errlog button calls POST /bstool/errlog via Execute', async () => {
    renderComponent();
    const serverInput = screen.getByPlaceholderText(/Server name/);
    await userEvent.type(serverInput, 'AP01');
    await userEvent.click(screen.getByText('Execute'));
    await waitFor(() => {
      const errlogCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => typeof c[0] === 'string' && c[0].includes('/bstool/errlog') && (c[1] as any)?.method === 'POST',
      );
      // May go through WebSocket fallback (which errors in jsdom) → REST fallback
      // In jsdom, WebSocket will fail, so it should fall back to REST
      expect(errlogCalls.length).toBeGreaterThan(0);
    });
  });

  it('shows error when server name is empty', async () => {
    renderComponent();
    // Clear any default server name
    const serverInput = screen.getByPlaceholderText(/Server name/);
    await userEvent.clear(serverInput);
    await userEvent.click(screen.getByText('Execute'));
    // The Execute button is disabled when serverName is empty, so verify it's disabled
    expect(screen.getByText('Execute').closest('button')).toBeDisabled();
  });

  it('displays output after execution', async () => {
    renderComponent();
    const serverInput = screen.getByPlaceholderText(/Server name/);
    await userEvent.type(serverInput, 'AP01');
    await userEvent.click(screen.getByText('Execute'));
    await waitFor(() => {
      expect(screen.getByText(/BsTool output line 1/)).toBeInTheDocument();
    });
  });

  it('has Clear Terminal button', async () => {
    renderComponent();
    const clearBtn = screen.getByTitle('Clear Terminal');
    expect(clearBtn).toBeInTheDocument();
  });

  it('has Copy to Log button', async () => {
    renderComponent();
    const copyBtn = screen.getByTitle('Copy to Log');
    expect(copyBtn).toBeInTheDocument();
  });
});