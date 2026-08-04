"use client";

/**
 * ConnectionForm — create or edit a database connection.
 * react-hook-form + zod validation matching the ConnectionCreate/ConnectionUpdate
 * schema from openapi.json (database_type must be "postgresql" | "mysql",
 * port 1–65535, all required fields present).
 */

import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { connectionsApi, type ConnectionOut } from "@/lib/api/connections";

// ── Zod schema — mirrors ConnectionCreate from openapi.json ──────────────────

const connectionSchema = z.object({
  name: z.string().min(1, "Name is required").max(255),
  database_type: z.enum(["postgresql", "mysql"] as const, {
    error: "Database type must be postgresql or mysql",
  }),
  host: z.string().min(1, "Host is required").max(255),
  port: z
    .number({ error: "Port must be a number" })
    .int()
    .min(1)
    .max(65535),
  database_name: z.string().min(1, "Database name is required").max(255),
  username: z.string().min(1, "Username is required").max(255),
  password: z.string().min(1, "Password is required"),
  ssl_enabled: z.boolean().optional(),
});

type ConnectionFormValues = z.infer<typeof connectionSchema>;

// ── Component ─────────────────────────────────────────────────────────────────

interface ConnectionFormProps {
  existing?: ConnectionOut;
  onClose: () => void;
}

export function ConnectionForm({ existing, onClose }: ConnectionFormProps) {
  const queryClient = useQueryClient();
  const isEdit = !!existing;

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ConnectionFormValues>({
    resolver: zodResolver(connectionSchema),
    defaultValues: existing
      ? {
          name: existing.name,
          database_type: existing.database_type as "postgresql" | "mysql",
          host: existing.host,
          port: existing.port,
          database_name: existing.database_name,
          username: existing.username,
          password: "",   // password never returned from API — always blank in edit mode
          ssl_enabled: existing.ssl_enabled,
        }
      : {
          database_type: "postgresql",
          port: 5432,
          ssl_enabled: false,
        },
  });

  const mutation = useMutation({
    mutationFn: (data: ConnectionFormValues) =>
      isEdit && existing
        ? connectionsApi.update(existing.id, data)
        : connectionsApi.create(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["connections"] });
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
      aria-labelledby="connection-form-title"
    >
      <div className="bg-surface border-thick border-ink-dark shadow-hard w-full max-w-lg flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="bg-ink-dark text-white p-3 px-5 flex items-center justify-between">
          <h2
            id="connection-form-title"
            className="font-display font-extrabold text-sm uppercase tracking-wider"
          >
            {isEdit ? "EDIT CONNECTION" : "NEW CONNECTION"}
          </h2>
          <button
            onClick={onClose}
            className="font-mono text-xs text-white/60 hover:text-white transition-none cursor-pointer"
            aria-label="Close"
          >
            [ESC]
          </button>
        </div>

        {/* Form */}
        <form
          onSubmit={handleSubmit((data) => mutation.mutate(data))}
          noValidate
          className="overflow-y-auto p-5 flex flex-col gap-4"
        >
          {/* Name */}
          <div>
            <label htmlFor="conn-name" className={labelClass}>Name</label>
            <input id="conn-name" {...register("name")} className={fieldClass(!!errors.name)} placeholder="PROD-POSTGRES-PRIMARY" />
            {errors.name && <p className={errorClass}>{errors.name.message}</p>}
          </div>

          {/* DB Type */}
          <div>
            <label htmlFor="conn-type" className={labelClass}>Database Type</label>
            <select
              id="conn-type"
              {...register("database_type")}
              className={`${fieldClass(!!errors.database_type)} cursor-pointer`}
            >
              <option value="postgresql">PostgreSQL</option>
              <option value="mysql">MySQL</option>
            </select>
            {errors.database_type && <p className={errorClass}>{errors.database_type.message}</p>}
          </div>

          {/* Host + Port */}
          <div className="flex gap-3">
            <div className="flex-1">
              <label htmlFor="conn-host" className={labelClass}>Host</label>
              <input id="conn-host" {...register("host")} className={fieldClass(!!errors.host)} placeholder="localhost" />
              {errors.host && <p className={errorClass}>{errors.host.message}</p>}
            </div>
            <div className="w-24">
              <label htmlFor="conn-port" className={labelClass}>Port</label>
              <input
                id="conn-port"
                type="number"
                {...register("port", { valueAsNumber: true })}
                className={fieldClass(!!errors.port)}
                placeholder="5432"
              />
              {errors.port && <p className={errorClass}>{errors.port.message}</p>}
            </div>
          </div>

          {/* Database name */}
          <div>
            <label htmlFor="conn-db" className={labelClass}>Database Name</label>
            <input id="conn-db" {...register("database_name")} className={fieldClass(!!errors.database_name)} placeholder="platform" />
            {errors.database_name && <p className={errorClass}>{errors.database_name.message}</p>}
          </div>

          {/* Username + Password */}
          <div className="flex gap-3">
            <div className="flex-1">
              <label htmlFor="conn-user" className={labelClass}>Username</label>
              <input id="conn-user" {...register("username")} className={fieldClass(!!errors.username)} placeholder="db_user" />
              {errors.username && <p className={errorClass}>{errors.username.message}</p>}
            </div>
            <div className="flex-1">
              <label htmlFor="conn-pass" className={labelClass}>
                Password {isEdit && <span className="text-ink-muted normal-case font-normal">(leave blank to keep)</span>}
              </label>
              <input
                id="conn-pass"
                type="password"
                {...register("password")}
                className={fieldClass(!!errors.password)}
                placeholder="••••••••"
                autoComplete="new-password"
              />
              {errors.password && <p className={errorClass}>{errors.password.message}</p>}
            </div>
          </div>

          {/* SSL */}
          <div className="flex items-center gap-3">
            <input
              id="conn-ssl"
              type="checkbox"
              {...register("ssl_enabled")}
              className="w-4 h-4 border-thick border-ink-dark accent-cobalt-signal cursor-pointer"
            />
            <label htmlFor="conn-ssl" className={labelClass}>
              Enable SSL
            </label>
          </div>

          {/* Mutation error */}
          {mutation.isError && (
            <div className="p-3 bg-rust-bg border-thick border-rust-warn font-mono text-[11px] font-bold text-rust-warn">
              <span className="font-extrabold">SAVE FAILED</span> — {mutation.error?.message}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2 border-t-med border-ink-dark mt-2">
            <button
              type="submit"
              id="conn-form-submit"
              disabled={isSubmitting || mutation.isPending}
              className="flex-1 bg-yellow-signal text-ink-dark border-thick border-ink-dark py-2.5 font-display font-extrabold text-sm uppercase shadow-hard hover:bg-ink-dark hover:text-yellow-signal disabled:opacity-50 cursor-pointer transition-none"
            >
              {mutation.isPending ? "// SAVING..." : isEdit ? "SAVE CHANGES" : "CREATE CONNECTION"}
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
