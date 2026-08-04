import React from "react";
import { SchemaOut, TableOut } from "@/lib/api/connections";
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
    <div className="bg-white border border-gray-300 rounded-md overflow-hidden shadow-sm">
      <table className="w-full text-left text-xs border-collapse">
        <thead className="bg-gray-50 border-b border-gray-300 font-semibold text-[11px] uppercase tracking-wider text-gray-600">
          <tr>
            <th className="p-3 border-r border-gray-200 w-1/4">SCHEMA &amp; TABLE</th>
            <th className="p-3 border-r border-gray-200 w-1/6">ACCESS TYPE</th>
            <th className="p-3 border-r border-gray-200 w-1/4">ROW FILTER (WHERE)</th>
            <th className="p-3 w-1/3">COLUMN CONTROLS (ALLOW / MASK)</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 text-gray-900">
          {schemas.flatMap((schema) =>
            schema.tables.map((table) => {
              const perm = getTablePerm(schema.schema_name, table.table_name);
              const isAllowed = perm ? perm.access_type !== "none" : true;

              return (
                <tr key={`${schema.id}-${table.id}`} className="hover:bg-gray-50/80 transition-colors">
                  <td className="p-3 font-mono text-xs font-semibold border-r border-gray-200 align-top text-gray-900">
                    {schema.schema_name}.{table.table_name}
                  </td>
                  <td className="p-3 border-r border-gray-200 align-top">
                    <select
                      value={perm?.access_type || "read"}
                      onChange={(e) => handleTableAccessChange(schema, table, e.target.value as any)}
                      className="border border-gray-300 rounded px-2 py-1 font-mono text-xs bg-white text-gray-800 w-full focus:outline-none focus:border-blue-500"
                    >
                      <option value="read">READ</option>
                      <option value="write">WRITE</option>
                      <option value="none">NONE (BLOCKED)</option>
                    </select>
                  </td>
                  <td className="p-3 border-r border-gray-200 align-top">
                    <input
                      type="text"
                      placeholder="e.g. tenant_id = 'xxx'"
                      value={perm?.row_filter || ""}
                      onChange={(e) => handleRowFilterChange(schema, table, e.target.value)}
                      onBlur={(e) => handleRowFilterChange(schema, table, e.target.value)}
                      disabled={!isAllowed}
                      className="border border-gray-300 rounded px-2 py-1 font-mono text-xs bg-white text-gray-800 w-full disabled:bg-gray-50 disabled:text-gray-400 focus:outline-none focus:border-blue-500"
                    />
                  </td>
                  <td className="p-3 align-top">
                    <div className="flex flex-col gap-1.5 max-h-48 overflow-y-auto pr-1">
                      {table.columns?.map((col) => {
                        const colPerm = perm?.column_permissions?.find((c) => c.column_name === col.column_name);
                        const colAllowed = colPerm ? colPerm.is_allowed : true;
                        const colMasked = colPerm ? colPerm.is_masked : false;

                        return (
                          <div key={col.id} className="flex items-center justify-between bg-gray-50 px-2.5 py-1.5 border border-gray-200 rounded text-xs">
                            <span className="font-mono text-xs text-gray-800 font-medium">{col.column_name}</span>
                            <div className="flex items-center gap-3">
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
