/**
 * Files API client matching openapi.json.
 */

import { apiFetch } from "./apiClient";
import { tokenStorage } from "@/lib/auth/tokenStorage";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface FileOut {
  id: string;
  tenant_id: string;
  knowledge_base_id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  // Real backend values (DB CHECK constraint on `files.processing_status`):
  // pending | processing | completed | failed
  processing_status: "pending" | "processing" | "completed" | "failed" | string;
  processing_error?: string | null;
  chunk_count?: number | null;
  file_metadata?: Record<string, unknown> | null;
  created_at?: string | null;
}

export const filesApi = {
  upload: async (knowledgeBaseId: string, file: File): Promise<FileOut> => {
    const token = tokenStorage.getAccessToken();
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(
      `${API_BASE}/api/files/upload?knowledge_base_id=${encodeURIComponent(knowledgeBaseId)}`,
      {
        method: "POST",
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: formData,
      }
    );

    if (!response.ok) {
      let errorDetail = `Upload failed (${response.status})`;
      try {
        const errJson = await response.json();
        errorDetail = errJson.detail || errorDetail;
      } catch {
        /* ignore JSON parse error */
      }
      throw new Error(errorDetail);
    }

    return response.json();
  },

  list: (knowledgeBaseId: string): Promise<FileOut[]> =>
    apiFetch(`/api/files?knowledge_base_id=${encodeURIComponent(knowledgeBaseId)}`),

  get: (fileId: string): Promise<FileOut> =>
    apiFetch(`/api/files/${encodeURIComponent(fileId)}`),

  delete: (fileId: string): Promise<void> =>
    apiFetch(`/api/files/${encodeURIComponent(fileId)}`, {
      method: "DELETE",
    }),

  reprocess: (fileId: string): Promise<FileOut> =>
    apiFetch(`/api/files/${encodeURIComponent(fileId)}/reprocess`, {
      method: "POST",
    }),
};
