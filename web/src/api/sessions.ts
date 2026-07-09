import { apiFetch } from './client'

export interface SessionRecord {
  id: string
  kind: 'telnet' | 'bstool'
  node_name: string
  ip: string
  token?: string
  started_at: string
  ended_at?: string
  active: boolean
  lines: number
}

export interface SessionsResponse {
  total: number
  sessions: SessionRecord[]
}

export const sessionsApi = {
  list: () => apiFetch<SessionsResponse>('/api/sessions'),
  clear: () => apiFetch<void>('/api/sessions', { method: 'DELETE' })
}
