import { create } from 'zustand'
import { telnetApi, TelnetSession, CommandResult } from '../api/telnet'

export interface TerminalLine {
  type: 'cmd' | 'out' | 'err' | 'info'
  text: string
  ts: number
}

interface TelnetState {
  ip: string
  port: number
  session: TelnetSession | null
  connecting: boolean
  lines: TerminalLine[]
  inputCmd: string
  contextToken: string
  error: string | null
  setIP: (v: string) => void
  setPort: (v: number) => void
  setInputCmd: (v: string) => void
  setContextToken: (v: string) => void
  connect: () => Promise<void>
  disconnect: () => Promise<void>
  sendCommand: () => Promise<void>
  clearTerminal: () => void
}

function push(lines: TerminalLine[], type: TerminalLine['type'], text: string): TerminalLine[] {
  return [...lines, { type, text, ts: Date.now() }]
}

export const useTelnetStore = create<TelnetState>((set, get) => ({
  ip: '',
  port: 23,
  session: null,
  connecting: false,
  lines: [],
  inputCmd: '',
  contextToken: '',
  error: null,
  setIP: (v) => set({ ip: v }),
  setPort: (v) => set({ port: v }),
  setInputCmd: (v) => set({ inputCmd: v }),
  setContextToken: (v) => set({ contextToken: v }),

  connect: async () => {
    const { ip, port } = get()
    if (!ip) return
    set({ connecting: true, error: null })
    try {
      const sess = await telnetApi.connect(ip, port)
      set({
        session: sess,
        connecting: false,
        lines: push(get().lines, 'info', `Connected to ${sess.addr || ip}:${port}`)
      })
    } catch (e) {
      set({
        connecting: false,
        error: String(e),
        lines: push(get().lines, 'err', `Connection failed: ${e}`)
      })
    }
  },

  disconnect: async () => {
    const { session } = get()
    if (!session) return
    try {
      await telnetApi.disconnect(session.session_id)
    } catch (_) {}
    set({
      session: null,
      lines: push(get().lines, 'info', 'Disconnected')
    })
  },

  sendCommand: async () => {
    const { session, inputCmd, contextToken } = get()
    if (!session || !inputCmd.trim()) return
    const cmd = inputCmd.trim()
    set({
      inputCmd: '',
      lines: push(get().lines, 'cmd', `> ${cmd}`)
    })
    try {
      const result: CommandResult = await telnetApi.command(session.session_id, cmd, contextToken)
      const resolved = result.command !== cmd ? `[resolved: ${result.command}]` : ''
      const outLines = result.output.split('\n').filter(l => l.trim())
      let newLines = get().lines
      if (resolved) newLines = push(newLines, 'info', resolved)
      for (const l of outLines) {
        newLines = push(newLines, 'out', l)
      }
      if (outLines.length === 0) newLines = push(newLines, 'info', '(no output)')
      set({ lines: newLines })
    } catch (e) {
      set({ lines: push(get().lines, 'err', `Error: ${e}`) })
    }
  },

  clearTerminal: () => set({ lines: [] })
}))
