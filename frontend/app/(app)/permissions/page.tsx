"use client";

import React from "react";

export default function PermissionsPage() {
  return (
    <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
      <div className="border-b-thick border-ink-dark pb-3 flex items-center justify-between">
        <h1 className="font-display text-2xl font-extrabold uppercase tracking-tight">
          Effective Schema &amp; Security Pipeline Rules
        </h1>
        <button className="bg-cobalt-signal text-white border-med border-ink-dark px-4 py-2 font-display font-extrabold text-xs uppercase shadow-sm hover:bg-yellow-signal hover:text-ink-dark cursor-pointer">
          + OVERRIDE RULE
        </button>
      </div>

      <div className="bg-white border-thick border-ink-dark shadow-hard overflow-x-auto">
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="bg-surface font-display font-extrabold text-xs uppercase border-b-thick border-ink-dark">
              <th className="p-3 border-r-med border-ink-dark">SCHEMA</th>
              <th className="p-3 border-r-med border-ink-dark">TABLE</th>
              <th className="p-3 border-r-med border-ink-dark">PERMITTED COLUMNS</th>
              <th className="p-3 border-r-med border-ink-dark">MASKED COLUMNS</th>
              <th className="p-3">SERVER-SIDE ROW FILTER (AST INJECTED)</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b-med border-ink-dark hover:bg-cobalt-bg">
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">public</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">invoices</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">id, customer_name, amount, status, created_at</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">None</td>
              <td className="p-3 font-mono text-xs font-extrabold text-cobalt-signal">tenant_id = 'e8f410a2-99c0'</td>
            </tr>
            <tr className="border-b-med border-ink-dark hover:bg-cobalt-bg">
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">public</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">customers</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">id, name, email, ssn</td>
              <td className="p-3 font-mono text-xs font-extrabold text-rust-warn border-r-med border-ink-dark">ssn [MASKED]</td>
              <td className="p-3 font-mono text-xs font-extrabold text-cobalt-signal">tenant_id = 'e8f410a2-99c0'</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
