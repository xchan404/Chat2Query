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

  const resourceStr = log.resource_type
    ? `${log.resource_type}${log.resource_id ? `:${log.resource_id.slice(0, 8)}` : ""}`
    : "system";

  return (
    <tr className="hover:bg-gray-50/80 transition-colors">
      <td className="p-3 font-mono text-[11px] text-gray-600 border-r border-gray-200">
        {formattedTime}
      </td>
      <td className="p-3 font-mono text-[11px] text-gray-700 border-r border-gray-200">
        {log.user_id ? `${log.user_id.slice(0, 8)}...` : "system"}
      </td>
      <td className="p-3 border-r border-gray-200">
        <span className="bg-gray-100 text-gray-800 border border-gray-200 font-mono text-[11px] font-medium px-2 py-0.5 rounded">
          {log.action}
        </span>
      </td>
      <td className="p-3 font-mono text-[11px] text-gray-600 border-r border-gray-200">
        {resourceStr}
      </td>
      <td className="p-3 border-r border-gray-200">
        <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-semibold px-2 py-0.5 rounded uppercase">
          Recorded
        </span>
      </td>
      <td className="p-3 font-normal text-xs text-gray-800">
        {log.description ?? "N/A"}
      </td>
    </tr>
  );
}
