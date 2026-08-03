"use client";

import React from "react";
import { useUIStore } from "@/lib/stores/uiStore";

export default function ChatPage() {
  const { isEvidenceRailOpen, toggleEvidenceRail } = useUIStore();

  return (
    <div className="flex flex-1 min-h-0 overflow-hidden">
      {/* Workspace Area */}
      <div className="flex-1 flex flex-col min-w-0 border-r-thick border-ink-dark">
        {/* Workspace Topbar */}
        <div className="flex items-center justify-between p-2.5 px-4 bg-surface border-b-thick border-ink-dark gap-3">
          <div className="flex items-center gap-2.5">
            <div className="flex items-center gap-1.5 bg-cobalt-bg border-med border-cobalt-signal px-2.5 py-1 font-mono text-xs font-bold text-cobalt-signal shadow-sm">
              <span>DB:</span>
              <select className="bg-transparent border-none font-bold outline-none cursor-pointer">
                <option>Prod Postgres v16 (Live)</option>
                <option>Analytics Replica MySQL</option>
              </select>
            </div>
            <div className="flex items-center gap-1.5 bg-cyan-bg border-med border-cyan-signal px-2.5 py-1 font-mono text-xs font-bold text-cyan-signal shadow-sm">
              <span>KB:</span>
              <select className="bg-transparent border-none font-bold outline-none cursor-pointer">
                <option>Q3 Financial Reports</option>
                <option>Master Agreements PDF</option>
              </select>
            </div>
          </div>
          <button
            onClick={toggleEvidenceRail}
            className="bg-ink-dark text-white border-med border-ink-dark px-3 py-1.5 font-display font-bold text-xs uppercase shadow-sm hover:bg-yellow-signal hover:text-ink-dark cursor-pointer transition-none"
          >
            TOGGLE EVIDENCE RAIL
          </button>
        </div>

        {/* Chat Content Area */}
        <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-5">
          <div className="flex flex-col gap-1.5 max-w-[840px]">
            <div className="flex items-center gap-2.5 font-mono text-xs font-bold">
              <span className="bg-yellow-signal text-ink-dark px-2 py-0.5 border-med border-ink-dark uppercase font-extrabold">
                USER
              </span>
              <span>11:42:01 AM</span>
            </div>
            <div className="bg-white border-thick border-ink-dark p-4 border-l-8 border-l-yellow-signal shadow-sm font-body text-sm">
              What is the total revenue in Q3 invoice records compared to the contract maximum cap specified in the agreement PDF?
            </div>
          </div>

          <div className="flex flex-col gap-1.5 max-w-[840px]">
            <div className="flex items-center gap-2.5 font-mono text-xs font-bold">
              <span className="bg-purple-signal text-white px-2 py-0.5 border-med border-ink-dark uppercase font-extrabold">
                ASSISTANT // HYBRID INTENT (CONF: 0.94)
              </span>
              <span>11:42:03 AM</span>
            </div>
            <div className="bg-white border-thick border-ink-dark p-4 border-l-8 border-l-purple-signal shadow-sm font-body text-sm">
              Total Q3 invoice revenue calculated from the live <code>invoices</code> table is <strong>$44,500.50</strong> across 3 paid records.
              <br /><br />
              According to page 1 of <code>master_services_agreement.pdf</code>, the maximum annual contract budget value is capped at <strong>$500,000.00</strong>. Current utilization sits at 8.9% of contract allocation.
            </div>
          </div>
        </div>

        {/* Chat Input Bar */}
        <div className="p-3.5 px-5 bg-surface border-t-thick border-ink-dark flex gap-3">
          <input
            type="text"
            className="flex-1 bg-white border-thick border-ink-dark p-3 font-body text-sm font-semibold shadow-sm outline-none"
            placeholder="Ask database query or search document knowledge base..."
            defaultValue="Count total pending invoices in public.invoices"
          />
          <button className="bg-yellow-signal text-ink-dark border-thick border-ink-dark px-6 font-display font-extrabold text-sm uppercase shadow-hard hover:bg-ink-dark hover:text-yellow-signal cursor-pointer">
            SEND [ENTER]
          </button>
        </div>
      </div>

      {/* Evidence Rail Side Panel */}
      {isEvidenceRailOpen && (
        <aside className="w-[350px] bg-surface flex flex-col min-w-0 h-full shrink-0">
          <div className="bg-ink-dark text-white p-2.5 px-3.5 font-display font-extrabold text-xs uppercase tracking-wider flex items-center justify-between border-b-thick border-ink-dark">
            <span>EXPOSED EVIDENCE LEDGER</span>
            <span className="bg-yellow-signal text-ink-dark px-1.5 py-0.5 font-mono text-[11px] font-extrabold">
              LIVE
            </span>
          </div>

          <div className="flex bg-surface-alt border-b-thick border-ink-dark">
            <button className="flex-1 py-2 px-1 font-mono text-[11px] font-extrabold uppercase bg-yellow-signal text-ink-dark border-b-4 border-ink-dark cursor-pointer">
              SQL EXECUTION
            </button>
            <button className="flex-1 py-2 px-1 font-mono text-[11px] font-extrabold uppercase bg-surface text-ink-muted border-r-med border-ink-dark hover:bg-paper cursor-pointer">
              DOC CITATIONS
            </button>
            <button className="flex-1 py-2 px-1 font-mono text-[11px] font-extrabold uppercase bg-surface text-ink-muted hover:bg-paper cursor-pointer">
              RAW PAYLOAD
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-3.5 flex flex-col gap-4">
            <div className="bg-white border-thick border-ink-dark p-3.5 shadow-sm flex flex-col gap-2.5 border-t-[5px] border-t-cobalt-signal">
              <div className="flex items-center justify-between font-mono text-[11px] font-extrabold border-b-med border-ink-dark pb-1.5">
                <span>[EVD-001] SQL AST PIPELINE</span>
                <span className="bg-emerald-bg text-emerald-pass px-1.5 py-0.5 border border-ink-dark font-extrabold">
                  VALIDATED
                </span>
              </div>
              <div className="font-mono text-xs font-semibold">DIALECT: PostgreSQL</div>
              <div className="font-mono text-xs font-semibold">EXECUTION ID: b0e65c0f-7a5e-41d1-97bd-00b694f57240</div>
              <pre className="bg-code-bg text-code-fg font-mono text-xs p-2.5 border-med border-ink-dark whitespace-pre-wrap">
                SELECT SUM(amount) AS total_payments FROM invoices LIMIT 1000;
              </pre>
              <div className="font-mono text-xs font-semibold">LIVE RESULT (1 ROW / 1.5ms):</div>
              <table className="w-full border-collapse font-mono text-[11px] bg-white border-med border-ink-dark">
                <thead>
                  <tr className="bg-cobalt-bg text-cobalt-signal border-b-med border-ink-dark">
                    <th className="text-left p-1.5 border-r-med border-ink-dark font-extrabold">total_payments</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="p-1.5 border-r-thin border-ink-dark">$44,500.50</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </aside>
      )}
    </div>
  );
}
