"use client";

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
    <aside className="w-[360px] max-[860px]:fixed max-[860px]:right-0 max-[860px]:top-12 max-[860px]:bottom-0 max-[860px]:z-40 max-[860px]:shadow-lg max-[860px]:w-[320px] bg-white flex flex-col min-w-0 h-full shrink-0 border-l border-gray-300">
      {/* Header */}
      <div className="bg-gray-100 text-gray-900 p-2.5 px-3 font-semibold text-xs border-b border-gray-300 flex items-center justify-between">
        <span className="font-semibold text-gray-800">ANALYSIS & EXECUTION LEDGER</span>
        <span className="bg-emerald-100 text-emerald-800 text-[10px] font-mono px-1.5 py-0.5 rounded border border-emerald-300 font-semibold">
          LIVE
        </span>
      </div>

      {/* Structured Tab Bar */}
      <div className="flex bg-gray-50 border-b border-gray-300 text-xs">
        <button
          onClick={() => setActiveTab("sql")}
          className={`flex-1 py-2 px-1 font-medium text-xs transition-colors cursor-pointer border-r border-gray-200 ${
            activeTab === "sql"
              ? "bg-white text-blue-700 font-semibold border-b-2 border-blue-600"
              : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
          }`}
        >
          SQL {hasSql && "•"}
        </button>
        <button
          onClick={() => setActiveTab("citations")}
          className={`flex-1 py-2 px-1 font-medium text-xs transition-colors cursor-pointer border-r border-gray-200 ${
            activeTab === "citations"
              ? "bg-white text-blue-700 font-semibold border-b-2 border-blue-600"
              : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
          }`}
        >
          CITATIONS ({citations.length})
        </button>
        <button
          onClick={() => setActiveTab("raw")}
          className={`flex-1 py-2 px-1 font-medium text-xs transition-colors cursor-pointer ${
            activeTab === "raw"
              ? "bg-white text-blue-700 font-semibold border-b-2 border-blue-600"
              : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
          }`}
        >
          RAW LOGS
        </button>
      </div>

      {/* Dense Content Panel */}
      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-3 bg-gray-50/50">
        {activeTab === "sql" && (
          <>
            {hasSql ? (
              <SqlEvidenceCard
                sqlResult={sqlResult!}
                executionId={queryExecutionId}
              />
            ) : (
              <div className="p-4 text-center border border-dashed border-gray-300 rounded-md bg-white">
                <p className="font-mono text-xs font-semibold text-gray-500">
                  NO SQL EXECUTED
                </p>
                <p className="text-[11px] text-gray-400 mt-1">
                  Query intent: {intent ?? "pending"}. SQL AST output renders here upon query execution.
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
              <div className="p-4 text-center border border-dashed border-gray-300 rounded-md bg-white">
                <p className="font-mono text-xs font-semibold text-gray-500">
                  NO CITATIONS RETRIEVED
                </p>
                <p className="text-[11px] text-gray-400 mt-1">
                  Document chunk citations appear when knowledge bases are queried.
                </p>
              </div>
            )}
          </>
        )}

        {activeTab === "raw" && (
          <div className="flex flex-col gap-1.5">
            <span className="font-mono text-[10px] font-semibold text-gray-500 uppercase">
              PAYLOAD LOG:
            </span>
            <pre className="bg-gray-900 text-gray-100 font-mono text-[11px] p-3 rounded-md border border-gray-800 whitespace-pre-wrap overflow-x-auto">
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
