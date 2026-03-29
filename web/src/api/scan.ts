import { apiFetch } from './client'
import { FBCResult, RPCResult } from './types'

export interface ParsedScan {
  scan_id: string
  fbc: FBCResult[]
  rpc: RPCResult[]
}

export const scanApi = {
  getParsed: (scanId: string) =>
    apiFetch<ParsedScan>(`/api/scans/${scanId}/parsed`)
}
