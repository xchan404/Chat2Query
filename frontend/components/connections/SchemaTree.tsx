"use client";

/**
 * SchemaTree — displays schemas → tables → columns from a connection's synced schema.
 * Fetches from GET /api/database-connections/{id}/schemas (returns SchemaOut[]).
 * Collapsible per schema, collapsible per table.
 */

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { connectionsApi, type SchemaOut, type TableOut } from "@/lib/api/connections";

// ── Table row (expandable to show columns) ────────────────────────────────────

function TableRow({ table }: { table: TableOut }) {
  const [open, setOpen] = useState(false);

  return (
    <div>
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full text-left flex items-center gap-2 px-3 py-1.5 hover:bg-surface-alt font-mono text-xs font-bold text-ink-dark group transition-none cursor-pointer"
      >
        <span className="text-cobalt-signal font-extrabold text-[10px] w-3">
          {open ? "▼" : "▶"}
        </span>
        <span className="flex-1 truncate">{table.table_name}</span>
        {table.table_type && (
          <span className="text-ink-muted text-[10px] font-normal shrink-0">
            {table.table_type}
          </span>
        )}
        {table.row_count != null && (
          <span className="text-ink-muted text-[10px] font-normal shrink-0">
            {table.row_count.toLocaleString()} rows
          </span>
        )}
      </button>

      {open && table.columns && table.columns.length > 0 && (
        <div className="pl-8 border-l-med border-cobalt-signal ml-5 mb-1">
          {table.columns.map((col) => (
            <div
              key={col.id}
              className="flex items-center gap-2 py-0.5 px-2 font-mono text-[11px]"
            >
              {col.is_primary_key && (
                <span className="text-yellow-signal font-extrabold text-[9px] shrink-0">PK</span>
              )}
              <span className="font-semibold text-ink-dark truncate">{col.column_name}</span>
              <span className="text-ink-muted shrink-0">{col.data_type}</span>
              {col.is_nullable === false && (
                <span className="text-rust-warn text-[9px] font-extrabold shrink-0">NOT NULL</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Schema section (collapsible) ─────────────────────────────────────────────

function SchemaSection({ schema }: { schema: SchemaOut }) {
  const [open, setOpen] = useState(true);

  return (
    <div className="border-b-med border-ink-dark last:border-b-0">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full text-left flex items-center gap-2 px-4 py-2 bg-surface-alt hover:bg-ink-dark hover:text-white font-mono text-[11px] font-extrabold uppercase tracking-wider cursor-pointer transition-none"
      >
        <span className="text-[10px] w-3">{open ? "▼" : "▶"}</span>
        <span className="flex-1">{schema.schema_name}</span>
        <span className="font-normal normal-case text-[10px] opacity-60">
          {schema.tables.length} tables
        </span>
      </button>

      {open && (
        <div className="py-1">
          {schema.tables.length === 0 ? (
            <p className="px-4 py-2 font-mono text-[11px] text-ink-muted">No tables found</p>
          ) : (
            schema.tables.map((table) => <TableRow key={table.id} table={table} />)
          )}
        </div>
      )}
    </div>
  );
}

// ── Main SchemaTree ───────────────────────────────────────────────────────────

interface SchemaTreeProps {
  connectionId: string;
  connectionName: string;
  onClose: () => void;
}

export function SchemaTree({ connectionId, connectionName, onClose }: SchemaTreeProps) {
  const { data: schemas, isLoading, isError, error } = useQuery({
    queryKey: ["schemas", connectionId],
    queryFn: () => connectionsApi.schemas(connectionId),
  });

  return (
    <div
      className="fixed inset-0 bg-ink-dark/60 flex items-start justify-end z-50"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-surface border-l-thick border-ink-dark shadow-hard h-full w-full max-w-md flex flex-col">
        {/* Header */}
        <div className="bg-ink-dark text-white p-3 px-5 flex items-center justify-between shrink-0">
          <div>
            <div className="font-display font-extrabold text-sm uppercase tracking-wider">
              Schema Browser
            </div>
            <div className="font-mono text-[10px] text-white/60 mt-0.5 truncate max-w-[260px]">
              {connectionName}
            </div>
          </div>
          <button
            onClick={onClose}
            className="font-mono text-xs text-white/60 hover:text-white cursor-pointer transition-none"
          >
            [CLOSE]
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {isLoading && (
            <div className="p-6 font-mono text-[11px] text-ink-muted uppercase tracking-widest animate-pulse">
              // Loading schema...
            </div>
          )}

          {isError && (
            <div className="m-4 p-3 bg-rust-bg border-thick border-rust-warn font-mono text-[11px] font-bold text-rust-warn">
              <span className="font-extrabold">SCHEMA LOAD FAILED</span>
              <p className="mt-1 font-normal">{error?.message}</p>
              <p className="mt-1 text-[10px] text-ink-muted">
                Run SYNC SCHEMA on the connection card first to populate schema data.
              </p>
            </div>
          )}

          {schemas && schemas.length === 0 && (
            <div className="p-6 flex flex-col gap-3">
              <p className="font-mono text-[11px] text-ink-muted uppercase tracking-widest">
                // No schema data
              </p>
              <p className="font-mono text-[11px] text-ink-muted">
                Run SYNC SCHEMA on the connection card to discover the schema.
              </p>
            </div>
          )}

          {schemas && schemas.length > 0 && (
            <div>
              {schemas.map((schema) => (
                <SchemaSection key={schema.id} schema={schema} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
