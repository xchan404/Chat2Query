import React from "react";

interface RoleSelectProps {
  selectedRole: string;
  onRoleChange: (roleId: string) => void;
  availableRoles: { id: string; name: string }[];
}

export function RoleSelect({ selectedRole, onRoleChange, availableRoles }: RoleSelectProps) {
  // Brutalist styling for role select
  return (
    <div className="flex items-center gap-2">
      <label className="font-display text-xs font-extrabold uppercase tracking-tight text-ink">
        TARGET ROLE:
      </label>
      <select
        value={selectedRole}
        onChange={(e) => onRoleChange(e.target.value)}
        className="border-thick border-ink-dark bg-white px-3 py-1 font-mono text-sm font-semibold shadow-sm focus:outline-none focus:ring-0"
      >
        <option value="" disabled>Select role...</option>
        {availableRoles.map((role) => (
          <option key={role.id} value={role.id}>
            {role.name}
          </option>
        ))}
      </select>
    </div>
  );
}
