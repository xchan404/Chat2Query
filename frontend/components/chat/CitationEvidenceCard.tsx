"use client";

/**
 * CitationEvidenceCard — displays document citations, chunk snippets, page numbers, and source type.
 */

import React from "react";
import { type CitationOut } from "@/lib/api/chat";

interface CitationEvidenceCardProps {
  citation: CitationOut;
  index: number;
}

export function CitationEvidenceCard({ citation, index }: CitationEvidenceCardProps) {
  return (
    <div className="bg-white border-thick border-ink-dark p-3.5 shadow-sm flex flex-col gap-2 border-t-[5px] border-t-cyan-signal">
      <div className="flex items-center justify-between font-mono text-[11px] font-extrabold border-b-med border-ink-dark pb-1.5">
        <span className="text-cyan-signal font-extrabold">
          [CIT-{String(index + 1).padStart(3, "0")}] DOCUMENT CHUNK
        </span>
        <span className="bg-cyan-bg text-cyan-signal px-1.5 py-0.5 border border-ink-dark font-extrabold uppercase text-[10px]">
          {citation.source_type || "DOCUMENT"}
        </span>
      </div>

      <div className="flex items-center justify-between font-mono text-xs font-bold text-ink-dark">
        <span className="truncate max-w-[200px]" title={citation.file_name ?? undefined}>
          📄 {citation.file_name ?? "Document"}
        </span>
        {citation.page_number != null && (
          <span className="bg-yellow-bg px-1.5 py-0.5 border border-ink-dark text-[10px]">
            PAGE {citation.page_number}
          </span>
        )}
      </div>

      {citation.chunk_id && (
        <div className="font-mono text-[10px] text-ink-muted truncate">
          CHUNK ID: {citation.chunk_id}
        </div>
      )}

      {citation.snippet && (
        <div className="mt-1">
          <span className="font-mono text-[10px] font-extrabold uppercase text-ink-muted block mb-1">
            RETRIEVED TEXT SNIPPET:
          </span>
          <p className="bg-paper p-2.5 border-med border-ink-dark font-body text-xs leading-relaxed text-ink-dark italic">
            "{citation.snippet}"
          </p>
        </div>
      )}
    </div>
  );
}
