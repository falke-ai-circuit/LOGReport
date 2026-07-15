import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import TelnetTerminal from '../TelnetTerminal';

function renderComponent(props: Partial<Parameters<typeof TelnetTerminal>[0]> = {}) {
  return render(
    <TelnetTerminal
      currentToken="102"
      currentTokenType="FBC"
      currentNodeName="AL01m"
      {...props}
    />,
  );
}

describe('TelnetTerminal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn(() =>
      Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}), text: () => Promise.resolve('') } as Response),
    ) as any;
  });

  it('renders terminal output area with placeholder text', async () => {
    renderComponent();
    expect(screen.getByText(/Terminal output will appear here/)).toBeInTheDocument();
  });

  it('renders command input field', async () => {
    renderComponent();
    expect(screen.getByPlaceholderText(/Enter command/)).toBeInTheDocument();
  });

  it('renders IP address input', async () => {
    renderComponent();
    expect(screen.getByPlaceholderText('IP address')).toBeInTheDocument();
  });

  it('renders Port input', async () => {
    renderComponent();
    expect(screen.getByPlaceholderText('Port')).toBeInTheDocument();
  });

  it('renders Connect button', async () => {
    renderComponent();
    expect(screen.getByText('Connect')).toBeInTheDocument();
  });

  it('renders Send button', async () => {
    renderComponent();
    expect(screen.getByText('Send')).toBeInTheDocument();
  });

  it('shows disconnected status initially', async () => {
    renderComponent();
    expect(screen.getByText('Disconnected')).toBeInTheDocument();
  });

  it('shows token info when currentToken provided', async () => {
    renderComponent();
    expect(screen.getByText(/Token: 102/)).toBeInTheDocument();
  });

  it('command input is disabled when not connected', async () => {
    renderComponent();
    const cmdInput = screen.getByPlaceholderText(/Enter command/);
    expect(cmdInput).toBeDisabled();
  });

  it('Send button is disabled when not connected', async () => {
    renderComponent();
    const sendBtn = screen.getByText('Send').closest('button');
    expect(sendBtn).toBeDisabled();
  });

  it('shows external log lines when provided', async () => {
    renderComponent({ externalLog: ['> test command', 'Getting data...'] });
    expect(screen.getByText('> test command')).toBeInTheDocument();
    expect(screen.getByText('Getting data...')).toBeInTheDocument();
  });

  it('has Clear Terminal button', async () => {
    renderComponent();
    expect(screen.getByTitle('Clear Terminal')).toBeInTheDocument();
  });

  it('has Clear Log button', async () => {
    renderComponent();
    expect(screen.getByTitle('Clear Log')).toBeInTheDocument();
  });

  it('has Copy to Log button', async () => {
    renderComponent();
    expect(screen.getByTitle('Copy to Log')).toBeInTheDocument();
  });
});