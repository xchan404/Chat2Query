"use client";

/**
 * UploadDropzone — drag-and-drop / click-to-browse upload for a selected knowledge base.
 * Wired to POST /api/files/upload (filesApi.upload). Each dropped/selected file is uploaded
 * independently; in-flight and failed-at-the-network-level uploads are tracked locally here
 * (distinct from a persisted file's processing_status="failed", which FileCard handles).
 */

import React, { useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { filesApi } from "@/lib/api/files";

const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv", ".txt"];

interface InFlightUpload {
  key: string;
  fileName: string;
  status: "uploading" | "error";
  error?: string;
}

interface UploadDropzoneProps {
  knowledgeBaseId: string | null;
}

export function UploadDropzone({ knowledgeBaseId }: UploadDropzoneProps) {
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploads, setUploads] = useState<InFlightUpload[]>([]);

  const disabled = !knowledgeBaseId;

  const uploadFile = async (file: File) => {
    const key = `${file.name}-${Date.now()}-${Math.random()}`;
    setUploads((prev) => [...prev, { key, fileName: file.name, status: "uploading" }]);

    try {
      await filesApi.upload(knowledgeBaseId as string, file);
      setUploads((prev) => prev.filter((u) => u.key !== key));
      void queryClient.invalidateQueries({ queryKey: ["files", knowledgeBaseId] });
    } catch (err) {
      setUploads((prev) =>
        prev.map((u) =>
          u.key === key
            ? { ...u, status: "error", error: err instanceof Error ? err.message : "Upload failed" }
            : u
        )
      );
    }
  };

  const handleFiles = (fileList: FileList | null) => {
    if (!fileList || disabled) return;
    Array.from(fileList).forEach((file) => void uploadFile(file));
  };

  const dismissUpload = (key: string) => {
    setUploads((prev) => prev.filter((u) => u.key !== key));
  };

  return (
    <div className="flex flex-col gap-3">
      <div
        id="upload-dropzone"
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragOver(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => !disabled && inputRef.current?.click()}
        role="button"
        tabIndex={disabled ? -1 : 0}
        onKeyDown={(e) => {
          if (!disabled && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        aria-disabled={disabled}
        className={`border-thick border-dashed p-8 text-center transition-none ${
          disabled
            ? "border-ink-muted bg-surface-alt opacity-50 cursor-not-allowed"
            : isDragOver
              ? "border-cobalt-signal bg-cobalt-bg cursor-pointer"
              : "border-ink-dark bg-surface hover:bg-cobalt-bg cursor-pointer"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED_EXTENSIONS.join(",")}
          disabled={disabled}
          onChange={(e) => {
            handleFiles(e.target.files);
            e.target.value = "";
          }}
          className="hidden"
        />
        <p className="font-display font-extrabold text-sm uppercase text-ink-dark">
          {disabled ? "SELECT A KNOWLEDGE BASE FIRST" : "DROP FILES OR CLICK TO UPLOAD"}
        </p>
        <p className="font-mono text-[10px] text-ink-muted mt-1 uppercase tracking-widest">
          PDF · DOCX · XLSX · CSV · TXT
        </p>
      </div>

      {uploads.length > 0 && (
        <div className="flex flex-col gap-2">
          {uploads.map((u) => (
            <div
              key={u.key}
              className={`flex items-center justify-between p-2.5 border-med font-mono text-[11px] font-bold ${
                u.status === "error"
                  ? "border-rust-warn bg-rust-bg text-rust-warn"
                  : "border-cobalt-signal bg-cobalt-bg text-cobalt-signal"
              }`}
            >
              <span className="truncate flex-1">
                {u.status === "uploading" ? "// UPLOADING..." : "// FAILED —"} {u.fileName}
                {u.error ? ` (${u.error})` : ""}
              </span>
              {u.status === "error" && (
                <button
                  onClick={() => dismissUpload(u.key)}
                  className="ml-2 shrink-0 hover:underline cursor-pointer"
                >
                  DISMISS
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
