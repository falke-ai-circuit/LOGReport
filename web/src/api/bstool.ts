import { apiFetch } from './client'

export interface BstoolStatus {
  available: boolean
  path: string
}

export interface BstoolResult {
  output: string
  exit_code: number
  timed_out: boolean
}

export const bstoolApi = {
  status: () => apiFetch<BstoolStatus>('/api/bstool/status'),
  run: (ip: string, token: string, timeout_sec = 30) =>
    apiFetch<BstoolResult>('/api/bstool/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip, token, timeout_sec })
    })
}
