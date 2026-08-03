"use client";

/**
 * Login page — authenticates against POST /api/auth/login.
 *
 * Design: brutalist token system, full-page centered card.
 * Validation: react-hook-form + zod.
 * Error handling: inline error under the form (no redirect loop, no silent failure).
 */

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/lib/auth/AuthProvider";

// ── Zod schema ────────────────────────────────────────────────────────────────

const loginSchema = z.object({
  username: z.string().min(1, "Username is required").max(100),
  password: z.string().min(1, "Password is required"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

// ── Component ─────────────────────────────────────────────────────────────────

export default function LoginPage() {
  const { login } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormValues) => {
    setServerError(null);
    try {
      await login(data.username, data.password);
      // AuthProvider.login() calls router.push("/chat") on success
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Authentication failed. Check credentials and try again.";
      setServerError(message);
    }
  };

  return (
    <div className="min-h-screen bg-paper flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Brand header */}
        <div className="bg-ink-dark text-white p-4 px-5 flex items-center justify-between border-b-0 border-thick border-ink-dark">
          <span className="font-display font-extrabold text-base uppercase tracking-wider">
            Chat2Query // Control Engine
          </span>
          <span className="bg-yellow-signal text-ink-dark px-2 py-0.5 font-mono text-[11px] font-extrabold border border-ink-dark">
            v1.0-AUDIT
          </span>
        </div>

        {/* Login form card */}
        <div className="bg-surface border-thick border-ink-dark border-t-0 shadow-hard">
          <div className="p-6 border-b-med border-ink-dark bg-surface-alt">
            <h1 className="font-display font-extrabold text-lg uppercase tracking-wide text-ink-dark">
              Operator Authentication
            </h1>
            <p className="font-mono text-[11px] text-ink-muted mt-1 uppercase tracking-widest">
              // Multi-tenant access control — credentials required
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} noValidate className="p-6 flex flex-col gap-5">
            {/* Username */}
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="login-username"
                className="font-mono text-[11px] font-extrabold uppercase text-ink-dark tracking-widest"
              >
                Username
              </label>
              <input
                id="login-username"
                type="text"
                autoComplete="username"
                autoFocus
                aria-invalid={!!errors.username}
                aria-describedby={errors.username ? "login-username-error" : undefined}
                className={`bg-white border-thick border-ink-dark p-3 font-body text-sm font-semibold outline-none w-full shadow-sm focus:border-cobalt-signal ${
                  errors.username ? "border-rust-warn bg-rust-bg" : ""
                }`}
                placeholder="acme_admin"
                {...register("username")}
              />
              {errors.username && (
                <span
                  id="login-username-error"
                  role="alert"
                  className="font-mono text-[11px] font-bold text-rust-warn flex items-center gap-1"
                >
                  ⚠ {errors.username.message}
                </span>
              )}
            </div>

            {/* Password */}
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="login-password"
                className="font-mono text-[11px] font-extrabold uppercase text-ink-dark tracking-widest"
              >
                Password
              </label>
              <input
                id="login-password"
                type="password"
                autoComplete="current-password"
                aria-invalid={!!errors.password}
                aria-describedby={errors.password ? "login-password-error" : undefined}
                className={`bg-white border-thick border-ink-dark p-3 font-body text-sm font-semibold outline-none w-full shadow-sm ${
                  errors.password ? "border-rust-warn bg-rust-bg" : ""
                }`}
                placeholder="••••••••"
                {...register("password")}
              />
              {errors.password && (
                <span
                  id="login-password-error"
                  role="alert"
                  className="font-mono text-[11px] font-bold text-rust-warn flex items-center gap-1"
                >
                  ⚠ {errors.password.message}
                </span>
              )}
            </div>

            {/* Server-side error — inline, not a redirect loop */}
            {serverError && (
              <div
                id="login-server-error"
                role="alert"
                aria-live="assertive"
                className="bg-rust-bg border-thick border-rust-warn p-3 flex items-start gap-2"
              >
                <span className="font-mono text-xs font-extrabold text-rust-warn uppercase tracking-widest shrink-0">
                  AUTH FAILURE
                </span>
                <span className="font-mono text-xs text-rust-warn font-bold">
                  {serverError}
                </span>
              </div>
            )}

            {/* Submit */}
            <button
              id="login-submit"
              type="submit"
              disabled={isSubmitting}
              className="bg-yellow-signal text-ink-dark border-thick border-ink-dark px-6 py-3 font-display font-extrabold text-sm uppercase shadow-hard hover:bg-ink-dark hover:text-yellow-signal disabled:opacity-50 disabled:cursor-not-allowed transition-none cursor-pointer w-full"
            >
              {isSubmitting ? (
                <span className="font-mono text-[12px] animate-pulse">
                  // Authenticating...
                </span>
              ) : (
                "AUTHENTICATE [ENTER]"
              )}
            </button>
          </form>
        </div>

        {/* Footer hint */}
        <div className="mt-4 font-mono text-[10px] text-ink-muted text-center uppercase tracking-widest">
          Demo: acme_admin / admin123 · acme_analyst / analyst123
        </div>
      </div>
    </div>
  );
}
