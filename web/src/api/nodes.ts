import { apiFetch } from './client'
import type { Node } from '../types/node'

export const nodesApi = {
  getAll: () => apiFetch<Node[]>('/api/nodes'),
  getOne: (name: string) => apiFetch<Node>(`/api/nodes/${encodeURIComponent(name)}`),
  create: (node: Node) => apiFetch<Node>('/api/nodes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(node)
  }),
  update: (name: string, node: Node) => apiFetch<Node>(`/api/nodes/${encodeURIComponent(name)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(node)
  }),
  delete: (name: string) => apiFetch<void>(`/api/nodes/${encodeURIComponent(name)}`, { method: 'DELETE' })
}
