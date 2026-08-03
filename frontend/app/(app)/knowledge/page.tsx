"use client";

import React from "react";

export default function KnowledgePage() {
  return (
    <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
      <div className="border-b-thick border-ink-dark pb-3 flex items-center justify-between">
        <h1 className="font-display text-2xl font-extrabold uppercase tracking-tight">
          Knowledge Bases &amp; Vector Stores
        </h1>
        <button className="bg-cobalt-signal text-white border-med border-ink-dark px-4 py-2 font-display font-extrabold text-xs uppercase shadow-sm hover:bg-yellow-signal hover:text-ink-dark cursor-pointer">
          + CREATE KNOWLEDGE BASE
        </button>
      </div>

      <div className="bg-white border-thick border-ink-dark shadow-hard overflow-x-auto">
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="bg-surface font-display font-extrabold text-xs uppercase border-b-thick border-ink-dark">
              <th className="p-3 border-r-med border-ink-dark">FILE NAME</th>
              <th className="p-3 border-r-med border-ink-dark">TYPE</th>
              <th className="p-3 border-r-med border-ink-dark">SIZE</th>
              <th className="p-3 border-r-med border-ink-dark">PAGES</th>
              <th className="p-3 border-r-med border-ink-dark">CHUNKS</th>
              <th className="p-3 border-r-med border-ink-dark">EMBEDDING MODEL</th>
              <th className="p-3 border-r-med border-ink-dark">STATUS</th>
              <th className="p-3">ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b-med border-ink-dark hover:bg-cobalt-bg">
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">master_services_agreement.pdf</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">
                <span className="bg-rust-bg text-rust-warn px-1.5 py-0.5 border border-ink-dark font-extrabold">PDF</span>
              </td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">1.4 MB</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">2</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">4</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">BAAI/bge-m3 (1024d)</td>
              <td className="p-3 border-r-med border-ink-dark">
                <span className="font-mono text-[11px] font-extrabold px-2 py-0.5 border border-emerald-pass bg-emerald-bg text-emerald-pass uppercase">COMPLETED</span>
              </td>
              <td className="p-3">
                <button className="bg-ink-dark text-white border-med border-ink-dark px-3 py-1 font-display font-extrabold text-xs uppercase hover:bg-yellow-signal hover:text-ink-dark cursor-pointer">
                  REPROCESS
                </button>
              </td>
            </tr>
            <tr className="border-b-med border-ink-dark hover:bg-cobalt-bg">
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">q3_financial_statements.xlsx</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">
                <span className="bg-emerald-bg text-emerald-pass px-1.5 py-0.5 border border-ink-dark font-extrabold">XLSX</span>
              </td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">480 KB</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">N/A</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">12</td>
              <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark">BAAI/bge-m3 (1024d)</td>
              <td className="p-3 border-r-med border-ink-dark">
                <span className="font-mono text-[11px] font-extrabold px-2 py-0.5 border border-emerald-pass bg-emerald-bg text-emerald-pass uppercase">COMPLETED</span>
              </td>
              <td className="p-3">
                <button className="bg-ink-dark text-white border-med border-ink-dark px-3 py-1 font-display font-extrabold text-xs uppercase hover:bg-yellow-signal hover:text-ink-dark cursor-pointer">
                  REPROCESS
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
