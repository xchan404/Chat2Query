"use client";

/**
 * Login Page — Operator Authentication.
 * Uses react-hook-form + zod validation and renders an inline error box
 * on invalid credentials. No console error or redirect loop.
 */

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/lib/auth/AuthProvider";

const loginSchema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const { login } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setServerError(null);
    try {
      await login(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Authentication failed";
      setServerError(message);
    }
  };

  return (
    <div className="min-h-screen bg-paper flex items-center justify-center p-4">
      <div className="bg-surface border-thick border-ink-dark shadow-hard w-full max-w-md">
        {/* Header Bar */}
        <div className="bg-ink-dark text-white p-3 px-5 flex items-center justify-between border-b-thick border-ink-dark">
          <span className="font-display font-extrabold text-sm uppercase tracking-wider">
            CHAT2QUERY // CONTROL ENGINE
          </span>
          <span className="bg-yellow-signal text-ink-dark px-1.5 py-0.5 font-mono text-[10px] font-extrabold">
            v1.0-AUDIT
          </span>
        </div>

        {/* Title Section */}
        <div className="p-5 border-b-thick border-ink-dark bg-paper">
          <h1 className="font-display font-extrabold text-xl uppercase tracking-wider text-ink-dark">
            OPERATOR AUTHENTICATION
          </h1>
          <p className="font-mono text-xs text-ink-muted mt-1 uppercase tracking-widest">
            // MULTI-TENANT ACCESS CONTROL — CREDENTIALS REQUIRED
          </p>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit(onSubmit)} className="p-5 flex flex-col gap-4">
          <div>
            <label
              htmlFor="login-username"
              className="block font-mono text-xs font-extrabold uppercase tracking-widest text-ink-dark mb-1"
            >
              USERNAME
            </label>
            <input
              id="login-username"
              type="text"
              {...register("username")}
              className="w-full bg-white border-thick border-ink-dark p-2.5 font-body text-sm font-semibold outline-none focus:border-cobalt-signal shadow-sm"
              placeholder="acme_admin"
            />
            {errors.username && (
              <p className="font-mono text-[11px] font-bold text-rust-warn mt-1">
                {errors.username.message}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="login-password"
              className="block font-mono text-xs font-extrabold uppercase tracking-widest text-ink-dark mb-1"
            >
              PASSWORD
            </label>
            <input
              id="login-password"
              type="password"
              {...register("password")}
              className="w-full bg-white border-thick border-ink-dark p-2.5 font-body text-sm font-semibold outline-none focus:border-cobalt-signal shadow-sm"
              placeholder="••••••••"
            />
            {errors.password && (
              <p className="font-mono text-[11px] font-bold text-rust-warn mt-1">
                {errors.password.message}
              </p>
            )}
          </div>

          {/* Inline Server Error Display */}
          {serverError && (
            <div
              id="login-error-box"
              className="p-3 bg-rust-bg border-thick border-rust-warn text-rust-warn font-mono text-xs font-bold"
            >
              <span className="font-extrabold uppercase">AUTH FAILURE</span> {serverError}
            </div>
          )}

          <button
            id="login-submit"
            type="submit"
            disabled={isSubmitting}
            className="w-full mt-2 bg-yellow-signal text-ink-dark border-thick border-ink-dark py-3 font-display font-extrabold text-sm uppercase shadow-hard hover:bg-ink-dark hover:text-yellow-signal transition-none cursor-pointer disabled:opacity-50"
          >
            {isSubmitting ? "// AUTHENTICATING..." : "AUTHENTICATE [ENTER]"}
          </button>
        </form>

        {/* Footer Demo Note */}
        <div className="p-3 bg-surface-alt border-t-thick border-ink-dark font-mono text-[10px] text-ink-muted text-center uppercase tracking-widest">
          DEMO: ACME_ADMIN / ADMIN123 • ACME_ANALYST / ANALYST123
        </div>
      </div>
    </div>
  );
}
