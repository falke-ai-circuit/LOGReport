import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ErrorBoundary from '../ErrorBoundary';

function ThrowOnRender(): never {
  throw new Error('test error from child');
}

function GoodChild() {
  return <div data-testid="child">child content</div>;
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset window.location.reload mock
    delete (window as any).location;
    (window as any).location = { reload: vi.fn() };
  });

  it('renders children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <GoodChild />
      </ErrorBoundary>,
    );
    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('renders error UI when a child throws', () => {
    // Suppress the expected React error boundary console.error
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ThrowOnRender />
      </ErrorBoundary>,
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('test error from child')).toBeInTheDocument();
    expect(screen.getByText('An unexpected error occurred. Try refreshing the page.')).toBeInTheDocument();

    spy.mockRestore();
  });

  it('shows a Reload Page button in the error state', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ThrowOnRender />
      </ErrorBoundary>,
    );

    expect(screen.getByText('Reload Page')).toBeInTheDocument();
    spy.mockRestore();
  });

  it('calls window.location.reload when Reload Page is clicked', async () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ThrowOnRender />
      </ErrorBoundary>,
    );

    const reloadButton = screen.getByText('Reload Page');
    await userEvent.click(reloadButton);

    expect((window as any).location.reload).toHaveBeenCalled();
    spy.mockRestore();
  });

  it('calls componentDidCatch (console.error) when a child throws', () => {
    // Override the global console.error mock to capture all calls
    const spy = vi.fn();
    const originalErr = console.error;
    console.error = spy;

    render(
      <ErrorBoundary>
        <ThrowOnRender />
      </ErrorBoundary>,
    );

    // componentDidCatch calls console.error with 'ErrorBoundary caught:'
    expect(spy).toHaveBeenCalled();
    // Find the call that contains 'ErrorBoundary caught:'
    const found = spy.mock.calls.some(call =>
      call.some(arg => String(arg).includes('ErrorBoundary caught:'))
    );
    expect(found).toBe(true);
    console.error = originalErr;
  });
});