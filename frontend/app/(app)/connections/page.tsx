"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { connectionsApi, type ConnectionOut } from "@/lib/api/connections";
import { ConnectionForm } from "@/components/connections/ConnectionForm";
import { SchemaTree } from "@/components/connections/SchemaTree";

export default function ConnectionsPage() {
  const queryClient = useQueryClient();
  const [formOpen, setFormOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<ConnectionOut | undefined>();
  const [schemaConnectionId, setSchemaConnectionId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ id: string; ok: boolean; msg: string } | null>(null);

  const {
    data: connections,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["connections"],
    queryFn: connectionsApi.list,
  });

  const testMutation = useMutation({
    mutationFn: (id: string) => connectionsApi.testConnection(id),
    onSuccess: (data, id) => {
      setTestResult({ id, ok: data.success, msg: data.message });
    },
    onError: (err: Error, id) => {
      setTestResult({ id, ok: false, msg: err.message });
    },
  });

  const syncMutation = useMutation({
    mutationFn: (id: string) => connectionsApi.syncSchema(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connections"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => connectionsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connections"] });
    },
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
    <div className="flex flex-col flex-1 min-h-0 overflow-hidden bg-gray-50">
      {/* Page Header */}
      <div className="flex items-center justify-between p-3.5 px-5 bg-white border-b border-gray-300">
        <div>
          <h1 className="font-semibold text-sm text-gray-900">
            Registered Database Connections
          </h1>
          <p className="text-xs text-gray-500 mt-0.5 font-normal">
            Tenant-scoped data sources configured for Text-to-SQL query generation
          </p>
        </div>
        <button
          id="btn-new-connection"
          onClick={openCreate}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs px-3.5 py-1.5 rounded-md transition-colors cursor-pointer"
        >
          + Add Connection
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-5">
        {/* Loading */}
        {isLoading && (
          <div className="bg-white border border-gray-300 rounded-md p-8 text-center text-xs text-gray-500">
            Loading connections...
          </div>
        )}

        {/* Error */}
        {isError && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 max-w-lg mb-4">
            <p className="font-semibold text-xs text-red-800">Failed to load database connections</p>
            <p className="text-xs text-red-600 mt-1">{error?.message}</p>
          </div>
        )}

        {/* Empty state */}
        {connections && connections.length === 0 && (
          <div className="bg-white border border-gray-300 rounded-md p-10 text-center max-w-md mx-auto my-12">
            <p className="text-sm font-semibold text-gray-800">No database connections registered</p>
            <p className="text-xs text-gray-500 mt-1">
              Add a PostgreSQL or MySQL connection to enable natural language querying.
            </p>
            <button
              onClick={openCreate}
              className="mt-4 bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs px-4 py-2 rounded-md transition-colors"
            >
              + Add First Connection
            </button>
          </div>
        )}

        {/* Connection Table */}
        {connections && connections.length > 0 && (
          <div className="bg-white border border-gray-300 rounded-md overflow-hidden shadow-sm">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 border-b border-gray-300 text-gray-600 font-semibold text-[11px] uppercase tracking-wider">
                <tr>
                  <th className="p-3 pl-4">Connection Name</th>
                  <th className="p-3">Engine Dialect</th>
                  <th className="p-3">Host / Port</th>
                  <th className="p-3">Target DB</th>
                  <th className="p-3">Schema Status</th>
                  <th className="p-3 pr-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 text-gray-900">
                {connections.map((conn) => (
                  <tr key={conn.id} className="hover:bg-gray-50 transition-colors">
                    <td className="p-3 pl-4 font-semibold text-gray-900">
                      {conn.name}
                      <span className="block font-mono text-[10px] text-gray-400 font-normal">
                        ID: {conn.id.slice(0, 16)}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className="bg-gray-100 border border-gray-300 px-2 py-0.5 rounded text-[11px] font-mono font-medium uppercase text-gray-700">
                        {conn.database_type}
                      </span>
                    </td>
                    <td className="p-3 font-mono text-gray-600 text-[11px]">
                      {conn.host}:{conn.port}
                    </td>
                    <td className="p-3 font-mono text-gray-800 text-[11px]">
                      {conn.database_name}
                    </td>
                    <td className="p-3">
                      {conn.is_active ? (
                        <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded text-[10px] font-semibold uppercase">
                          Active
                        </span>
                      ) : (
                        <span className="bg-gray-100 text-gray-600 border border-gray-200 px-2 py-0.5 rounded text-[10px] font-semibold uppercase">
                          Inactive
                        </span>
                      )}
                    </td>
                    <td className="p-3 pr-4 text-right space-x-2">
                      <button
                        onClick={() => testMutation.mutate(conn.id)}
                        disabled={testMutation.isPending}
                        className="text-blue-600 hover:text-blue-800 font-medium text-xs"
                      >
                        {testMutation.isPending && testMutation.variables === conn.id ? "Testing..." : "Test"}
                      </button>
                      <span className="text-gray-300">|</span>
                      <button
                        onClick={() => syncMutation.mutate(conn.id)}
                        disabled={syncMutation.isPending}
                        className="text-blue-600 hover:text-blue-800 font-medium text-xs"
                      >
                        {syncMutation.isPending && syncMutation.variables === conn.id ? "Syncing..." : "Sync Schema"}
                      </button>
                      <span className="text-gray-300">|</span>
                      <button
                        onClick={() => setSchemaConnectionId(conn.id)}
                        className="text-blue-600 hover:text-blue-800 font-medium text-xs"
                      >
                        Schema Tree
                      </button>
                      <span className="text-gray-300">|</span>
                      <button
                        onClick={() => openEdit(conn)}
                        className="text-gray-600 hover:text-gray-900 font-medium text-xs"
                      >
                        Edit
                      </button>
                      <span className="text-gray-300">|</span>
                      <button
                        onClick={() => {
                          if (confirm(`Delete connection "${conn.name}"?`)) {
                            deleteMutation.mutate(conn.id);
                          }
                        }}
                        className="text-red-600 hover:text-red-800 font-medium text-xs"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Test Result Alert */}
        {testResult && (
          <div
            className={`mt-4 p-3 rounded-md text-xs border ${
              testResult.ok
                ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                : "bg-red-50 border-red-200 text-red-800"
            }`}
          >
            <span className="font-semibold">Test Status:</span> {testResult.msg}
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
