/**
 * Conversations API client and types — strictly matching openapi.json.
 */

import { apiFetch } from "./apiClient";

export interface MessageOut {
  id: string;
  conversation_id: string;
  parent_message_id?: string | null;
  role: "user" | "assistant";
  content: string;
  intent?: string | null;
  sources_used?: string[];
  created_at?: string | null;
}

export interface ConversationOut {
  id: string;
  tenant_id: string;
  user_id: string;
  title?: string | null;
  summary?: string | null;
  created_at?: string | null;
}

export interface ConversationDetailOut {
  id: string;
  tenant_id: string;
  user_id: string;
  title?: string | null;
  summary?: string | null;
  messages: MessageOut[];
  created_at?: string | null;
}

export const conversationsApi = {
  list: (limit = 50, offset = 0): Promise<ConversationOut[]> =>
    apiFetch(`/api/conversations?limit=${limit}&offset=${offset}`),

  get: (id: string): Promise<ConversationDetailOut> =>
    apiFetch(`/api/conversations/${id}`),

  delete: (id: string): Promise<void> =>
    apiFetch(`/api/conversations/${id}`, { method: "DELETE" }),
};
