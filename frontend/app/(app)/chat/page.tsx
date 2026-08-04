"use client";

/**
 * ChatPage — F4 core Chat screen.
 * Real-time SSE streaming via streamChat(), populated EvidenceRail,
 * multi-turn conversation support, zero hardcoded mockup demo text.
 */

import React, { useState, useRef, useEffect } from "react";
import { useUIStore } from "@/lib/stores/uiStore";
import { streamChat } from "@/lib/sse/chatStream";
import { type SQLResultOut, type CitationOut } from "@/lib/api/chat";
import { MessageRow, type ChatMessageItem } from "@/components/chat/MessageRow";
import { Composer } from "@/components/chat/Composer";
import { EvidenceRail } from "@/components/chat/EvidenceRail";

export default function ChatPage() {
  const { isEvidenceRailOpen, toggleEvidenceRail } = useUIStore();

  const [question, setQuestion] = useState("");
  const [selectedConnectionId, setSelectedConnectionId] = useState<string | null>(null);
  const [selectedKbId, setSelectedKbId] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  // In-flight Evidence state for EvidenceRail
  const [activeIntent, setActiveIntent] = useState<string | null>(null);
  const [activeSqlResult, setActiveSqlResult] = useState<SQLResultOut | null>(null);
  const [activeCitations, setActiveCitations] = useState<CitationOut[]>([]);
  const [activeExecutionId, setActiveExecutionId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || isStreaming) return;

    const userMessageId = `user-${Date.now()}`;
    const assistantMessageId = `asst-${Date.now()}`;
    const nowTime = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

    // Clear input
    setQuestion("");

    // Reset evidence rail for new turn
    setActiveIntent(null);
    setActiveSqlResult(null);
    setActiveCitations([]);
    setActiveExecutionId(null);

    // Append User Message and empty Assistant Message shell
    const userMsg: ChatMessageItem = {
      id: userMessageId,
      role: "user",
      content: trimmedQuestion,
      timestamp: nowTime,
    };

    const asstMsg: ChatMessageItem = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: nowTime,
      intent: "pending...",
      sources_used: [],
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, asstMsg]);
    setIsStreaming(true);

    try {
      await streamChat(
        {
          question: trimmedQuestion,
          connection_id: selectedConnectionId,
          knowledge_base_id: selectedKbId,
          conversation_id: conversationId,
        },
        {
          onIntent: (data) => {
            setActiveIntent(data.intent);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId ? { ...msg, intent: data.intent } : msg
              )
            );
          },

          onSqlResult: (sqlData) => {
            setActiveSqlResult(sqlData);
            // If execution_id returned in SQLResultOut or rows
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId ? { ...msg, sql: sqlData } : msg
              )
            );
          },

          onCitation: (citationData) => {
            if (citationData.query_execution_id) {
              setActiveExecutionId(citationData.query_execution_id);
            }
            setActiveCitations((prev) => [...prev, citationData]);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, citations: [...(msg.citations ?? []), citationData] }
                  : msg
              )
            );
          },

          onToken: (tokenData) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: msg.content + tokenData.text }
                  : msg
              )
            );
          },

          onDone: (doneData) => {
            setConversationId(doneData.conversation_id);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? {
                      ...msg,
                      id: doneData.message_id,
                      intent: doneData.intent,
                      sources_used: doneData.sources_used,
                      isStreaming: false,
                    }
                  : msg
              )
            );
            setIsStreaming(false);
          },

          onError: (errData) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? {
                      ...msg,
                      content: `[ERROR]: ${errData.detail}`,
                      isStreaming: false,
                    }
                  : msg
              )
            );
            setIsStreaming(false);
          },
        }
      );
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : "Request failed";
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, content: `[STREAM ERROR]: ${errMsg}`, isStreaming: false }
            : msg
        )
      );
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex flex-1 min-h-0 overflow-hidden">
      {/* Workspace Main Area */}
      <div className="flex-1 flex flex-col min-w-0 border-r-thick border-ink-dark">
        {/* Workspace Top Action Bar */}
        <div className="flex items-center justify-between p-2.5 px-4 bg-surface border-b-thick border-ink-dark gap-3">
          <div className="flex items-center gap-2">
            <span className="font-display font-extrabold text-xs uppercase tracking-wider text-ink-dark">
              CHAT & EVIDENCE WORKSPACE
            </span>
            {conversationId && (
              <span className="font-mono text-[10px] text-ink-muted bg-paper px-1.5 py-0.5 border border-ink-dark">
                CONV: {conversationId.slice(0, 8)}...
              </span>
            )}
          </div>

          <button
            id="toggle-evidence-rail-btn"
            onClick={toggleEvidenceRail}
            className="bg-ink-dark text-white border-med border-ink-dark px-3 py-1.5 font-display font-bold text-xs uppercase shadow-sm hover:bg-yellow-signal hover:text-ink-dark cursor-pointer transition-none"
          >
            {isEvidenceRailOpen ? "HIDE EVIDENCE RAIL" : "SHOW EVIDENCE RAIL"}
          </button>
        </div>

        {/* Message Thread Area */}
        <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-5 bg-paper">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-4 text-center py-16">
              <div className="bg-surface border-thick border-ink-dark p-6 shadow-hard max-w-md">
                <div className="font-mono text-xs font-extrabold uppercase tracking-widest text-ink-dark">
                  // Chat2Query Control Engine
                </div>
                <p className="font-body text-sm text-ink-muted mt-2">
                  Ask natural language questions to query connected SQL databases or search indexed document knowledge bases.
                </p>
                <div className="mt-4 flex flex-col gap-2 font-mono text-[11px]">
                  <span className="bg-paper p-2 border border-ink-dark text-left font-semibold text-ink-dark">
                    💡 "What database tables exist in the schema?"
                  </span>
                  <span className="bg-paper p-2 border border-ink-dark text-left font-semibold text-ink-dark">
                    💡 "List total users registered per tenant"
                  </span>
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg) => <MessageRow key={msg.id} message={msg} />)
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Composer Input Bar */}
        <Composer
          question={question}
          setQuestion={setQuestion}
          selectedConnectionId={selectedConnectionId}
          setSelectedConnectionId={setSelectedConnectionId}
          selectedKbId={selectedKbId}
          setSelectedKbId={setSelectedKbId}
          onSend={handleSend}
          disabled={isStreaming}
        />
      </div>

      {/* Evidence Rail Side Panel */}
      {isEvidenceRailOpen && (
        <EvidenceRail
          sqlResult={activeSqlResult}
          citations={activeCitations}
          intent={activeIntent}
          queryExecutionId={activeExecutionId}
        />
      )}
    </div>
  );
}
