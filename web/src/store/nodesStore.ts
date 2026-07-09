import { create } from 'zustand'
import type { Node } from '../types/node'
import { nodesApi } from '../api/nodes'

interface NodesState {
  nodes: Node[]
  selectedNode: Node | null
  loading: boolean
  error: string | null
  fetchNodes: () => Promise<void>
  selectNode: (node: Node | null) => void
}

export const useNodesStore = create<NodesState>((set) => ({
  nodes: [],
  selectedNode: null,
  loading: false,
  error: null,
  fetchNodes: async () => {
    set({ loading: true, error: null })
    try {
      const nodes = await nodesApi.getAll()
      set({ nodes, loading: false })
    } catch (e) {
      set({ error: String(e), loading: false })
    }
  },
  selectNode: (node) => set({ selectedNode: node })
}))
