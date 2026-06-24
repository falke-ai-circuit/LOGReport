import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SysFileUpload from '../SysFileUpload';

const parseResponse = {
  filename: 'test.sys',
  file_size_bytes: 2048,
  parsed_at: '2025-01-01T10:00:00Z',
  entries: [
    { lid: 'LID001', node_type: 'ACN', description: 'ACN node for building A' },
    { lid: 'LID002', node_type: 'CIS', description: 'CIS node for floor 1' },
  ],
  total_entries: 2,
  nodes_created: 2,
};

function mockFile(name = 'test.sys', size = 2048) {
  const content = new Array(size).fill('x').join('');
  return new File([content], name);
}

describe('SysFileUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(<SysFileUpload />);
    expect(screen.getByText('SysFile Upload')).toBeInTheDocument();
  });

  it('shows idle state with drop zone text', () => {
    render(<SysFileUpload />);
    expect(screen.getByText(/Drag and drop a/)).toBeInTheDocument();
    expect(screen.getByText('or click to browse')).toBeInTheDocument();
  });

  it('shows description text about .sys files', () => {
    render(<SysFileUpload />);
    expect(screen.getByText(/Upload a/i)).toBeInTheDocument();
  });

  it('uploads a valid .sys file and shows success state', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(parseResponse),
      text: () => Promise.resolve(''),
    } as Response);

    render(<SysFileUpload />);

    // Use the hidden file input directly (no label associated)
    const fileInputs = document.querySelectorAll('input[type="file"]');
    expect(fileInputs.length).toBe(1);

    const fileInput = fileInputs[0] as HTMLInputElement;
    await userEvent.upload(fileInput, mockFile());

    await waitFor(() => {
      expect(screen.getByText('Parsed successfully')).toBeInTheDocument();
    });
    expect(screen.getByText('2 entries found')).toBeInTheDocument();
  });

  it('fetches /api/v1/parse/sysfile with POST when uploading', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(parseResponse),
      text: () => Promise.resolve(''),
    } as Response);

    render(<SysFileUpload />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(fileInput, mockFile());

    await waitFor(() => {
      const postCalls = vi.mocked(global.fetch).mock.calls.filter(
        (c) => c[0] === '/api/v1/parse/sysfile' && c[1]?.method === 'POST',
      );
      expect(postCalls.length).toBe(1);
    });
  });

  it('shows parse results table after successful upload', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(parseResponse),
      text: () => Promise.resolve(''),
    } as Response);

    render(<SysFileUpload />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(fileInput, mockFile());

    await waitFor(() => {
      expect(screen.getByText('Parse Results')).toBeInTheDocument();
    });
    expect(screen.getByText('LID001')).toBeInTheDocument();
    expect(screen.getByText('LID002')).toBeInTheDocument();
    expect(screen.getByText('ACN node for building A')).toBeInTheDocument();
    expect(screen.getByText('CIS node for floor 1')).toBeInTheDocument();
  });

  it('shows file info in the results header', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(parseResponse),
      text: () => Promise.resolve(''),
    } as Response);

    render(<SysFileUpload />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(fileInput, mockFile('test.sys', 2048));

    await waitFor(() => {
      expect(screen.getByText(/test.sys/)).toBeInTheDocument();
    });
    expect(screen.getByText(/2.0 KB/)).toBeInTheDocument();
  });

  it('shows error state when upload fails with non-ok response', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ message: 'Invalid file format' }),
      text: () => Promise.resolve(''),
    } as Response);

    render(<SysFileUpload />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(fileInput, mockFile());

    await waitFor(() => {
      expect(screen.getByText('Parse failed')).toBeInTheDocument();
    });
    expect(screen.getByText('Invalid file format')).toBeInTheDocument();
  });

  it('shows error state when fetch throws', async () => {
    vi.mocked(global.fetch).mockRejectedValue(new Error('Network error'));

    render(<SysFileUpload />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(fileInput, mockFile());

    await waitFor(() => {
      expect(screen.getByText('Parse failed')).toBeInTheDocument();
    });
    expect(screen.getByText('Network error')).toBeInTheDocument();
  });

  it('rejects non-.sys files', async () => {
    render(<SysFileUpload />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const txtFile = new File(['content'], 'test.txt', { type: 'text/plain' });
    fireEvent.change(fileInput, { target: { files: [txtFile] } });

    await waitFor(() => {
      expect(screen.getAllByText('Only .sys files are supported').length).toBeGreaterThan(0);
    });
  });

  it('shows uploading state during file upload', async () => {
    let resolveUpload: (value: any) => void;
    vi.mocked(global.fetch).mockReturnValue(
      new Promise((resolve) => {
        resolveUpload = resolve;
      }) as Promise<Response>,
    );

    render(<SysFileUpload />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(fileInput, mockFile('uploading.sys', 1024));

    await waitFor(() => {
      expect(screen.getByText(/Parsing/)).toBeInTheDocument();
    });
    expect(screen.getByText('uploading.sys')).toBeInTheDocument();

    resolveUpload!({
      ok: true,
      status: 200,
      json: () => Promise.resolve(parseResponse),
      text: () => Promise.resolve(''),
    } as Response);
  });

  it('can reset from success state', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(parseResponse),
      text: () => Promise.resolve(''),
    } as Response);

    render(<SysFileUpload />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(fileInput, mockFile());

    await waitFor(() => {
      expect(screen.getByText('Parsed successfully')).toBeInTheDocument();
    });

    // Find and click the reset (X) button in the results header
    const buttons = screen.getAllByRole('button');
    // The reset button is a btn-ghost with X icon inside the results card
    const resetBtn = buttons.find((b) => b.className.includes('btn-ghost'));
    expect(resetBtn).toBeTruthy();
    await userEvent.click(resetBtn!);

    await waitFor(() => {
      expect(screen.queryByText('Parse Results')).not.toBeInTheDocument();
    });
    expect(screen.getAllByText(/Drag and drop/i).length).toBeGreaterThan(0);
  });

  it('shows table headers LID, Node Type, Description', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(parseResponse),
      text: () => Promise.resolve(''),
    } as Response);

    render(<SysFileUpload />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(fileInput, mockFile());

    await waitFor(() => {
      expect(screen.getByText('LID')).toBeInTheDocument();
      expect(screen.getByText('Node Type')).toBeInTheDocument();
      expect(screen.getByText('Description')).toBeInTheDocument();
    });
  });

  it('shows empty entries message when parse returns 0 entries', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        ...parseResponse,
        entries: [],
        total_entries: 0,
      }),
      text: () => Promise.resolve(''),
    } as Response);

    render(<SysFileUpload />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(fileInput, mockFile());

    await waitFor(() => {
      expect(screen.getByText('No entries found in this file.')).toBeInTheDocument();
    });
  });
});