"use client";

/**
 * FileCard — single file row reflecting real processing_status.
 * Polling for non-terminal files is driven by the parent's list query
 * (refetchInterval), not owned per-card — this component is presentational
 * plus its own delete/reprocess mutations.
 */

import React from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { filesApi, type FileOut } from "@/lib/api/files";
import { StatusPill, type StatusVariant } from "@/components/shared/StatusPill";

const STATUS_DISPLAY: Record<string, { variant: StatusVariant; label: string; pulse?: boolean }> = {
  pending: { variant: "pending", label: "PENDING", pulse: true },
  processing: { variant: "info", label: "PROCESSING", pulse: true },
  completed: { variant: "ok", label: "COMPLETED" },
  failed: { variant: "error", label: "FAILED" },
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface FileCardProps {
  file: FileOut;
  knowledgeBaseId: string;
}

export function FileCard({ file, knowledgeBaseId }: FileCardProps) {
  const queryClient = useQueryClient();

  const reprocessMutation = useMutation({
    mutationFn: () => filesApi.reprocess(file.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["files", knowledgeBaseId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => filesApi.delete(file.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["files", knowledgeBaseId] });
    },
  });

  const status = STATUS_DISPLAY[file.processing_status] ?? {
    variant: "warn" as StatusVariant,
    label: file.processing_status.toUpperCase(),
  };

  return (
    <div
      id={`file-card-${file.id}`}
      className="bg-surface border-thick border-ink-dark shadow-hard flex flex-col"
    >
      <div className="p-3 px-4 flex items-center justify-between gap-3 border-b-med border-ink-dark">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="bg-ink-dark text-white px-1.5 py-0.5 font-mono text-[10px] font-extrabold border border-ink-dark shrink-0">
            {file.file_type.toUpperCase()}
          </span>
          <span
            className="font-display font-extrabold text-sm uppercase tracking-wider truncate"
            title={file.file_name}
          >
            {file.file_name}
          </span>
        </div>
        <StatusPill variant={status.variant} label={status.label} pulse={status.pulse} />
      </div>

      <div className="p-4 flex flex-col gap-2 font-mono text-xs text-ink-muted border-b-med border-ink-dark">
        <div className="flex gap-2">
          <span className="text-ink-dark font-extrabold w-24 shrink-0">SIZE</span>
          <span>{formatBytes(file.file_size)}</span>
        </div>
        <div className="flex gap-2">
          <span className="text-ink-dark font-extrabold w-24 shrink-0">CHUNKS</span>
          <span>{file.chunk_count ?? 0}</span>
        </div>
        {file.created_at && (
          <div className="flex gap-2">
            <span className="text-ink-dark font-extrabold w-24 shrink-0">UPLOADED</span>
            <span>{new Date(file.created_at).toLocaleString()}</span>
          </div>
        )}
      </div>

      {file.processing_status === "failed" && file.processing_error && (
        <div className="mx-4 mt-3 p-2.5 border-med border-rust-warn bg-rust-bg font-mono text-[11px] font-bold text-rust-warn">
          <span className="font-extrabold">ERROR</span> — {file.processing_error}
        </div>
      )}

      {(reprocessMutation.isError || deleteMutation.isError) && (
        <div className="mx-4 mt-2 p-2.5 border-med border-rust-warn bg-rust-bg font-mono text-[11px] font-bold text-rust-warn">
          {(reprocessMutation.error ?? deleteMutation.error)?.message}
        </div>
      )}

      <div className="p-3 flex flex-wrap gap-2 bg-surface-alt border-t-med border-ink-dark mt-auto">
        <button
          id={`btn-reprocess-${file.id}`}
          onClick={() => reprocessMutation.mutate()}
          disabled={reprocessMutation.isPending || file.processing_status === "processing"}
          className="flex-1 min-w-0 bg-cobalt-bg text-cobalt-signal border-med border-cobalt-signal px-3 py-1.5 font-mono text-[11px] font-extrabold uppercase hover:bg-cobalt-signal hover:text-white disabled:opacity-50 transition-none cursor-pointer"
        >
          {reprocessMutation.isPending ? "// REPROCESSING..." : "REPROCESS"}
        </button>
        <button
          id={`btn-delete-file-${file.id}`}
          onClick={() => {
            if (window.confirm(`Delete "${file.file_name}"? This cannot be undone.`)) {
              deleteMutation.mutate();
            }
          }}
          disabled={deleteMutation.isPending}
          className="px-3 py-1.5 bg-rust-bg text-rust-warn border-med border-rust-warn font-mono text-[11px] font-extrabold uppercase hover:bg-rust-warn hover:text-white disabled:opacity-50 transition-none cursor-pointer"
        >
          {deleteMutation.isPending ? "..." : "DELETE"}
        </button>
      </div>
    </div>
  );
}
