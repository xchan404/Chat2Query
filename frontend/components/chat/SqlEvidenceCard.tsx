"use client";

/**
 * SqlEvidenceCard — displays validated SQL AST pipeline results,
 * generated SQL, row count, and live tabular output.
 */

import React from "react";
import { type SQLResultOut } from "@/lib/api/chat";

interface SqlEvidenceCardProps {
  sqlResult: SQLResultOut;
  dialect?: string;
  executionId?: string | null;
}

export function SqlEvidenceCard({
  sqlResult,
  dialect = "PostgreSQL",
  executionId,
}: SqlEvidenceCardProps) {
  const rows = sqlResult.rows ?? [];
  const columns = rows.length > 0 ? Object.keys(rows[0]) : [];

  return (
    <div className="bg-white border-thick border-ink-dark p-3.5 shadow-sm flex flex-col gap-2.5 border-t-[5px] border-t-cobalt-signal">
      <div className="flex items-center justify-between font-mono text-[11px] font-extrabold border-b-med border-ink-dark pb-1.5">
        <span>[EVD-001] SQL AST PIPELINE</span>
        <span className="bg-emerald-bg text-emerald-pass px-1.5 py-0.5 border border-ink-dark font-extrabold">
          VALIDATED
        </span>
      </div>

      <div className="font-mono text-xs font-semibold">
        DIALECT: <span className="text-cobalt-signal font-bold">{dialect}</span>
      </div>

      {executionId && (
        <div className="font-mono text-[11px] font-semibold text-ink-muted truncate">
          EXECUTION ID: {executionId}
        </div>
      )}

      {sqlResult.generated_sql && (
        <div className="flex flex-col gap-1">
          <span className="font-mono text-[10px] font-extrabold uppercase text-ink-muted">
            GENERATED SQL:
          </span>
          <pre className="bg-code-bg text-code-fg font-mono text-xs p-2.5 border-med border-ink-dark whitespace-pre-wrap overflow-x-auto">
            {sqlResult.generated_sql}
          </pre>
        </div>
      )}

      <div className="font-mono text-xs font-semibold mt-1">
        LIVE RESULT ({sqlResult.row_count ?? rows.length} ROW
        {(sqlResult.row_count ?? rows.length) === 1 ? "" : "S"}):
      </div>

      {rows.length > 0 ? (
        <div className="overflow-x-auto border-med border-ink-dark">
          <table className="w-full border-collapse font-mono text-[11px] bg-white">
            <thead>
              <tr className="bg-cobalt-bg text-cobalt-signal border-b-med border-ink-dark">
                {columns.map((col) => (
                  <th
                    key={col}
                    className="text-left p-1.5 border-r-med border-ink-dark font-extrabold last:border-r-0"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr key={idx} className="border-b-thin border-ink-dark last:border-b-0 hover:bg-surface-alt">
                  {columns.map((col) => (
                    <td
                      key={col}
                      className="p-1.5 border-r-thin border-ink-dark last:border-r-0 font-medium"
                    >
                      {row[col] != null ? String(row[col]) : <span className="text-ink-muted italic">NULL</span>}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="font-mono text-xs text-ink-muted italic p-2 bg-surface border-med border-ink-dark text-center">
          0 rows returned
        </div>
      )}
    </div>
  );
}
