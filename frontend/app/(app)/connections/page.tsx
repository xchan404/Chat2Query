"use client";

/**
 * Connections page — F3.
 * Renders real connection data from GET /api/database-connections via TanStack Query.
 * No hardcoded connection strings, no mockup copy-paste.
 */

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { connectionsApi, type ConnectionOut } from "@/lib/api/connections";
import { ConnectionCard } from "@/components/connections/ConnectionCard";
import { ConnectionForm } from "@/components/connections/ConnectionForm";
import { SchemaTree } from "@/components/connections/SchemaTree";

export default function ConnectionsPage() {
  const [formOpen, setFormOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<ConnectionOut | undefined>();
  const [schemaConnectionId, setSchemaConnectionId] = useState<string | null>(null);

  const {
    data: connections,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["connections"],
    queryFn: connectionsApi.list,
  });

  const openCreate = () => {
    setEditTarget(undefined);
    setFormOpen(true);
  };

  const openEdit = (conn: ConnectionOut) => {
    setEditTarget(conn);
    setFormOpen(true);
  };

  const schemaConnection = connections?.find((c) => c.id === schemaConnectionId);

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
      {/* Page TopBar */}
      <div className="flex items-center justify-between p-3 px-5 bg-surface border-b-thick border-ink-dark">
        <div>
          <h1 className="font-display font-extrabold text-sm uppercase tracking-wider text-ink-dark">
            Live Connections
          </h1>
          <p className="font-mono text-[10px] text-ink-muted mt-0.5 uppercase tracking-widest">
            // Registered database connections — tenant-scoped
          </p>
        </div>
        <button
          id="btn-new-connection"
          onClick={openCreate}
          className="bg-yellow-signal text-ink-dark border-thick border-ink-dark px-5 py-2 font-display font-extrabold text-xs uppercase shadow-hard hover:bg-ink-dark hover:text-yellow-signal transition-none cursor-pointer"
        >
          + NEW CONNECTION
        </button>
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-y-auto p-5">
        {/* Loading */}
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {[1, 2].map((i) => (
              <div
                key={i}
                className="bg-surface border-thick border-ink-dark h-52 animate-pulse opacity-40"
              />
            ))}
          </div>
        )}

        {/* Error */}
        {isError && (
          <div className="bg-rust-bg border-thick border-rust-warn p-5 max-w-lg">
            <p className="font-mono text-[11px] font-extrabold text-rust-warn uppercase tracking-widest">
              LOAD FAILED
            </p>
            <p className="font-mono text-xs text-rust-warn mt-2">{error?.message}</p>
          </div>
        )}

        {/* Empty state */}
        {connections && connections.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-5 text-center py-20">
            <div className="bg-surface border-thick border-ink-dark p-8 shadow-hard max-w-sm">
              <p className="font-mono text-xs font-extrabold uppercase tracking-widest text-ink-muted">
                // No connections registered
              </p>
              <p className="font-body text-sm text-ink-muted mt-3">
                Add your first database connection to start querying with natural language.
              </p>
              <button
                onClick={openCreate}
                className="mt-5 bg-yellow-signal text-ink-dark border-thick border-ink-dark px-6 py-2.5 font-display font-extrabold text-xs uppercase shadow-hard hover:bg-ink-dark hover:text-yellow-signal transition-none cursor-pointer w-full"
              >
                + ADD CONNECTION
              </button>
            </div>
          </div>
        )}

        {/* Connection grid */}
        {connections && connections.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {connections.map((conn) => (
              <ConnectionCard
                key={conn.id}
                connection={conn}
                onEdit={openEdit}
                onViewSchema={(id) => setSchemaConnectionId(id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Modals */}
      {formOpen && (
        <ConnectionForm
          existing={editTarget}
          onClose={() => {
            setFormOpen(false);
            setEditTarget(undefined);
          }}
        />
      )}

      {schemaConnectionId && schemaConnection && (
        <SchemaTree
          connectionId={schemaConnectionId}
          connectionName={schemaConnection.name}
          onClose={() => setSchemaConnectionId(null)}
        />
      )}
    </div>
  );
}
