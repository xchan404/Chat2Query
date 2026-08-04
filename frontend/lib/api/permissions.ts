import { apiFetch } from "./apiClient";

export interface ColumnPermissionCreate {
  column_name: string;
  is_allowed: boolean;
  is_masked: boolean;
}

export interface ColumnPermissionOut extends ColumnPermissionCreate {
  id: string;
  table_permission_id: string;
  role_id: string;
  created_at: string | null;
}

export interface TablePermissionCreate {
  role_id: string;
  connection_id: string;
  schema_name: string;
  table_name: string;
  access_type: "read" | "write" | "none";
  row_filter: string | null;
  column_permissions: ColumnPermissionCreate[];
}

export interface TablePermissionOut {
  id: string;
  role_id: string;
  connection_id: string;
  schema_name: string;
  table_name: string;
  access_type: "read" | "write" | "none";
  row_filter: string | null;
  column_permissions: ColumnPermissionOut[];
  created_at: string | null;
}

export const permissionsApi = {
  listByConnection: (connectionId: string): Promise<TablePermissionOut[]> => {
    return apiFetch(`/api/permissions/connections/${connectionId}`);
  },

  createOrUpdate: (data: TablePermissionCreate): Promise<TablePermissionOut> => {
    return apiFetch("/api/permissions/tables", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  delete: (permissionId: string): Promise<void> => {
    return apiFetch(`/api/permissions/tables/${permissionId}`, {
      method: "DELETE",
    });
  },
};
