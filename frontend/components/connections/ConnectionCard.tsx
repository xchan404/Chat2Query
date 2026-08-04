"use client";

/**
 * ConnectionCard — displays a single connection with test + sync-schema actions.
 * Owns its own test/sync pending/success/error state (not in Zustand).
 * Wired to real backend via TanStack Query mutations.
 */

import React, { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { connectionsApi, type ConnectionOut, type TestResult } from "@/lib/api/connections";
import { StatusPill } from "@/components/shared/StatusPill";

interface ConnectionCardProps {
  connection: ConnectionOut;
  onEdit: (connection: ConnectionOut) => void;
  onViewSchema: (connectionId: string) => void;
}

export function ConnectionCard({ connection, onEdit, onViewSchema }: ConnectionCardProps) {
  const queryClient = useQueryClient();
  const [lastTestResult, setLastTestResult] = useState<TestResult | null>(null);

  const testMutation = useMutation({
    mutationFn: () => connectionsApi.test(connection.id),
    onSuccess: (result) => {
      setLastTestResult(result);
    },
  });

  const syncMutation = useMutation({
    mutationFn: () => connectionsApi.syncSchema(connection.id),
    onSuccess: () => {
      // Invalidate schemas cache for this connection
      void queryClient.invalidateQueries({ queryKey: ["schemas", connection.id] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => connectionsApi.delete(connection.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["connections"] });
    },
  });

  const dbTypeLabel = connection.database_type.toUpperCase();

  return (
    <div
      className="bg-surface border-thick border-ink-dark shadow-hard flex flex-col"
      id={`connection-card-${connection.id}`}
    >
      {/* Card header */}
      <div className="bg-ink-dark text-white p-3 px-4 flex items-center justify-between border-b-thick border-ink-dark">
        <div className="flex items-center gap-2.5">
          <span className="bg-cobalt-signal text-white px-1.5 py-0.5 font-mono text-[10px] font-extrabold border border-white/20">
            {dbTypeLabel}
          </span>
          <span className="font-display font-extrabold text-sm uppercase tracking-wider truncate max-w-[180px]">
            {connection.name}
          </span>
        </div>
        <StatusPill
          variant={connection.is_active ? "ok" : "warn"}
          label={connection.is_active ? "ACTIVE" : "INACTIVE"}
        />
      </div>

      {/* Connection details */}
      <div className="p-4 flex flex-col gap-2 font-mono text-xs text-ink-muted border-b-med border-ink-dark">
        <div className="flex gap-2">
          <span className="text-ink-dark font-extrabold w-24 shrink-0">HOST</span>
          <span className="truncate">{connection.host}:{connection.port}</span>
        </div>
        <div className="flex gap-2">
          <span className="text-ink-dark font-extrabold w-24 shrink-0">DB</span>
          <span className="truncate">{connection.database_name}</span>
        </div>
        <div className="flex gap-2">
          <span className="text-ink-dark font-extrabold w-24 shrink-0">USER</span>
          <span className="truncate">{connection.username}</span>
        </div>
        <div className="flex gap-2">
          <span className="text-ink-dark font-extrabold w-24 shrink-0">SSL</span>
          <span>{connection.ssl_enabled ? "ENABLED" : "DISABLED"}</span>
        </div>
      </div>

      {/* Test result — shown inline, not a toast */}
      {lastTestResult && (
        <div
          className={`mx-4 mt-3 p-2.5 border-med font-mono text-[11px] font-bold flex items-center gap-2 ${
            lastTestResult.success
              ? "bg-emerald-bg border-emerald-pass text-emerald-pass"
              : "bg-rust-bg border-rust-warn text-rust-warn"
          }`}
        >
          <span className="font-extrabold">
            {lastTestResult.success ? "CONNECTED" : "FAILED"}
          </span>
          <span>—</span>
          <span className="flex-1 truncate">{lastTestResult.message}</span>
          {lastTestResult.latency_ms != null && (
            <span className="shrink-0 text-ink-muted">
              {lastTestResult.latency_ms.toFixed(0)}ms
            </span>
          )}
        </div>
      )}

      {syncMutation.isSuccess && syncMutation.data && (
        <div className="mx-4 mt-2 p-2.5 border-med border-cobalt-signal bg-cobalt-bg font-mono text-[11px] font-bold text-cobalt-signal flex gap-2">
          <span>SYNCED</span>
          <span>—</span>
          <span>
            {syncMutation.data.schemas_synced}s / {syncMutation.data.tables_synced}t / {syncMutation.data.columns_synced}c
          </span>
        </div>
      )}

      {(testMutation.isError || syncMutation.isError || deleteMutation.isError) && (
        <div className="mx-4 mt-2 p-2.5 border-med border-rust-warn bg-rust-bg font-mono text-[11px] font-bold text-rust-warn">
          {(testMutation.error ?? syncMutation.error ?? deleteMutation.error)?.message}
        </div>
      )}

      {/* Actions */}
      <div className="p-3 flex flex-wrap gap-2 bg-surface-alt border-t-med border-ink-dark mt-auto">
        <button
          id={`btn-test-${connection.id}`}
          onClick={() => {
            setLastTestResult(null);
            testMutation.mutate();
          }}
          disabled={testMutation.isPending}
          className="flex-1 min-w-0 bg-cobalt-bg text-cobalt-signal border-med border-cobalt-signal px-3 py-1.5 font-mono text-[11px] font-extrabold uppercase hover:bg-cobalt-signal hover:text-white disabled:opacity-50 transition-none cursor-pointer"
        >
          {testMutation.isPending ? "// TESTING..." : "TEST"}
        </button>
        <button
          id={`btn-sync-${connection.id}`}
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
          className="flex-1 min-w-0 bg-surface text-ink-dark border-med border-ink-dark px-3 py-1.5 font-mono text-[11px] font-extrabold uppercase hover:bg-ink-dark hover:text-white disabled:opacity-50 transition-none cursor-pointer"
        >
          {syncMutation.isPending ? "// SYNCING..." : "SYNC SCHEMA"}
        </button>
        <button
          id={`btn-schema-${connection.id}`}
          onClick={() => onViewSchema(connection.id)}
          className="flex-1 min-w-0 bg-surface text-ink-dark border-med border-ink-dark px-3 py-1.5 font-mono text-[11px] font-extrabold uppercase hover:bg-ink-dark hover:text-white transition-none cursor-pointer"
        >
          VIEW SCHEMA
        </button>
        <button
          id={`btn-edit-${connection.id}`}
          onClick={() => onEdit(connection)}
          className="px-3 py-1.5 bg-surface text-ink-dark border-med border-ink-dark font-mono text-[11px] font-extrabold uppercase hover:bg-ink-dark hover:text-white transition-none cursor-pointer"
        >
          EDIT
        </button>
        <button
          id={`btn-delete-${connection.id}`}
          onClick={() => {
            if (window.confirm(`Delete connection "${connection.name}"? This cannot be undone.`)) {
              deleteMutation.mutate();
            }
          }}
          disabled={deleteMutation.isPending}
          className="px-3 py-1.5 bg-rust-bg text-rust-warn border-med border-rust-warn font-mono text-[11px] font-extrabold uppercase hover:bg-rust-warn hover:text-white disabled:opacity-50 transition-none cursor-pointer"
        >
          {deleteMutation.isPending ? "..." : "DEL"}
        </button>
      </div>
    </div>
  );
}
