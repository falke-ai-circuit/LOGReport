import { useEffect, useRef, useCallback } from 'react';

/**
 * Generic polling hook. Calls `fn` immediately on mount, then every
 * `intervalMs` milliseconds. Cleans up on unmount. Returns a manual
 * `trigger` function for on-demand refresh.
 */
export function usePolling(
  fn: () => void | Promise<void>,
  intervalMs: number,
  enabled = true,
) {
  const fnRef = useRef(fn);
  fnRef.current = fn;

  const trigger = useCallback(() => {
    void fnRef.current();
  }, []);

  useEffect(() => {
    if (!enabled) return;

    // Immediate first call
    void fnRef.current();

    const id = setInterval(() => {
      void fnRef.current();
    }, intervalMs);

    return () => clearInterval(id);
  }, [intervalMs, enabled]);

  return { trigger };
}
