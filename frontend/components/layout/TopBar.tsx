"use client";

import React from "react";
import { useUIStore } from "@/lib/stores/uiStore";
import { useAuth } from "@/lib/auth/AuthProvider";

export function TopBar() {
  const openCmdk = useUIStore((state) => state.openCmdk);
  const { user, logout } = useAuth();

  return (
    <header className="grid-cols-1 flex items-center justify-between bg-ink-dark text-white px-4 border-b-thick border-ink-dark h-12">
      <div className="flex items-center gap-3 font-display font-extrabold text-base tracking-wider uppercase">
        <span>Chat2Query // Control Engine</span>
        <span className="bg-yellow-signal text-ink-dark px-2 py-0.5 font-mono text-[11px] font-extrabold border border-ink-dark">
          v1.0-AUDIT
        </span>
      </div>
      <div className="flex items-center gap-3 font-mono text-xs">
        {user && (
          <>
            <span className="bg-white/10 px-2 py-1 border border-white/25 font-bold uppercase">
              {user.username}
            </span>
            <span className="bg-white/10 px-2 py-1 border border-white/25 font-bold uppercase">
              ROLE: {user.roles[0] ?? "user"}
            </span>
          </>
        )}
        <button
          id="topbar-cmdk-btn"
          onClick={openCmdk}
          className="bg-yellow-signal text-ink-dark border-med border-ink-dark px-2.5 py-1 font-mono text-[11px] font-extrabold flex items-center gap-2 shadow-sm hover:bg-white transition-none cursor-pointer"
        >
          <span>SEARCH / CMD</span>
          <kbd className="bg-ink-dark text-white px-1 py-0.5 text-[10px]">CTRL+K</kbd>
        </button>
        {user && (
          <button
            id="topbar-logout-btn"
            onClick={logout}
            className="bg-rust-warn text-white border-med border-rust-warn px-2.5 py-1 font-mono text-[11px] font-extrabold hover:bg-white hover:text-rust-warn transition-none cursor-pointer"
          >
            LOGOUT
          </button>
        )}
      </div>
    </header>
  );
}

