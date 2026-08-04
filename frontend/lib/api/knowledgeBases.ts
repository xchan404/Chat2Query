/**
 * Knowledge Bases API client — matching openapi.json.
 */

import { apiFetch } from "./apiClient";

export interface KnowledgeBaseOut {
  id: string;
  tenant_id: string;
  name: string;
  description?: string | null;
  is_active?: boolean;
  created_at?: string | null;
}

export interface KnowledgeBaseCreate {
  name: string;
  description?: string | null;
}

export const knowledgeBasesApi = {
  list: (): Promise<KnowledgeBaseOut[]> =>
    apiFetch("/api/knowledge-bases"),

  get: (id: string): Promise<KnowledgeBaseOut> =>
    apiFetch(`/api/knowledge-bases/${encodeURIComponent(id)}`),

  create: (data: KnowledgeBaseCreate): Promise<KnowledgeBaseOut> =>
    apiFetch("/api/knowledge-bases", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  delete: (id: string): Promise<void> =>
    apiFetch(`/api/knowledge-bases/${encodeURIComponent(id)}`, {
      method: "DELETE",
    }),
};
