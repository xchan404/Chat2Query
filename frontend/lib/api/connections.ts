/**
 * Connections API client — typed wrappers for /api/database-connections/*.
 * Shapes sourced directly from openapi.json — do not reconstruct from memory.
 *
 * ConnectionCreate  → POST /api/database-connections
 * ConnectionOut[]   → GET  /api/database-connections
 * ConnectionOut     → GET  /api/database-connections/{id}
 * ConnectionOut     → PUT  /api/database-connections/{id}
 * void              → DELETE /api/database-connections/{id}
 * TestResult        → POST /api/database-connections/{id}/test
 * SyncSchemaResponse→ POST /api/database-connections/{id}/sync-schema
 * SchemaOut[]       → GET  /api/database-connections/{id}/schemas
 * TableOut[]        → GET  /api/database-connections/{id}/tables
 */

import { apiFetch } from "./apiClient";

// ── Shapes from openapi.json ──────────────────────────────────────────────────

export interface ConnectionCreate {
  name: string;
  database_type: "postgresql" | "mysql";
  host: string;
  port: number;
  database_name: string;
  username: string;
  password: string;
  ssl_enabled?: boolean;
  description?: string | null;
}

export interface ConnectionUpdate {
  name?: string | null;
  host?: string | null;
  port?: number | null;
  database_name?: string | null;
  username?: string | null;
  password?: string | null;
  ssl_enabled?: boolean | null;
  description?: string | null;
}

export interface ConnectionOut {
  id: string;
  tenant_id: string;
  name: string;
  database_type: string;
  host: string;
  port: number;
  database_name: string;
  username: string;
  ssl_enabled: boolean;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface TestResult {
  success: boolean;
  message: string;
  latency_ms: number | null;
}

export interface SyncSchemaResponse {
  connection_id: string;
  schemas_synced: number;
  tables_synced: number;
  columns_synced: number;
  message: string;
}

export interface TableOut {
  id: string;
  schema_id: string;
  table_name: string;
  table_type: string | null;
  row_count: number | null;
  description: string | null;
  columns?: ColumnOut[];
}

export interface ColumnOut {
  id: string;
  table_id: string;
  column_name: string;
  data_type: string | null;
  is_nullable: boolean | null;
  is_primary_key: boolean | null;
}

export interface SchemaOut {
  id: string;
  connection_id: string;
  schema_name: string;
  is_active: boolean;
  tables: TableOut[];
}

// ── Endpoints ─────────────────────────────────────────────────────────────────

export const connectionsApi = {
  list: (): Promise<ConnectionOut[]> =>
    apiFetch("/api/database-connections"),

  get: (id: string): Promise<ConnectionOut> =>
    apiFetch(`/api/database-connections/${id}`),

  create: (data: ConnectionCreate): Promise<ConnectionOut> =>
    apiFetch("/api/database-connections", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: string, data: ConnectionUpdate): Promise<ConnectionOut> =>
    apiFetch(`/api/database-connections/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: string): Promise<void> =>
    apiFetch(`/api/database-connections/${id}`, { method: "DELETE" }),

  test: (id: string): Promise<TestResult> =>
    apiFetch(`/api/database-connections/${id}/test`, { method: "POST" }),

  syncSchema: (id: string): Promise<SyncSchemaResponse> =>
    apiFetch(`/api/database-connections/${id}/sync-schema`, { method: "POST" }),

  schemas: (id: string): Promise<SchemaOut[]> =>
    apiFetch(`/api/database-connections/${id}/schemas`),

  tables: (id: string): Promise<TableOut[]> =>
    apiFetch(`/api/database-connections/${id}/tables`),
};
