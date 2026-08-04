"use client";

import React from "react";
import { type AuditLogOut } from "@/lib/api/audit";

interface AuditLogRowProps {
  log: AuditLogOut;
}

export function AuditLogRow({ log }: AuditLogRowProps) {
  // Format timestamp
  const formattedTime = log.created_at
    ? new Date(log.created_at).toISOString().replace("T", " ").substring(0, 19)
    : "—";

  // Action badge color mapping
  const actionUpper = log.action.toUpperCase();
  let actionColorClass = "bg-cobalt-bg text-cobalt-signal";
  if (actionUpper.includes("CHAT") || actionUpper.includes("EXECUTE")) {
    actionColorClass = "bg-purple-bg text-purple-signal";
  } else if (actionUpper.includes("LOGIN") || actionUpper.includes("AUTH")) {
    actionColorClass = "bg-emerald-bg text-emerald-pass";
  } else if (actionUpper.includes("PERMISSION") || actionUpper.includes("UPDATE")) {
    actionColorClass = "bg-yellow-bg text-yellow-signal";
  }

  const resourceStr = log.resource_type
    ? `${log.resource_type}${log.resource_id ? `:${log.resource_id.slice(0, 8)}` : ""}`
    : "system";

  return (
    <tr className="border-b-med border-ink-dark hover:bg-cobalt-bg transition-none">
      <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">
        {formattedTime}
      </td>
      <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">
        {log.user_id ? `${log.user_id.slice(0, 8)}...` : "system"}
      </td>
      <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">
        <span className={`${actionColorClass} px-1.5 py-0.5 border border-ink-dark font-extrabold`}>
          {log.action}
        </span>
      </td>
      <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">
        {resourceStr}
      </td>
      <td className="p-3 border-r-med border-ink-dark">
        <span className="font-mono text-[11px] font-extrabold px-2 py-0.5 border border-ink-dark uppercase bg-emerald-bg text-emerald-pass border-emerald-pass">
          LOGGED
        </span>
      </td>
      <td className="p-3 font-mono text-xs font-semibold">
        {log.description ?? "N/A"}
      </td>
    </tr>
  );
}
