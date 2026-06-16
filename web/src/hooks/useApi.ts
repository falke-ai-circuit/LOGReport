import { useState, useCallback } from 'react';

interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface ApiClient {
  get: <T>(path: string) => Promise<T>;
  post: <T>(path: string, body: unknown) => Promise<T>;
  upload: <T>(path: string, formData: FormData) => Promise<T>;
}

const BASE = '/api/v1';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error');
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json();
}

export function useApi(): ApiClient {
  const get = useCallback(async <T,>(path: string): Promise<T> => {
    const res = await fetch(`${BASE}${path}`);
    return handleResponse<T>(res);
  }, []);

  const post = useCallback(async <T,>(path: string, body: unknown): Promise<T> => {
    const res = await fetch(`${BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return handleResponse<T>(res);
  }, []);

  const upload = useCallback(async <T,>(path: string, formData: FormData): Promise<T> => {
    const res = await fetch(`${BASE}${path}`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<T>(res);
  }, []);

  return { get, post, upload };
}

export function useApiGet<T>(path: string): ApiState<T> & { refetch: () => void } {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const res = await fetch(`${BASE}${path}`);
      const data = await handleResponse<T>(res);
      setState({ data, loading: false, error: null });
    } catch (err) {
      setState({
        data: null,
        loading: false,
        error: err instanceof Error ? err.message : 'Unknown error',
      });
    }
  }, [path]);

  // Initial fetch is handled by the caller via useEffect
  return { ...state, refetch: fetchData };
}
