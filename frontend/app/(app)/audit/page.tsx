"use client";

import React from "react";

export default function AuditPage() {
  return (
    <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
      <div className="border-b-thick border-ink-dark pb-3 flex items-center justify-between">
        <h1 className="font-display text-2xl font-extrabold uppercase tracking-tight">
          Audit Trail &amp; Verification Logs
        </h1>
        <button className="bg-ink-dark text-white border-med border-ink-dark px-4 py-2 font-display font-extrabold text-xs uppercase shadow-sm hover:bg-yellow-signal hover:text-ink-dark cursor-pointer">
          EXPORT LOGS (CSV)
        </button>
      </div>

      <div className="bg-white border-thick border-ink-dark shadow-hard overflow-x-auto">
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="bg-surface font-display font-extrabold text-xs uppercase border-b-thick border-ink-dark">
              <th className="p-3 border-r-med border-ink-dark">TIMESTAMP (UTC)</th>
              <th className="p-3 border-r-med border-ink-dark">USER ID</th>
              <th className="p-3 border-r-med border-ink-dark">ACTION</th>
              <th className="p-3 border-r-med border-ink-dark">RESOURCE</th>
              <th className="p-3 border-r-med border-ink-dark">STATUS</th>
              <th className="p-3">QUERY EXEC ID</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b-med border-ink-dark hover:bg-cobalt-bg">
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">2026-08-03 11:42:03</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">usr-9012</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">
                <span className="bg-purple-bg text-purple-signal px-1.5 py-0.5 border border-ink-dark font-extrabold">CHAT_QUERY_EXECUTE</span>
              </td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">public.invoices</td>
              <td className="p-3 border-r-med border-ink-dark">
                <span className="font-mono text-[11px] font-extrabold px-2 py-0.5 border border-emerald-pass bg-emerald-bg text-emerald-pass uppercase">APPROVED</span>
              </td>
              <td className="p-3 font-mono text-xs font-semibold">b0e65c0f-7a5e-41d1-97bd-00b694f57240</td>
            </tr>
            <tr className="border-b-med border-ink-dark hover:bg-cobalt-bg">
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">2026-08-03 11:30:12</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">usr-9012</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">
                <span className="bg-cobalt-bg text-cobalt-signal px-1.5 py-0.5 border border-ink-dark font-extrabold">CONNECTION_TEST</span>
              </td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">Prod-Postgres-Primary</td>
              <td className="p-3 border-r-med border-ink-dark">
                <span className="font-mono text-[11px] font-extrabold px-2 py-0.5 border border-emerald-pass bg-emerald-bg text-emerald-pass uppercase">SUCCESS</span>
              </td>
              <td className="p-3 font-mono text-xs font-semibold">N/A</td>
            </tr>
            <tr className="border-b-med border-ink-dark hover:bg-cobalt-bg">
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">2026-08-03 11:15:00</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">usr-9012</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">
                <span className="bg-emerald-bg text-emerald-pass px-1.5 py-0.5 border border-ink-dark font-extrabold">AUTH_LOGIN_SUCCESS</span>
              </td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">/api/auth/login</td>
              <td className="p-3 border-r-med border-ink-dark">
                <span className="font-mono text-[11px] font-extrabold px-2 py-0.5 border border-emerald-pass bg-emerald-bg text-emerald-pass uppercase">SUCCESS</span>
              </td>
              <td className="p-3 font-mono text-xs font-semibold">N/A</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
