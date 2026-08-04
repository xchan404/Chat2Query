"use client";

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
    <div className="flex flex-col border-t border-gray-300 bg-white">
      {/* Inline Scope Selector Bar */}
      <div className="flex items-center justify-between px-4 py-1.5 bg-gray-50 border-b border-gray-200 text-xs">
        <div className="flex items-center gap-4">
          {/* DB Scope */}
          <div className="flex items-center gap-1.5 font-medium text-gray-700">
            <span className="text-gray-500 font-normal">Database:</span>
            <select
              id="select-db-connection"
              value={selectedConnectionId ?? ""}
              onChange={(e) => setSelectedConnectionId(e.target.value || null)}
              className="bg-white border border-gray-300 rounded px-2 py-0.5 text-xs text-gray-800 font-medium focus:outline-none focus:border-blue-500"
            >
              <option value="">All Databases (Default)</option>
              {connections?.map((conn) => (
                <option key={conn.id} value={conn.id}>
                  {conn.name} ({conn.database_type})
                </option>
              ))}
            </select>
          </div>

          {/* KB Scope */}
          <div className="flex items-center gap-1.5 font-medium text-gray-700">
            <span className="text-gray-500 font-normal">Knowledge Base:</span>
            <select
              id="select-knowledge-base"
              value={selectedKbId ?? ""}
              onChange={(e) => setSelectedKbId(e.target.value || null)}
              className="bg-white border border-gray-300 rounded px-2 py-0.5 text-xs text-gray-800 font-medium focus:outline-none focus:border-blue-500"
            >
              <option value="">All Knowledge Bases (Default)</option>
              {knowledgeBases?.map((kb) => (
                <option key={kb.id} value={kb.id}>
                  {kb.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="text-[11px] font-mono text-gray-400">
          SSE REALTIME
        </div>
      </div>

      {/* Input Field & Action Button */}
      <div className="p-3 px-4 flex gap-3">
        <input
          id="chat-input"
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          className="flex-1 bg-white border border-gray-300 rounded-md px-3 py-2 text-xs font-normal text-gray-900 placeholder-gray-400 focus:outline-none focus:border-blue-500 disabled:bg-gray-50"
          placeholder="Enter natural language query or analysis request..."
        />
        <button
          id="chat-send-btn"
          onClick={onSend}
          disabled={disabled || !question.trim()}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs px-4 py-2 rounded-md transition-colors disabled:opacity-50 cursor-pointer shrink-0"
        >
          {disabled ? "Processing..." : "Submit Query"}
        </button>
      </div>
    </div>
  );
}
