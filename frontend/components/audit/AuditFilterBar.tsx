"use client";

import React from "react";

interface AuditFilterBarProps {
  onExport?: () => void;
  count: number;
}

export function AuditFilterBar({ onExport, count }: AuditFilterBarProps) {
  return (
    <div className="border-b-thick border-ink-dark pb-3 flex items-center justify-between">
      <div>
        <h1 className="font-display text-2xl font-extrabold uppercase tracking-tight">
          Audit Trail &amp; Verification Logs
        </h1>
        <div className="font-mono text-xs text-ink-muted mt-1">
          TOTAL RECORDED EVENTS: <span className="font-bold text-ink-dark">{count}</span>
        </div>
      </div>
      <button
        onClick={onExport}
        className="bg-ink-dark text-white border-med border-ink-dark px-4 py-2 font-display font-extrabold text-xs uppercase shadow-sm hover:bg-yellow-signal hover:text-ink-dark cursor-pointer transition-none"
      >
        EXPORT LOGS (CSV)
      </button>
    </div>
  );
}
