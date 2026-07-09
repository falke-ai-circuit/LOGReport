// Shared types used across multiple API modules

export interface IORow {
  index: string
  type: string
  name: string
  value: string
  status: string
}

export interface FBCResult {
  node: string
  token: string
  rows: IORow[]
  raw: string
  error?: string
}

export interface Counter {
  name: string
  value: string
  unit?: string
}

export interface RPCResult {
  node: string
  token: string
  counters: Counter[]
  raw: string
  error?: string
}
