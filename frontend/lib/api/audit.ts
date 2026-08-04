import { apiFetch } from "./apiClient";

export interface AuditLogOut {
  id: string;
  tenant_id: string;
  user_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  ip_address: string | null;
  details: Record<string, unknown> | null;
  description: string | null;
  created_at: string | null;
}

export const auditApi = {
  getAuditLogs: async (limit: number = 100, offset: number = 0): Promise<AuditLogOut[]> => {
    return apiFetch<AuditLogOut[]>(`/api/audit-logs?limit=${limit}&offset=${offset}`);
  },
};
