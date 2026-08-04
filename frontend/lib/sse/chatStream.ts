/**
 * Typed SSE Stream Client for POST /api/chat/stream
 *
 * Uses fetch with ReadableStream to pass Authorization: Bearer header.
 * Emits events:
 *   - intent: { intent: string }
 *   - sql_result: SQLResultOut
 *   - citation: CitationOut
 *   - token: { text: string }
 *   - done: { message_id, conversation_id, intent, sources_used }
 *   - error: { detail: string }
 */

import { tokenStorage } from "@/lib/auth/tokenStorage";
import { type ChatRequest, type SQLResultOut, type CitationOut } from "@/lib/api/chat";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface StreamEventCallbacks {
  onIntent?: (data: { intent: string }) => void;
  onSqlResult?: (data: SQLResultOut) => void;
  onCitation?: (data: CitationOut) => void;
  onToken?: (data: { text: string }) => void;
  onDone?: (data: { message_id: string; conversation_id: string; intent: string; sources_used: string[] }) => void;
  onError?: (data: { detail: string }) => void;
}

export async function streamChat(
  req: ChatRequest,
  callbacks: StreamEventCallbacks
): Promise<void> {
  const token = tokenStorage.getAccessToken();

  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(req),
  });

  if (!response.ok) {
    let errorDetail = `HTTP error ${response.status}`;
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      /* ignore JSON parse failure */
    }
    callbacks.onError?.({ detail: errorDetail });
    return;
  }

  if (!response.body) {
    callbacks.onError?.({ detail: "Response body is null" });
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Process complete SSE frames separated by double newline \n\n
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? ""; // keep incomplete trailing frame in buffer

    for (const frame of frames) {
      if (!frame.trim()) continue;

      let eventType = "message";
      let eventDataStr = "";

      const lines = frame.split("\n");
      for (const line of lines) {
        if (line.startsWith("event: ")) {
          eventType = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          eventDataStr = line.slice(6).trim();
        }
      }

      if (!eventDataStr) continue;

      try {
        const parsed = JSON.parse(eventDataStr);

        switch (eventType) {
          case "intent":
            callbacks.onIntent?.(parsed);
            break;
          case "sql_result":
            callbacks.onSqlResult?.(parsed);
            break;
          case "citation":
            callbacks.onCitation?.(parsed);
            break;
          case "token":
            callbacks.onToken?.(parsed);
            break;
          case "done":
            callbacks.onDone?.(parsed);
            break;
          case "error":
            callbacks.onError?.(parsed);
            break;
          default:
            console.log("Unhandled SSE event:", eventType, parsed);
        }
      } catch (err) {
        console.error("Failed to parse SSE event data:", eventDataStr, err);
      }
    }
  }
}
