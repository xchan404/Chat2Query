"use client";

/**
 * KnowledgeBaseHeader — top action bar with KB dropdown selector,
 * "+ CREATE KNOWLEDGE BASE" button, and active KB delete action.
 */

import React from "react";
import { type KnowledgeBaseOut } from "@/lib/api/knowledgeBases";

interface KnowledgeBaseHeaderProps {
  knowledgeBases: KnowledgeBaseOut[];
  selectedKbId: string | null;
  setSelectedKbId: (id: string | null) => void;
  onOpenCreateModal: () => void;
  onDeleteKb: (id: string) => void;
}

export function KnowledgeBaseHeader({
  knowledgeBases,
  selectedKbId,
  setSelectedKbId,
  onOpenCreateModal,
  onDeleteKb,
}: KnowledgeBaseHeaderProps) {
  const currentKb = knowledgeBases.find((kb) => kb.id === selectedKbId);

  return (
    <div className="flex flex-col gap-4 bg-surface p-4 border-thick border-ink-dark shadow-sm">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="font-display font-extrabold text-sm uppercase text-ink-dark">
            KNOWLEDGE BASE:
          </span>
          <select
            id="kb-selector"
            value={selectedKbId ?? ""}
            onChange={(e) => setSelectedKbId(e.target.value || null)}
            className="bg-white border-med border-ink-dark p-2 font-mono text-xs font-bold text-ink-dark outline-none cursor-pointer min-w-[240px]"
          >
            {knowledgeBases.length === 0 && (
              <option value="">-- No Knowledge Bases Created --</option>
            )}
            {knowledgeBases.map((kb) => (
              <option key={kb.id} value={kb.id}>
                {kb.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          {currentKb && (
            <button
              id="delete-kb-btn"
              onClick={() => onDeleteKb(currentKb.id)}
              className="bg-rust-bg text-rust-warn border-med border-ink-dark px-3 py-2 font-display font-extrabold text-xs uppercase hover:bg-rust-warn hover:text-white cursor-pointer transition-none"
            >
              DELETE KB
            </button>
          )}
          <button
            id="open-create-kb-modal-btn"
            onClick={onOpenCreateModal}
            className="bg-cobalt-signal text-white border-med border-ink-dark px-4 py-2 font-display font-extrabold text-xs uppercase shadow-sm hover:bg-yellow-signal hover:text-ink-dark cursor-pointer transition-none"
          >
            + CREATE KNOWLEDGE BASE
          </button>
        </div>
      </div>

      {currentKb && currentKb.description && (
        <div className="font-body text-xs text-ink-muted bg-paper p-2.5 border border-ink-dark">
          <span className="font-mono font-bold uppercase text-ink-dark">DESC: </span>
          {currentKb.description}
        </div>
      )}
    </div>
  );
}
