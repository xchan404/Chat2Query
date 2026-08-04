"use client";

import React from "react";

interface AuditFilterBarProps {
  onExport?: () => void;
  count: number;
}

export function AuditFilterBar({ onExport, count }: AuditFilterBarProps) {
  return (
    <div className="flex items-center justify-between p-3.5 px-5 bg-white border-b border-gray-300">
      <div>
        <h1 className="font-semibold text-sm text-gray-900">
          Audit Trail &amp; Verification Logs
        </h1>
        <p className="text-xs text-gray-500 mt-0.5 font-normal">
          Immutable event log stream • Total recorded events: <span className="font-semibold text-gray-800">{count}</span>
        </p>
      </div>
      <button
        onClick={onExport}
        className="bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 font-medium text-xs px-3 py-1.5 rounded-md transition-colors cursor-pointer"
      >
        Export Logs (CSV)
      </button>
    </div>
  );
}
