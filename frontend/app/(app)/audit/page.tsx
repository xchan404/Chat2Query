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
    enabled: !!isAdmin, // Only fetch if user is admin
    staleTime: 0, // Always fresh when visiting page
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
      <div className="flex-1 p-6 font-mono text-xs uppercase text-ink-muted">
        Loading Session Authentication...
      </div>
    );
  }

  // Admin authorization gate check
  if (!user || !isAdmin) {
    return (
      <div className="flex-1 p-6 flex flex-col items-center justify-center gap-4">
        <div className="bg-red-50 border-thick border-ink-dark p-6 shadow-hard text-center max-w-md">
          <div className="font-display text-xl font-extrabold text-red-600 uppercase mb-2">
            403 — Access Denied
          </div>
          <p className="font-mono text-xs text-ink-dark mb-4">
            Audit logs contain sensitive security metrics and are strictly gated to users with the <span className="font-bold">admin</span> role.
          </p>
          <div className="font-mono text-[11px] bg-paper p-2 border border-ink-dark text-ink-muted">
            CURRENT USER: {user?.username ?? "Anonymous"} ({user?.roles?.join(", ") || "no roles"})
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
      <AuditFilterBar onExport={handleExportCSV} count={logs?.length ?? 0} />

      <div className="bg-white border-thick border-ink-dark shadow-hard overflow-x-auto">
        {logsLoading ? (
          <div className="p-8 text-center font-mono text-xs text-ink-muted uppercase">
            Loading Audit Records...
          </div>
        ) : isError ? (
          <div className="p-8 text-center font-mono text-xs text-red-600 uppercase">
            Failed to load audit logs: {(error as Error)?.message ?? "Unknown Error"}
          </div>
        ) : !logs || logs.length === 0 ? (
          <div className="p-8 text-center font-mono text-xs text-ink-muted uppercase">
            No audit records found.
          </div>
        ) : (
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="bg-surface font-display font-extrabold text-xs uppercase border-b-thick border-ink-dark">
                <th className="p-3 border-r-med border-ink-dark">TIMESTAMP (UTC)</th>
                <th className="p-3 border-r-med border-ink-dark">USER ID</th>
                <th className="p-3 border-r-med border-ink-dark">ACTION</th>
                <th className="p-3 border-r-med border-ink-dark">RESOURCE</th>
                <th className="p-3 border-r-med border-ink-dark">STATUS</th>
                <th className="p-3">DESCRIPTION</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <AuditLogRow key={log.id} log={log} />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
