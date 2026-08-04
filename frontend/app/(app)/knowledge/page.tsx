"use client";

/**
 * Knowledge Bases page — F5.
 * Renders real knowledge base / file data via TanStack Query.
 * No hardcoded file rows, no mockup copy-paste.
 */

import React, { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { knowledgeBasesApi } from "@/lib/api/knowledgeBases";
import { filesApi, type FileOut } from "@/lib/api/files";
import { KnowledgeBaseHeader } from "@/components/knowledge/KnowledgeBaseHeader";
import { KnowledgeBaseForm } from "@/components/knowledge/KnowledgeBaseForm";
import { UploadDropzone } from "@/components/knowledge/UploadDropzone";
import { FileCard } from "@/components/knowledge/FileCard";

export default function KnowledgePage() {
  const queryClient = useQueryClient();
  const [selectedKbId, setSelectedKbId] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);

  const {
    data: knowledgeBases,
    isLoading: kbLoading,
    isError: kbError,
    error: kbErrorObj,
  } = useQuery({
    queryKey: ["knowledgeBases"],
    queryFn: knowledgeBasesApi.list,
  });

  // Default to the first knowledge base once loaded, if nothing selected yet.
  useEffect(() => {
    if (!selectedKbId && knowledgeBases && knowledgeBases.length > 0) {
      setSelectedKbId(knowledgeBases[0].id);
    }
  }, [knowledgeBases, selectedKbId]);

  const {
    data: files,
    isLoading: filesLoading,
    isError: filesError,
    error: filesErrorObj,
  } = useQuery({
    queryKey: ["files", selectedKbId],
    queryFn: () => filesApi.list(selectedKbId as string),
    enabled: !!selectedKbId,
    // Poll only while at least one file is still pending/processing; stop once terminal.
    refetchInterval: (query) => {
      const data = query.state.data as FileOut[] | undefined;
      if (!data) return false;
      const nonTerminal = data.some(
        (f) => f.processing_status === "pending" || f.processing_status === "processing"
      );
      return nonTerminal ? 2000 : false;
    },
  });

  const deleteKbMutation = useMutation({
    mutationFn: (id: string) => knowledgeBasesApi.delete(id),
    onSuccess: (_data, deletedId) => {
      void queryClient.invalidateQueries({ queryKey: ["knowledgeBases"] });
      if (selectedKbId === deletedId) setSelectedKbId(null);
    },
  });

  const handleDeleteKb = (id: string) => {
    const kb = knowledgeBases?.find((k) => k.id === id);
    if (window.confirm(`Delete knowledge base "${kb?.name ?? id}" and all its files? This cannot be undone.`)) {
      deleteKbMutation.mutate(id);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
      <div className="border-b-thick border-ink-dark pb-3">
        <h1 className="font-display text-2xl font-extrabold uppercase tracking-tight">
          Knowledge Bases &amp; Vector Stores
        </h1>
        <p className="font-mono text-[10px] text-ink-muted mt-1 uppercase tracking-widest">
          // Document ingestion — parse → chunk → embed → store
        </p>
      </div>

      {kbLoading && (
        <div className="bg-surface border-thick border-ink-dark h-20 animate-pulse opacity-40" />
      )}

      {kbError && (
        <div className="bg-rust-bg border-thick border-rust-warn p-5 max-w-lg">
          <p className="font-mono text-[11px] font-extrabold text-rust-warn uppercase tracking-widest">
            LOAD FAILED
          </p>
          <p className="font-mono text-xs text-rust-warn mt-2">{kbErrorObj?.message}</p>
        </div>
      )}

      {knowledgeBases && (
        <KnowledgeBaseHeader
          knowledgeBases={knowledgeBases}
          selectedKbId={selectedKbId}
          setSelectedKbId={setSelectedKbId}
          onOpenCreateModal={() => setFormOpen(true)}
          onDeleteKb={handleDeleteKb}
        />
      )}

      {knowledgeBases && knowledgeBases.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-5 text-center py-16">
          <div className="bg-surface border-thick border-ink-dark p-8 shadow-hard max-w-sm">
            <p className="font-mono text-xs font-extrabold uppercase tracking-widest text-ink-muted">
              // No knowledge bases created
            </p>
            <p className="font-body text-sm text-ink-muted mt-3">
              Create a knowledge base to upload and index documents for retrieval.
            </p>
            <button
              onClick={() => setFormOpen(true)}
              className="mt-5 bg-yellow-signal text-ink-dark border-thick border-ink-dark px-6 py-2.5 font-display font-extrabold text-xs uppercase shadow-hard hover:bg-ink-dark hover:text-yellow-signal transition-none cursor-pointer w-full"
            >
              + CREATE KNOWLEDGE BASE
            </button>
          </div>
        </div>
      )}

      {selectedKbId && (
        <>
          <UploadDropzone knowledgeBaseId={selectedKbId} />

          {filesLoading && (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
              {[1, 2].map((i) => (
                <div key={i} className="bg-surface border-thick border-ink-dark h-40 animate-pulse opacity-40" />
              ))}
            </div>
          )}

          {filesError && (
            <div className="bg-rust-bg border-thick border-rust-warn p-5 max-w-lg">
              <p className="font-mono text-[11px] font-extrabold text-rust-warn uppercase tracking-widest">
                LOAD FAILED
              </p>
              <p className="font-mono text-xs text-rust-warn mt-2">{filesErrorObj?.message}</p>
            </div>
          )}

          {files && files.length === 0 && (
            <div className="flex flex-col items-center justify-center gap-3 text-center py-12">
              <p className="font-mono text-xs font-extrabold uppercase tracking-widest text-ink-muted">
                // No files uploaded to this knowledge base yet
              </p>
            </div>
          )}

          {files && files.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
              {files.map((file) => (
                <FileCard key={file.id} file={file} knowledgeBaseId={selectedKbId} />
              ))}
            </div>
          )}
        </>
      )}

      {formOpen && (
        <KnowledgeBaseForm
          onClose={() => setFormOpen(false)}
          onCreated={(kb) => setSelectedKbId(kb.id)}
        />
      )}
    </div>
  );
}
