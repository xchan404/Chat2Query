"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth/AuthProvider";

const navItems = [
  { href: "/chat", label: "1. Chat & Evidence", num: "01" },
  { href: "/connections", label: "2. Live Connections", num: "02" },
  { href: "/knowledge", label: "3. Knowledge Bases", num: "03" },
  { href: "/permissions", label: "4. Permissions Matrix", num: "04" },
  { href: "/audit", label: "5. Audit Records", num: "05" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  return (
    <aside className="bg-surface border-r-thick border-ink-dark flex flex-col p-4 gap-5 w-60 shrink-0">
      <div className="bg-yellow-bg border-med border-ink-dark p-2.5 shadow-sm border-t-4 border-t-yellow-signal">
        <div className="font-display font-extrabold text-xs tracking-wider uppercase">
          {user?.username ?? "—"}
        </div>
        <div className="font-mono text-[11px] text-ink-muted mt-0.5">
          ID: {user?.id?.slice(0, 13) ?? "—"}
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <div className="font-mono text-[10px] font-extrabold uppercase text-ink-muted tracking-widest pl-1">
          // Control Views
        </div>
        <nav className="flex flex-col gap-1.5">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (pathname === "/" && item.href === "/chat");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center justify-between w-full p-2.5 border-med font-display font-extrabold text-xs uppercase shadow-sm transition-none ${
                  isActive
                    ? "bg-cobalt-signal text-white border-ink-dark shadow-[3px_3px_0px_#0F1419]"
                    : "bg-paper text-ink-dark border-ink-dark hover:bg-yellow-signal hover:text-ink-dark"
                }`}
              >
                <span>{item.label}</span>
                <span
                  className={`font-mono text-[11px] px-1.5 py-0.5 font-bold ${
                    isActive ? "bg-yellow-signal text-ink-dark" : "bg-ink-dark text-white"
                  }`}
                >
                  {item.num}
                </span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="mt-auto pt-3 border-t-med border-ink-dark">
        <div className="flex items-center gap-2 font-mono text-[11px] font-extrabold bg-emerald-bg border-med border-ink-dark p-2 text-emerald-pass">
          <div className="w-2.5 h-2.5 bg-emerald-pass border border-ink-dark" />
          <span>ENGINE: ONLINE (PG16)</span>
        </div>
      </div>
    </aside>
  );
}
