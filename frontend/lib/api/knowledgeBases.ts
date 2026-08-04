/**
 * Knowledge Bases API client — matching openapi.json.
 */

import { apiFetch } from "./apiClient";

export interface KnowledgeBaseOut {
  id: string;
  tenant_id: string;
  name: string;
  description?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export const knowledgeBasesApi = {
  list: (): Promise<KnowledgeBaseOut[]> =>
    apiFetch("/api/knowledge-bases"),

  get: (id: string): Promise<KnowledgeBaseOut> =>
    apiFetch(`/api/knowledge-bases/${id}`),
};
