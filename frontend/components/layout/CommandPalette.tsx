"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useUIStore } from "@/lib/stores/uiStore";

const cmdList = [
  { href: "/chat", label: "GOTO: Chat & Evidence Rail", num: "01" },
  { href: "/connections", label: "GOTO: Database Connections", num: "02" },
  { href: "/knowledge", label: "GOTO: Knowledge Bases", num: "03" },
  { href: "/permissions", label: "GOTO: Permissions Matrix", num: "04" },
  { href: "/audit", label: "GOTO: Audit Logs", num: "05" },
];

export function CommandPalette() {
  const router = useRouter();
  const { isCmdkOpen, closeCmdk, toggleCmdk } = useUIStore();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        toggleCmdk();
      }
      if (e.key === "Escape" && isCmdkOpen) {
        closeCmdk();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isCmdkOpen, toggleCmdk, closeCmdk]);

  if (!isCmdkOpen) return null;

  return (
    <div className="fixed inset-0 bg-ink-dark/85 z-[999] flex items-center justify-center">
      <div className="bg-paper border-thick border-ink-dark shadow-[8px_8px_0px_#FFD600] w-[620px] max-w-[90vw] flex flex-col">
        <div className="bg-ink-dark text-white p-3 px-4 font-display font-extrabold text-sm uppercase flex items-center justify-between">
          <span>COMMAND PALETTE (CTRL+K)</span>
          <button
            onClick={closeCmdk}
            className="bg-rust-warn text-white border-none px-2 py-0.5 font-extrabold cursor-pointer"
          >
            [X]
          </button>
        </div>
        <div className="p-5 flex flex-col gap-4">
          <input
            type="text"
            className="w-full bg-white border-thick border-ink-dark p-3 font-mono text-sm font-bold outline-none"
            placeholder="Type a command or search action..."
            autoFocus
          />
          <div className="flex flex-col gap-1.5">
            {cmdList.map((cmd) => (
              <button
                key={cmd.href}
                onClick={() => {
                  router.push(cmd.href);
                  closeCmdk();
                }}
                className="flex items-center justify-between p-3 bg-white border-med border-ink-dark font-display font-extrabold text-xs uppercase shadow-sm hover:bg-yellow-signal hover:text-ink-dark transition-none text-left cursor-pointer"
              >
                <span>{cmd.label}</span>
                <span className="font-mono text-xs font-bold px-1.5 py-0.5 bg-ink-dark text-white">
                  {cmd.num}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
