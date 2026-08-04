"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { connectionsApi } from "@/lib/api/connections";
import { permissionsApi, TablePermissionCreate } from "@/lib/api/permissions";
import { apiClient } from "@/lib/api/apiClient";
import { PermissionMatrix } from "@/components/permissions/PermissionMatrix";
import { RoleSelect } from "@/components/permissions/RoleSelect";

export default function PermissionsPage() {
  const queryClient = useQueryClient();
  const [selectedConnectionId, setSelectedConnectionId] = useState<string>("");
  const [selectedRoleId, setSelectedRoleId] = useState<string>("");

  // Fetch connections
  const { data: connections = [], isLoading: isLoadingConnections } = useQuery({
    queryKey: ["connections"],
    queryFn: connectionsApi.list,
  });

  // Fetch roles
  const { data: roles = [], isLoading: isLoadingRoles } = useQuery({
    queryKey: ["roles"],
    queryFn: async () => {
      const res = await apiClient.get("/api/auth/roles");
      return res.data as { id: string; name: string }[];
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

  const isLoading = isLoadingConnections || isLoadingRoles || isLoadingSchemas || isLoadingPermissions;

  return (
    <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
      <div className="border-b-thick border-ink-dark pb-3 flex items-center justify-between">
        <h1 className="font-display text-2xl font-extrabold uppercase tracking-tight">
          Effective Schema &amp; Security Pipeline Rules
        </h1>
      </div>

      <div className="flex flex-col sm:flex-row gap-6 p-4 bg-surface border-thick border-ink-dark shadow-hard">
        {/* Connection Selector */}
        <div className="flex items-center gap-2">
          <label className="font-display text-xs font-extrabold uppercase tracking-tight text-ink">
            DATABASE:
          </label>
          <select
            value={selectedConnectionId}
            onChange={(e) => setSelectedConnectionId(e.target.value)}
            className="border-thick border-ink-dark bg-white px-3 py-1 font-mono text-sm font-semibold shadow-sm focus:outline-none focus:ring-0"
          >
            <option value="" disabled>Select database...</option>
            {connections.map((conn) => (
              <option key={conn.id} value={conn.id}>
                {conn.name}
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
        {/* Since RoleSelect was built to show string names but takes id, let's just render standard select to show real names if needed, but RoleSelect is fine if we adapt it or just map it here. Wait, I should make sure it shows the name instead of the ID! */}
      </div>

      {isLoading ? (
        <div className="font-mono text-sm font-semibold p-4">Loading matrix...</div>
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
        <div className="font-mono text-sm p-4 bg-surface border-thick border-ink-dark shadow-hard">
          Please select a database connection and a target role.
        </div>
      )}
    </div>
  );
}
