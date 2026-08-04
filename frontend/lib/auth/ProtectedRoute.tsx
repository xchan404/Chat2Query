"use client";

/**
 * ProtectedRoute — redirect to /login if not authenticated.
 * Renders a full-page loading state while auth is being restored from storage.
 */

import React from "react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth/AuthProvider";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-paper">
        <div className="bg-surface border-thick border-ink-dark p-8 shadow-hard flex flex-col items-center gap-4">
          <div className="font-mono text-xs font-extrabold uppercase text-ink-muted tracking-widest animate-pulse">
            // Restoring session...
          </div>
          <div className="w-full h-0.5 bg-ink-dark/10">
            <div
              className="h-full bg-yellow-signal animate-[loading_1.2s_ease-in-out_infinite]"
              style={{ width: "60%" }}
            />
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    // Will redirect via useEffect — render nothing while redirecting
    return null;
  }

  return <>{children}</>;
}
