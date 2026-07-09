import { apiFetch } from './client'

export interface LogFile {
  path: string
  name: string
  ext: string
  size: number
  lines?: string[]
}

export interface FolderGroup {
  name: string
  rel_path: string
  files: LogFile[]
}

export interface ScanResult {
  scan_id: string
  total: number
  groups: FolderGroup[]
}

export interface GenerateResult {
  scan_id: string
  pdf_path: string
  download: string
}

export const logsApi = {
  scan: (rootPath: string, readContent = false) =>
    apiFetch<ScanResult>('/api/logs/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ root_path: rootPath, read_content: readContent, lines_mode: 'first' })
    }),
  generate: (scanId: string, title: string, maxLines = 0) =>
    apiFetch<GenerateResult>('/api/logs/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scan_id: scanId, title, max_lines: maxLines })
    })
}