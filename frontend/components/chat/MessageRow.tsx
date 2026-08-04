"use client";

/**
 * MessageRow — renders user query or assistant answer cards.
 * Badges: USER / ASSISTANT // INTENT (CONFIDENCE / INTENT TYPE)
 */

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

  const getIntentBadgeColor = (intent?: string | null) => {
    switch (intent) {
      case "database":
        return "bg-cobalt-signal text-white";
      case "document":
        return "bg-cyan-signal text-white";
      case "hybrid":
        return "bg-purple-signal text-white";
      default:
        return "bg-purple-signal text-white";
    }
  };

  return (
    <div className="flex flex-col gap-1.5 max-w-[880px] w-full">
      {/* Header Badge */}
      <div className="flex items-center gap-2.5 font-mono text-xs font-bold">
        {isUser ? (
          <span className="bg-yellow-signal text-ink-dark px-2 py-0.5 border-med border-ink-dark uppercase font-extrabold">
            USER
          </span>
        ) : (
          <span
            className={`px-2 py-0.5 border-med border-ink-dark uppercase font-extrabold ${getIntentBadgeColor(
              message.intent
            )}`}
          >
            ASSISTANT // {(message.intent ?? "HYBRID INTENT").toUpperCase()}
          </span>
        )}
        <span className="text-ink-muted text-[11px]">{message.timestamp}</span>
        {message.isStreaming && (
          <span className="bg-yellow-signal text-ink-dark px-1.5 py-0.2 font-mono text-[10px] font-extrabold animate-pulse border border-ink-dark">
            STREAMING...
          </span>
        )}
      </div>

      {/* Message Card Body */}
      <div
        className={`bg-white border-thick border-ink-dark p-4 shadow-sm font-body text-sm leading-relaxed whitespace-pre-wrap ${
          isUser ? "border-l-8 border-l-yellow-signal" : "border-l-8 border-l-purple-signal"
        }`}
      >
        {message.content}
        {message.isStreaming && (
          <span className="inline-block w-2 h-4 bg-purple-signal ml-1 animate-pulse align-middle" />
        )}
      </div>

      {/* Sources badge footer if assistant message */}
      {!isUser && message.sources_used && message.sources_used.length > 0 && (
        <div className="flex items-center gap-2 font-mono text-[10px] text-ink-muted mt-0.5">
          <span className="font-extrabold uppercase">SOURCES:</span>
          {message.sources_used.map((src, idx) => (
            <span
              key={idx}
              className="bg-surface border border-ink-dark px-1.5 py-0.5 font-bold uppercase text-ink-dark"
            >
              {src}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
