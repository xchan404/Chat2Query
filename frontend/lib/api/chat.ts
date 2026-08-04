/**
 * Chat API client and types — strictly matching openapi.json.
 */

import { apiFetch } from "./apiClient";

export interface ChatRequest {
  question: string;
  connection_id?: string | null;
  knowledge_base_id?: string | null;
  conversation_id?: string | null;
}

export interface SQLResultOut {
  generated_sql?: string | null;
  normalized_sql?: string | null;
  row_count?: number;
  rows?: Record<string, unknown>[];
}

export interface CitationOut {
  source_type: string;
  query_execution_id?: string | null;
  table_name?: string | null;
  chunk_id?: string | null;
  file_name?: string | null;
  page_number?: number | null;
  snippet?: string | null;
}

export interface ChatResponse {
  message_id: string;
  conversation_id: string;
  intent: string;
  answer: string;
  sources_used: string[];
  sql?: SQLResultOut | null;
  citations: CitationOut[];
}

export const chatApi = {
  sync: (req: ChatRequest): Promise<ChatResponse> =>
    apiFetch("/api/chat", {
      method: "POST",
      body: JSON.stringify(req),
    }),
};
