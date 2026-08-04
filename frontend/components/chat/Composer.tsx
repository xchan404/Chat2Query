"use client";

/**
 * Composer — query input bar with DB connection selector and KB scope selector.
 * Fetches real database connections and knowledge bases via TanStack Query.
 */

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { connectionsApi } from "@/lib/api/connections";
import { knowledgeBasesApi } from "@/lib/api/knowledgeBases";

interface ComposerProps {
  question: string;
  setQuestion: (val: string) => void;
  selectedConnectionId: string | null;
  setSelectedConnectionId: (val: string | null) => void;
  selectedKbId: string | null;
  setSelectedKbId: (val: string | null) => void;
  onSend: () => void;
  disabled?: boolean;
}

export function Composer({
  question,
  setQuestion,
  selectedConnectionId,
  setSelectedConnectionId,
  selectedKbId,
  setSelectedKbId,
  onSend,
  disabled,
}: ComposerProps) {
  // Query real connections
  const { data: connections } = useQuery({
    queryKey: ["connections"],
    queryFn: connectionsApi.list,
  });

  // Query real knowledge bases
  const { data: knowledgeBases } = useQuery({
    queryKey: ["knowledgeBases"],
    queryFn: knowledgeBasesApi.list,
  });

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="flex flex-col border-t-thick border-ink-dark bg-surface">
      {/* Scope Selectors Top Bar */}
      <div className="flex items-center justify-between p-2 px-4 bg-surface border-b-med border-ink-dark gap-3 flex-wrap">
        <div className="flex items-center gap-2.5 flex-wrap">
          {/* DB Connection Selector */}
          <div className="flex items-center gap-1.5 bg-cobalt-bg border-med border-cobalt-signal px-2.5 py-1 font-mono text-xs font-bold text-cobalt-signal shadow-sm">
            <span>DB:</span>
            <select
              id="select-db-connection"
              value={selectedConnectionId ?? ""}
              onChange={(e) => setSelectedConnectionId(e.target.value || null)}
              className="bg-transparent border-none font-bold outline-none cursor-pointer text-cobalt-signal max-w-[200px]"
            >
              <option value="" className="bg-white text-ink-dark">
                All / Auto (Default)
              </option>
              {connections?.map((conn) => (
                <option key={conn.id} value={conn.id} className="bg-white text-ink-dark">
                  {conn.name} ({conn.database_type})
                </option>
              ))}
            </select>
          </div>

          {/* Knowledge Base Selector */}
          <div className="flex items-center gap-1.5 bg-cyan-bg border-med border-cyan-signal px-2.5 py-1 font-mono text-xs font-bold text-cyan-signal shadow-sm">
            <span>KB:</span>
            <select
              id="select-knowledge-base"
              value={selectedKbId ?? ""}
              onChange={(e) => setSelectedKbId(e.target.value || null)}
              className="bg-transparent border-none font-bold outline-none cursor-pointer text-cyan-signal max-w-[200px]"
            >
              <option value="" className="bg-white text-ink-dark">
                All / Auto (Default)
              </option>
              {knowledgeBases?.map((kb) => (
                <option key={kb.id} value={kb.id} className="bg-white text-ink-dark">
                  {kb.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="font-mono text-[10px] text-ink-muted uppercase">
          MODE: SSE REALTIME
        </div>
      </div>

      {/* Input Bar */}
      <div className="p-3.5 px-5 flex gap-3">
        <input
          id="chat-input"
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          className="flex-1 bg-white border-thick border-ink-dark p-3 font-body text-sm font-semibold shadow-sm outline-none focus:border-cobalt-signal disabled:opacity-50"
          placeholder="Ask database query or search document knowledge base..."
        />
        <button
          id="chat-send-btn"
          onClick={onSend}
          disabled={disabled || !question.trim()}
          className="bg-yellow-signal text-ink-dark border-thick border-ink-dark px-6 font-display font-extrabold text-sm uppercase shadow-hard hover:bg-ink-dark hover:text-yellow-signal disabled:opacity-50 transition-none cursor-pointer shrink-0"
        >
          {disabled ? "// SENDING..." : "SEND [ENTER]"}
        </button>
      </div>
    </div>
  );
}
