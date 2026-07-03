import { apiFetch } from './client'

export interface TelnetSession {
  session_id: string
  ip: string
  port: number
  connected: boolean
  addr?: string
}

export interface CommandResult {
  command: string
  raw: string
  output: string
  session: string
}

export const telnetApi = {
  sessions: () => apiFetch<TelnetSession[]>('/api/telnet/'),
  connect: (ip: string, port: number) =>
    apiFetch<TelnetSession>('/api/telnet/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip, port })
    }),
  disconnect: (id: string) =>
    apiFetch<void>(`/api/telnet/${id}`, { method: 'DELETE' }),
  status: (id: string) =>
    apiFetch<TelnetSession>(`/api/telnet/${id}`),
  command: (id: string, command: string, contextToken = '', timeoutMs = 5000) =>
    apiFetch<CommandResult>(`/api/telnet/${id}/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command, context_token: contextToken, timeout_ms: timeoutMs })
    })
}
