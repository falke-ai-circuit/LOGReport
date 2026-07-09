import { apiFetch } from './client'

export interface NodeScanResult {
  name: string
  ip: string
  reachable: boolean
  port_23: boolean
  port_1234: boolean
  latency_ms: number
}

export interface NodeScanResponse {
  total: number
  results: NodeScanResult[]
}

export const nodeScanApi = {
  scan: (names: string[] = []) =>
    apiFetch<NodeScanResponse>('/api/node-scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ names })
    })
}
