"use client";

import React from "react";
import { type CitationOut, type SQLResultOut } from "@/lib/api/chat";

export interface ChatMessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  intent?: string | null;
  sources_used?: string[];
  sql?: SQLResultOut | null;
  citations?: CitationOut[];
  isStreaming?: boolean;
}

interface MessageRowProps {
  message: ChatMessageItem;
}

export function MessageRow({ message }: MessageRowProps) {
  const isUser = message.role === "user";

  return (
    <div className="flex flex-col gap-1.5 w-full">
      {/* Header Info */}
      <div className="flex items-center gap-2 text-xs">
        {isUser ? (
          <span className="font-semibold text-gray-900 bg-gray-200 px-2 py-0.5 rounded text-[11px]">
            User Query
          </span>
        ) : (
          <span className="font-semibold text-blue-700 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded text-[11px]">
            Assistant Output • INTENT: {(message.intent ?? "HYBRID").toUpperCase()}
          </span>
        )}
        <span className="text-gray-400 text-[11px] font-mono">{message.timestamp}</span>
        {message.isStreaming && (
          <span className="text-blue-600 font-mono text-[10px] font-semibold">
            [Processing...]
          </span>
        )}
      </div>

      {/* Structured Card Content */}
      <div
        className={`border rounded-md p-4 text-xs font-normal leading-relaxed text-gray-900 ${
          isUser
            ? "bg-gray-100/80 border-gray-300"
            : "bg-white border-gray-300 shadow-sm"
        }`}
      >
        <div className="whitespace-pre-wrap">{message.content}</div>

        {/* Sources Footer */}
        {!isUser && message.sources_used && message.sources_used.length > 0 && (
          <div className="flex items-center gap-2 mt-3 pt-2 border-t border-gray-200 font-mono text-[10px] text-gray-500">
            <span className="font-semibold uppercase text-gray-600">SOURCES:</span>
            {message.sources_used.map((src, idx) => (
              <span
                key={idx}
                className="bg-gray-100 border border-gray-300 px-1.5 py-0.5 rounded text-gray-700 font-medium"
              >
                {src}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
