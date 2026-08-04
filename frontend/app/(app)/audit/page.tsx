"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth/AuthProvider";
import { auditApi, type AuditLogOut } from "@/lib/api/audit";
import { AuditFilterBar } from "@/components/audit/AuditFilterBar";
import { AuditLogRow } from "@/components/audit/AuditLogRow";

export default function AuditPage() {
  const { user, isLoading: authLoading } = useAuth();
  const isAdmin = user?.roles?.includes("admin");

  const { data: logs, isLoading: logsLoading, isError, error } = useQuery<AuditLogOut[]>({
    queryKey: ["audit-logs"],
    queryFn: () => auditApi.getAuditLogs(),
    enabled: !!isAdmin,
    staleTime: 0,
  });

  const handleExportCSV = () => {
    if (!logs || logs.length === 0) return;
    const headers = ["TIMESTAMP", "USER_ID", "ACTION", "RESOURCE_TYPE", "RESOURCE_ID", "DESCRIPTION"];
    const rows = logs.map((l) => [
      l.created_at ?? "",
      l.user_id ?? "",
      l.action,
      l.resource_type ?? "",
      l.resource_id ?? "",
      l.description ?? "",
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `audit_logs_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (authLoading) {
    return (
      <div className="flex-1 p-6 text-xs text-gray-500 font-mono">
        Loading Session Authentication...
      </div>
    );
  }

  // Admin authorization gate check
  if (!user || !isAdmin) {
    return (
      <div className="flex-1 p-6 flex flex-col items-center justify-center gap-4 bg-gray-50">
        <div className="bg-white border border-gray-300 rounded-md p-6 text-center max-w-md shadow-sm">
          <div className="text-sm font-semibold text-red-600 mb-2">
            403 — Access Restricted
          </div>
          <p className="text-xs text-gray-600 mb-4">
            Audit logs contain sensitive security metrics and are strictly gated to users with the <span className="font-semibold text-gray-800">admin</span> role.
          </p>
          <div className="text-[11px] font-mono bg-gray-50 p-2 rounded border border-gray-200 text-gray-600">
            CURRENT USER: {user?.username ?? "Anonymous"} ({user?.roles?.join(", ") || "no roles"})
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-hidden bg-gray-50">
      <AuditFilterBar onExport={handleExportCSV} count={logs?.length ?? 0} />

      <div className="flex-1 overflow-y-auto p-5">
        <div className="bg-white border border-gray-300 rounded-md overflow-hidden shadow-sm">
          {logsLoading ? (
            <div className="p-8 text-center text-xs text-gray-500 font-mono">
              Loading audit logs...
            </div>
          ) : isError ? (
            <div className="p-8 text-center text-xs text-red-600 font-mono">
              Failed to load audit logs: {(error as Error)?.message ?? "Unknown Error"}
            </div>
          ) : !logs || logs.length === 0 ? (
            <div className="p-8 text-center text-xs text-gray-500 font-mono">
              No audit records found.
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-gray-50 border-b border-gray-300 font-semibold text-[11px] uppercase tracking-wider text-gray-600">
                <tr>
                  <th className="p-3 border-r border-gray-200">TIMESTAMP (UTC)</th>
                  <th className="p-3 border-r border-gray-200">USER ID</th>
                  <th className="p-3 border-r border-gray-200">ACTION</th>
                  <th className="p-3 border-r border-gray-200">RESOURCE</th>
                  <th className="p-3 border-r border-gray-200">STATUS</th>
                  <th className="p-3">DESCRIPTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 text-gray-900">
                {logs.map((log) => (
                  <AuditLogRow key={log.id} log={log} />
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
