import '@testing-library/jest-dom';

// Mock fetch globally — individual tests override with vi.mocked(fetch) or
// by reassigning global.fetch.
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
  } as Response)
) as typeof fetch;

// Suppress console.error from ErrorBoundary tests
const originalError = console.error;
beforeEach(() => {
  console.error = vi.fn((...args) => {
    // Don't suppress test assertion errors
    if (args[0]?.toString?.()?.includes('ErrorBoundary caught:')) return;
    originalError.call(console, ...args);
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});