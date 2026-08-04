import React from "react";
import { SchemaOut, TableOut, ColumnOut } from "@/lib/api/connections";
import { TablePermissionOut, TablePermissionCreate, ColumnPermissionCreate } from "@/lib/api/permissions";
import { PermissionToggle } from "./PermissionToggle";

interface PermissionMatrixProps {
  connectionId: string;
  roleId: string;
  schemas: SchemaOut[];
  permissions: TablePermissionOut[];
  onUpdatePermission: (data: TablePermissionCreate) => void;
  onDeletePermission: (permissionId: string) => void;
}

export function PermissionMatrix({
  connectionId,
  roleId,
  schemas,
  permissions,
  onUpdatePermission,
  onDeletePermission,
}: PermissionMatrixProps) {
  // Find current permission for a table
  const getTablePerm = (schemaName: string, tableName: string) => {
    return permissions.find(
      (p) => p.schema_name === schemaName && p.table_name === tableName && p.role_id === roleId
    );
  };

  const handleTableAccessChange = (
    schema: SchemaOut,
    table: TableOut,
    newAccess: "read" | "write" | "none"
  ) => {
    const existing = getTablePerm(schema.schema_name, table.table_name);
    if (newAccess === "none" && existing) {
      onDeletePermission(existing.id);
      return;
    }
    
    // Create or update
    onUpdatePermission({
      role_id: roleId,
      connection_id: connectionId,
      schema_name: schema.schema_name,
      table_name: table.table_name,
      access_type: newAccess,
      row_filter: existing?.row_filter || null,
      column_permissions: existing?.column_permissions.map(cp => ({
        column_name: cp.column_name,
        is_allowed: cp.is_allowed,
        is_masked: cp.is_masked,
      })) || [],
    });
  };

  const handleRowFilterChange = (
    schema: SchemaOut,
    table: TableOut,
    filter: string
  ) => {
    const existing = getTablePerm(schema.schema_name, table.table_name);
    onUpdatePermission({
      role_id: roleId,
      connection_id: connectionId,
      schema_name: schema.schema_name,
      table_name: table.table_name,
      access_type: existing?.access_type || "read",
      row_filter: filter || null,
      column_permissions: existing?.column_permissions.map(cp => ({
        column_name: cp.column_name,
        is_allowed: cp.is_allowed,
        is_masked: cp.is_masked,
      })) || [],
    });
  };

  const handleColumnToggle = (
    schema: SchemaOut,
    table: TableOut,
    columnName: string,
    field: "is_allowed" | "is_masked",
    value: boolean
  ) => {
    const existing = getTablePerm(schema.schema_name, table.table_name);
    const existingCols = existing?.column_permissions || [];
    
    // Find if col already has an override
    const colIdx = existingCols.findIndex(c => c.column_name === columnName);
    
    const newCols: ColumnPermissionCreate[] = existingCols.map(c => ({
      column_name: c.column_name,
      is_allowed: c.is_allowed,
      is_masked: c.is_masked,
    }));

    if (colIdx >= 0) {
      newCols[colIdx][field] = value;
    } else {
      newCols.push({
        column_name: columnName,
        is_allowed: field === "is_allowed" ? value : true,
        is_masked: field === "is_masked" ? value : false,
      });
    }

    onUpdatePermission({
      role_id: roleId,
      connection_id: connectionId,
      schema_name: schema.schema_name,
      table_name: table.table_name,
      access_type: existing?.access_type || "read",
      row_filter: existing?.row_filter || null,
      column_permissions: newCols,
    });
  };

  return (
    <div className="bg-white border-thick border-ink-dark shadow-hard overflow-x-auto">
      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr className="bg-surface font-display font-extrabold text-xs uppercase border-b-thick border-ink-dark">
            <th className="p-3 border-r-med border-ink-dark w-1/4">TABLE</th>
            <th className="p-3 border-r-med border-ink-dark w-1/6">ACCESS</th>
            <th className="p-3 border-r-med border-ink-dark w-1/4">ROW FILTER (WHERE)</th>
            <th className="p-3 w-1/3">COLUMNS (ALLOWED / MASKED)</th>
          </tr>
        </thead>
        <tbody>
          {schemas.flatMap((schema) =>
            schema.tables.map((table) => {
              const perm = getTablePerm(schema.schema_name, table.table_name);
              const isAllowed = perm ? perm.access_type !== "none" : true; // Default is read for simplicity or none? Assuming read if no explicit block for MVP

              return (
                <tr key={`${schema.id}-${table.id}`} className="border-b-med border-ink-dark hover:bg-cobalt-bg/5">
                  <td className="p-3 font-mono text-xs font-semibold border-r-med border-ink-dark align-top">
                    {schema.schema_name}.{table.table_name}
                  </td>
                  <td className="p-3 border-r-med border-ink-dark align-top">
                    <select
                      value={perm?.access_type || "read"} // UI default
                      onChange={(e) => handleTableAccessChange(schema, table, e.target.value as any)}
                      className="border-med border-ink-dark px-2 py-1 font-mono text-xs bg-white w-full"
                    >
                      <option value="read">READ</option>
                      <option value="write">WRITE</option>
                      <option value="none">NONE (BLOCKED)</option>
                    </select>
                  </td>
                  <td className="p-3 border-r-med border-ink-dark align-top">
                    <input
                      type="text"
                      placeholder="e.g. tenant_id = 'xxx'"
                      value={perm?.row_filter || ""}
                      onChange={(e) => handleRowFilterChange(schema, table, e.target.value)}
                      onBlur={(e) => handleRowFilterChange(schema, table, e.target.value)} // ensure save
                      disabled={!isAllowed}
                      className="border-med border-ink-dark px-2 py-1 font-mono text-xs bg-white w-full disabled:bg-surface disabled:opacity-50"
                    />
                  </td>
                  <td className="p-3 align-top">
                    <div className="flex flex-col gap-2 max-h-48 overflow-y-auto pr-2">
                      {table.columns?.map((col) => {
                        const colPerm = perm?.column_permissions?.find((c) => c.column_name === col.column_name);
                        const colAllowed = colPerm ? colPerm.is_allowed : true;
                        const colMasked = colPerm ? colPerm.is_masked : false;

                        return (
                          <div key={col.id} className="flex items-center justify-between bg-surface p-2 border-med border-ink-dark">
                            <span className="font-mono text-xs">{col.column_name}</span>
                            <div className="flex items-center gap-4">
                              <PermissionToggle
                                label="Allow"
                                checked={colAllowed}
                                onChange={(val) => handleColumnToggle(schema, table, col.column_name, "is_allowed", val)}
                                disabled={!isAllowed}
                              />
                              <PermissionToggle
                                label="Mask"
                                checked={colMasked}
                                onChange={(val) => handleColumnToggle(schema, table, col.column_name, "is_masked", val)}
                                disabled={!isAllowed || !colAllowed}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
