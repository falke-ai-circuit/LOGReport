// TypeScript types matching LOGReport REST API response shapes.
// Derived from internal/api/handlers.go and internal/types/*.go

// ─── Health ───────────────────────────────────────────────────────

export interface HealthStatus {
  status: string;
  version: string;
  uptime: string;
  db_status: string;
  node_count: number;
}

// ─── Node ────────────────────────────────────────────────────────

export interface ApiNode {
  id: number;
  address: string;
  port: number;
  name: string;
  node_type: string;
  token: string;
  status: string;
  last_connected: string;
  created_at: string;
  updated_at: string;
}

export interface NodeListResponse {
  nodes: ApiNode[];
  total: number;
  limit: number;
  offset: number;
}

export interface NodeDetailResponse {
  node: ApiNode;
  io_summary: {
    fbc_modules: number;
    rpc_modules: number;
    total_io_points: number;
    last_scan: string | null;
  };
}

// ─── Connect ──────────────────────────────────────────────────────

export interface ConnectRequest {
  address: string;
  port: number;
  name: string;
  node_type: string;
  token: string;
  username: string;
  password: string;
}

export interface ConnectResponse {
  node: ApiNode;
}

// ─── Scan ─────────────────────────────────────────────────────────

export interface ScanRequest {
  modules: string[];
  token: string;
}

export interface ScanResponse {
  node_address: string;
  scanned_at: string;
  fbc_modules: ApiFBCModule[];
  rpc_modules: ApiRPCModule[];
  io_points_total: number;
}

// ─── FBC ─────────────────────────────────────────────────────────

export interface ApiFBCChannel {
  channel_position: number;
  channel_type: string;
}

export interface ApiFBCModule {
  module_position: number;
  channels: ApiFBCChannel[];
}

export interface FBCResponse {
  node_address: string;
  fbc_modules: ApiFBCModule[];
  total_modules: number;
}

// ─── RPC ─────────────────────────────────────────────────────────

export interface ApiRPCCounter {
  counter_name: string;
  counter_value: number;
}

export interface ApiRPCModule {
  module_position: number;
  counters: ApiRPCCounter[];
}

export interface RPCResponse {
  node_address: string;
  rpc_modules: ApiRPCModule[];
  total_modules: number;
}

// ─── Report ──────────────────────────────────────────────────────

export interface ApiReport {
  report_id: string;
  status: string;
  format: string;
  template: string;
  node_addresses: string[];
  file_path?: string;
  file_size?: number;
  created_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface ReportListResponse {
  reports: ApiReport[];
  total: number;
  limit: number;
  offset: number;
}

// ─── Error ───────────────────────────────────────────────────────

export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}
