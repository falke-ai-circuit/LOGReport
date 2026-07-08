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

// ─── Commander: NodeConfig / TreeNode ─────────────────────────────

export interface Token {
  token_id: string;
  token_type: string; // "FBC", "RPC", "LOG", "LIS", "FTP"
  port: number;
  protocol: string; // "telnet" or "ftp"
}

export interface NodeConfig {
  name: string;
  ip_address: string;
  tokens: Token[];
}

export interface TreeNodeData {
  name: string;
  type: string; // "root", "node", "group", "token", "file"
  ip?: string;
  token_id?: string;
  port?: number;
  protocol?: string;
  status?: string; // "idle", "connected", "error", "warning"
  file_path?: string; // absolute path for file-type nodes
  file_name?: string; // base filename for file-type nodes
  section_type?: string; // "FBC", "RPC", "LOG", "LIS"
  line_count?: number; // line count for file-type nodes
  children?: TreeNodeData[];
}

// ─── Commander: NodesConfig API ───────────────────────────────────

export interface NodesConfigResponse {
  configs: NodeConfig[];
  path: string;
  count?: number;
}

export interface NodesConfigTreeResponse {
  tree: TreeNodeData;
  path: string;
  count: number;
}

// ─── Commander: Telnet Session ────────────────────────────────────

export interface TelnetConnectRequest {
  host: string;
  port: number;
  timeout?: number;
}

export interface TelnetConnectResponse {
  session_id: string;
  host: string;
  port: number;
  connected: boolean;
}

export interface TelnetCommandResponse {
  session_id: string;
  command: string;
  sent: boolean;
}

export interface TelnetSessionsResponse {
  sessions: string[];
  count: number;
}

// ─── Commander: WebSocket Messages ────────────────────────────────

export interface TelnetWSMessage {
  action: 'connect' | 'command' | 'disconnect';
  host?: string;
  port?: number;
  command?: string;
}

export interface TelnetWSResponse {
  type: 'output' | 'status' | 'error' | 'prompt';
  data?: string;
  connected?: boolean;
  session_id?: string;
  message?: string;
}

export interface BsToolWSMessage {
  action: 'execute';
  server_name: string;
  command?: string;
}

export interface BsToolWSResponse {
  type: 'output' | 'done' | 'error';
  data?: string;
  exit_code?: number;
  message?: string;
  file_written?: boolean;
  file_path?: string;
}

// ─── Commander: Command Queue ─────────────────────────────────────

export interface QueuedCommand {
  id: string;
  type: string; // "fbc", "rpc", "log", "bstool", "raw"
  node_name: string;
  token_id: string;
  command: string;
  status: string; // "pending", "running", "completed", "failed", "cancelled"
  output?: string;
  error?: string;
  started_at?: string;
  finished_at?: string;
}

export interface QueueStatusResponse {
  current: number;
  total: number;
  state: string; // "idle", "running", "paused", "done"
  commands: QueuedCommand[];
}

export interface QueueAddRequest {
  type: string;
  node_name: string;
  token_id: string;
  command: string;
}

export interface QueueBatchRequest {
  configs: NodeConfig[];
  session_id?: string;
}

// ─── Commander: Log Writer ────────────────────────────────────────

export interface LogEntry {
  file_name: string;
  file_path: string;
  size: number;
  modified_at: string;
}

export interface LogListResponse {
  node_name: string;
  logs: LogEntry[];
  count: number;
}

export interface LogWriteRequest {
  token_type: string;
  token_id: string;
  output: string;
}

// ─── Commander: Scan Compare ──────────────────────────────────────

export interface ScanCompareRequest {
  node_address: string;
  port: number;
  token: string;
  file_data: string;
}

export interface ComparisonCell {
  row: number;
  col: number;
  file_value?: string;
  live_value?: string;
  status: string; // "match", "mismatch", "file_only", "live_only"
}

export interface ScanCompareResponse {
  comparison: {
    total_cells: number;
    matching: number;
    mismatched: number;
    file_only: number;
    live_only: number;
    cells: ComparisonCell[];
  };
}
