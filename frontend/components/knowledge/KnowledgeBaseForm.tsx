"use client";

/**
 * KnowledgeBaseForm — create a new knowledge base.
 * react-hook-form + zod, matching KnowledgeBaseCreate from openapi.json.
 */

import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { knowledgeBasesApi, type KnowledgeBaseOut } from "@/lib/api/knowledgeBases";

const kbSchema = z.object({
  name: z.string().min(1, "Name is required").max(255),
  description: z.string().max(1000).optional(),
});

type KbFormValues = z.infer<typeof kbSchema>;

interface KnowledgeBaseFormProps {
  onClose: () => void;
  onCreated: (kb: KnowledgeBaseOut) => void;
}

export function KnowledgeBaseForm({ onClose, onCreated }: KnowledgeBaseFormProps) {
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<KbFormValues>({
    resolver: zodResolver(kbSchema),
  });

  const mutation = useMutation({
    mutationFn: (data: KbFormValues) =>
      knowledgeBasesApi.create({
        name: data.name,
        description: data.description || null,
      }),
    onSuccess: (kb) => {
      void queryClient.invalidateQueries({ queryKey: ["knowledgeBases"] });
      onCreated(kb);
      onClose();
    },
  });

  const fieldClass = (hasError: boolean) =>
    `bg-white border-thick border-ink-dark p-2.5 font-body text-sm font-semibold outline-none w-full shadow-sm focus:border-cobalt-signal ${
      hasError ? "border-rust-warn bg-rust-bg" : ""
    }`;

  const labelClass = "font-mono text-[11px] font-extrabold uppercase text-ink-dark tracking-widest";
  const errorClass = "font-mono text-[10px] font-bold text-rust-warn mt-0.5";

  return (
    <div
      className="fixed inset-0 bg-ink-dark/60 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="kb-form-title"
    >
      <div className="bg-surface border-thick border-ink-dark shadow-hard w-full max-w-lg flex flex-col max-h-[90vh]">
        <div className="bg-ink-dark text-white p-3 px-5 flex items-center justify-between">
          <h2 id="kb-form-title" className="font-display font-extrabold text-sm uppercase tracking-wider">
            NEW KNOWLEDGE BASE
          </h2>
          <button
            onClick={onClose}
            className="font-mono text-xs text-white/60 hover:text-white transition-none cursor-pointer"
            aria-label="Close"
          >
            [ESC]
          </button>
        </div>

        <form
          onSubmit={handleSubmit((data) => mutation.mutate(data))}
          noValidate
          className="overflow-y-auto p-5 flex flex-col gap-4"
        >
          <div>
            <label htmlFor="kb-name" className={labelClass}>Name</label>
            <input
              id="kb-name"
              {...register("name")}
              className={fieldClass(!!errors.name)}
              placeholder="Q3 Financial Reports"
            />
            {errors.name && <p className={errorClass}>{errors.name.message}</p>}
          </div>

          <div>
            <label htmlFor="kb-description" className={labelClass}>Description (optional)</label>
            <textarea
              id="kb-description"
              {...register("description")}
              rows={3}
              className={fieldClass(!!errors.description)}
              placeholder="Financial filings and agreements"
            />
            {errors.description && <p className={errorClass}>{errors.description.message}</p>}
          </div>

          {mutation.isError && (
            <div className="p-3 bg-rust-bg border-thick border-rust-warn font-mono text-[11px] font-bold text-rust-warn">
              <span className="font-extrabold">CREATE FAILED</span> — {mutation.error?.message}
            </div>
          )}

          <div className="flex gap-3 pt-2 border-t-med border-ink-dark mt-2">
            <button
              type="submit"
              id="kb-form-submit"
              disabled={isSubmitting || mutation.isPending}
              className="flex-1 bg-yellow-signal text-ink-dark border-thick border-ink-dark py-2.5 font-display font-extrabold text-sm uppercase shadow-hard hover:bg-ink-dark hover:text-yellow-signal disabled:opacity-50 cursor-pointer transition-none"
            >
              {mutation.isPending ? "// CREATING..." : "CREATE KNOWLEDGE BASE"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-5 bg-surface text-ink-dark border-thick border-ink-dark py-2.5 font-display font-extrabold text-sm uppercase hover:bg-ink-dark hover:text-white cursor-pointer transition-none"
            >
              CANCEL
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
