"use client";

/**
 * EvidenceRail — exposed evidence ledger panel with tabbed navigation:
 *   - SQL EXECUTION (SqlEvidenceCard)
 *   - DOC CITATIONS (CitationEvidenceCard)
 *   - RAW PAYLOAD (formatted JSON of in-flight evidence)
 */

import React, { useState } from "react";
import { type SQLResultOut, type CitationOut } from "@/lib/api/chat";
import { SqlEvidenceCard } from "./SqlEvidenceCard";
import { CitationEvidenceCard } from "./CitationEvidenceCard";

interface EvidenceRailProps {
  sqlResult?: SQLResultOut | null;
  citations?: CitationOut[];
  intent?: string | null;
  queryExecutionId?: string | null;
}

type TabType = "sql" | "citations" | "raw";

export function EvidenceRail({
  sqlResult,
  citations = [],
  intent,
  queryExecutionId,
}: EvidenceRailProps) {
  const [activeTab, setActiveTab] = useState<TabType>("sql");

  const hasSql = !!(sqlResult && (sqlResult.generated_sql || (sqlResult.rows && sqlResult.rows.length > 0)));
  const hasCitations = citations.length > 0;

  return (
    <aside className="w-[350px] bg-surface flex flex-col min-w-0 h-full shrink-0 border-l-thick border-ink-dark">
      {/* Header */}
      <div className="bg-ink-dark text-white p-2.5 px-3.5 font-display font-extrabold text-xs uppercase tracking-wider flex items-center justify-between border-b-thick border-ink-dark">
        <span>EXPOSED EVIDENCE LEDGER</span>
        <span className="bg-yellow-signal text-ink-dark px-1.5 py-0.5 font-mono text-[11px] font-extrabold">
          LIVE
        </span>
      </div>

      {/* Tabs */}
      <div className="flex bg-surface-alt border-b-thick border-ink-dark">
        <button
          onClick={() => setActiveTab("sql")}
          className={`flex-1 py-2 px-1 font-mono text-[11px] font-extrabold uppercase transition-none cursor-pointer ${
            activeTab === "sql"
              ? "bg-yellow-signal text-ink-dark border-b-4 border-ink-dark"
              : "bg-surface text-ink-muted hover:bg-paper"
          }`}
        >
          SQL EXECUTION {hasSql && "•"}
        </button>
        <button
          onClick={() => setActiveTab("citations")}
          className={`flex-1 py-2 px-1 font-mono text-[11px] font-extrabold uppercase transition-none cursor-pointer border-r-med border-l-med border-ink-dark ${
            activeTab === "citations"
              ? "bg-yellow-signal text-ink-dark border-b-4 border-ink-dark"
              : "bg-surface text-ink-muted hover:bg-paper"
          }`}
        >
          CITATIONS ({citations.length})
        </button>
        <button
          onClick={() => setActiveTab("raw")}
          className={`flex-1 py-2 px-1 font-mono text-[11px] font-extrabold uppercase transition-none cursor-pointer ${
            activeTab === "raw"
              ? "bg-yellow-signal text-ink-dark border-b-4 border-ink-dark"
              : "bg-surface text-ink-muted hover:bg-paper"
          }`}
        >
          RAW PAYLOAD
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-3.5 flex flex-col gap-4">
        {activeTab === "sql" && (
          <>
            {hasSql ? (
              <SqlEvidenceCard
                sqlResult={sqlResult!}
                executionId={queryExecutionId}
              />
            ) : (
              <div className="p-6 text-center border-med border-dashed border-ink-muted/50 bg-paper">
                <p className="font-mono text-xs font-bold text-ink-muted uppercase tracking-wider">
                  // NO SQL EVIDENCE
                </p>
                <p className="font-mono text-[11px] text-ink-muted mt-2">
                  Query intent: {intent ?? "pending"}. SQL is generated when database queries execute.
                </p>
              </div>
            )}
          </>
        )}

        {activeTab === "citations" && (
          <>
            {hasCitations ? (
              citations.map((cite, idx) => (
                <CitationEvidenceCard key={idx} citation={cite} index={idx} />
              ))
            ) : (
              <div className="p-6 text-center border-med border-dashed border-ink-muted/50 bg-paper">
                <p className="font-mono text-xs font-bold text-ink-muted uppercase tracking-wider">
                  // NO DOCUMENT CITATIONS
                </p>
                <p className="font-mono text-[11px] text-ink-muted mt-2">
                  Document chunk citations appear when knowledge base documents are retrieved.
                </p>
              </div>
            )}
          </>
        )}

        {activeTab === "raw" && (
          <div className="flex flex-col gap-2">
            <span className="font-mono text-[10px] font-extrabold uppercase text-ink-muted">
              JSON PAYLOAD STREAM:
            </span>
            <pre className="bg-code-bg text-code-fg font-mono text-[11px] p-3 border-med border-ink-dark whitespace-pre-wrap overflow-x-auto">
              {JSON.stringify(
                {
                  intent,
                  query_execution_id: queryExecutionId,
                  sql_result: sqlResult,
                  citations,
                },
                null,
                2
              )}
            </pre>
          </div>
        )}
      </div>
    </aside>
  );
}
