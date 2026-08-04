/**
 * StatusPill — reusable status indicator used across Connections, Files, and Audit.
 * Variants: ok / warn / error / pending / info
 * One component, not reimplemented per screen.
 */

import React from "react";

export type StatusVariant = "ok" | "warn" | "error" | "pending" | "info";

const VARIANT_CLASSES: Record<StatusVariant, string> = {
  ok:      "bg-emerald-bg text-emerald-pass border-emerald-pass",
  warn:    "bg-yellow-bg text-ink-dark border-ink-dark",
  error:   "bg-rust-bg text-rust-warn border-rust-warn",
  pending: "bg-surface-alt text-ink-muted border-ink-muted",
  info:    "bg-cobalt-bg text-cobalt-signal border-cobalt-signal",
};

interface StatusPillProps {
  variant: StatusVariant;
  label: string;
  pulse?: boolean;
}

export function StatusPill({ variant, label, pulse }: StatusPillProps) {
  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 font-mono text-[10px] font-extrabold uppercase border tracking-widest ${VARIANT_CLASSES[variant]} ${pulse ? "animate-pulse" : ""}`}
    >
      {label}
    </span>
  );
}
