"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { connectionsApi } from "@/lib/api/connections";
import { permissionsApi, TablePermissionCreate } from "@/lib/api/permissions";
import { apiFetch } from "@/lib/api/apiClient";
import { PermissionMatrix } from "@/components/permissions/PermissionMatrix";
import { RoleSelect } from "@/components/permissions/RoleSelect";

export default function PermissionsPage() {
  const queryClient = useQueryClient();
  const [selectedConnectionId, setSelectedConnectionId] = useState<string>("");
  const [selectedRoleId, setSelectedRoleId] = useState<string>("");

  // Fetch connections
  const { data: connections = [] } = useQuery({
    queryKey: ["connections"],
    queryFn: connectionsApi.list,
  });

  // Fetch roles
  const { data: roles = [] } = useQuery({
    queryKey: ["roles"],
    queryFn: async () => {
      return await apiFetch<{ id: string; name: string }[]>("/api/auth/roles");
    },
  });

  // Default selection
  useEffect(() => {
    if (connections.length > 0 && !selectedConnectionId) {
      setSelectedConnectionId(connections[0].id);
    }
  }, [connections, selectedConnectionId]);

  useEffect(() => {
    if (roles.length > 0 && !selectedRoleId) {
      setSelectedRoleId(roles[0].id);
    }
  }, [roles, selectedRoleId]);

  // Fetch schemas for selected connection
  const { data: schemas = [], isLoading: isLoadingSchemas } = useQuery({
    queryKey: ["connections", selectedConnectionId, "schemas"],
    queryFn: () => connectionsApi.schemas(selectedConnectionId),
    enabled: !!selectedConnectionId,
  });

  // Fetch permissions for selected connection
  const { data: permissions = [], isLoading: isLoadingPermissions } = useQuery({
    queryKey: ["permissions", selectedConnectionId],
    queryFn: () => permissionsApi.listByConnection(selectedConnectionId),
    enabled: !!selectedConnectionId,
  });

  // Mutations
  const updatePermMutation = useMutation({
    mutationFn: (data: TablePermissionCreate) => permissionsApi.createOrUpdate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["permissions", selectedConnectionId] });
    },
  });

  const deletePermMutation = useMutation({
    mutationFn: (id: string) => permissionsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["permissions", selectedConnectionId] });
    },
  });

  const isLoading = isLoadingSchemas || isLoadingPermissions;

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-hidden bg-gray-50">
      {/* Page Header */}
      <div className="flex items-center justify-between p-3.5 px-5 bg-white border-b border-gray-300">
        <div>
          <h1 className="font-semibold text-sm text-gray-900">
            Role Access &amp; Security Pipeline Matrix
          </h1>
          <p className="text-xs text-gray-500 mt-0.5 font-normal">
            Configure table read/write rules, row-level WHERE filters, and column masking policies
          </p>
        </div>
      </div>

      {/* Selectors Bar */}
      <div className="p-4 px-5 bg-white border-b border-gray-300 flex flex-wrap gap-4 items-center">
        {/* Connection Selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-gray-600">Database Connection:</label>
          <select
            value={selectedConnectionId}
            onChange={(e) => setSelectedConnectionId(e.target.value)}
            className="border border-gray-300 rounded px-2.5 py-1 text-xs font-medium text-gray-800 bg-white focus:outline-none focus:border-blue-500"
          >
            <option value="" disabled>Select connection...</option>
            {connections.map((conn) => (
              <option key={conn.id} value={conn.id}>
                {conn.name} ({conn.database_type})
              </option>
            ))}
          </select>
        </div>

        {/* Role Selector */}
        <RoleSelect 
          selectedRole={selectedRoleId} 
          onRoleChange={setSelectedRoleId} 
          availableRoles={roles} 
        />
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-5">
        {isLoading ? (
          <div className="bg-white border border-gray-300 rounded-md p-6 text-xs text-gray-500 text-center">
            Loading security matrix...
          </div>
        ) : selectedConnectionId && selectedRoleId ? (
          <PermissionMatrix
            connectionId={selectedConnectionId}
            roleId={selectedRoleId}
            schemas={schemas}
            permissions={permissions}
            onUpdatePermission={(data) => updatePermMutation.mutate(data)}
            onDeletePermission={(id) => deletePermMutation.mutate(id)}
          />
        ) : (
          <div className="bg-white border border-gray-300 rounded-md p-6 text-xs text-gray-500 text-center">
            Please select a database connection and a target role.
          </div>
        )}
      </div>
    </div>
  );
}
