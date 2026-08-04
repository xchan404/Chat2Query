import React from "react";

interface PermissionToggleProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

export function PermissionToggle({ label, checked, onChange, disabled = false }: PermissionToggleProps) {
  return (
    <label className="flex items-center gap-2 cursor-pointer group">
      <span className="font-mono text-xs font-semibold text-ink uppercase">
        {label}
      </span>
      <div className={`relative w-8 h-4 border-thick border-ink-dark transition-colors ${checked ? "bg-emerald-pass" : "bg-surface"} ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}>
        <div className={`absolute top-0 w-3 h-3 bg-ink-dark transition-transform ${checked ? "translate-x-4" : "translate-x-0"}`} />
      </div>
      {/* Hide the actual checkbox */}
      <input
        type="checkbox"
        className="sr-only"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        disabled={disabled}
      />
    </label>
  );
}
