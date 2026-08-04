import apiClient from "./apiClient";

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
  listByConnection: async (connectionId: string): Promise<TablePermissionOut[]> => {
    const response = await apiClient.get(`/api/permissions/connections/${connectionId}`);
    return response.data;
  },

  createOrUpdate: async (data: TablePermissionCreate): Promise<TablePermissionOut> => {
    const response = await apiClient.post("/api/permissions/tables", data);
    return response.data;
  },

  delete: async (permissionId: string): Promise<void> => {
    await apiClient.delete(`/api/permissions/tables/${permissionId}`);
  },
};
