import React from "react";

interface PermissionToggleProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

export function PermissionToggle({ label, checked, onChange, disabled = false }: PermissionToggleProps) {
  return (
    <label className="flex items-center gap-1.5 cursor-pointer text-xs font-medium text-gray-700 select-none">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        disabled={disabled}
        className="w-3.5 h-3.5 text-blue-600 rounded border-gray-300 focus:ring-blue-500 disabled:opacity-50"
      />
      <span>{label}</span>
    </label>
  );
}
