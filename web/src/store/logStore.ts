import { create } from 'zustand'
import { logsApi, ScanResult } from '../api/logs'

interface LogState {
  rootPath: string
  scanResult: ScanResult | null
  scanning: boolean
  generating: boolean
  downloadUrl: string | null
  error: string | null
  setRootPath: (p: string) => void
  scan: () => Promise<void>
  generate: (title: string) => Promise<void>
  clear: () => void
}

export const useLogStore = create<LogState>((set, get) => ({
  rootPath: '',
  scanResult: null,
  scanning: false,
  generating: false,
  downloadUrl: null,
  error: null,
  setRootPath: (p) => set({ rootPath: p }),
  scan: async () => {
    const { rootPath } = get()
    if (!rootPath) return
    set({ scanning: true, error: null, scanResult: null, downloadUrl: null })
    try {
      const result = await logsApi.scan(rootPath)
      set({ scanResult: result, scanning: false })
    } catch (e) {
      set({ error: String(e), scanning: false })
    }
  },
  generate: async (title) => {
    const { scanResult } = get()
    if (!scanResult) return
    set({ generating: true, error: null })
    try {
      const result = await logsApi.generate(scanResult.scan_id, title)
      set({ downloadUrl: result.download, generating: false })
    } catch (e) {
      set({ error: String(e), generating: false })
    }
  },
  clear: () => set({ scanResult: null, downloadUrl: null, error: null })
}))