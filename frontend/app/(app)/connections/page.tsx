"use client";

import React from "react";

export default function ConnectionsPage() {
  return (
    <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
      <div className="border-b-thick border-ink-dark pb-3 flex items-center justify-between">
        <h1 className="font-display text-2xl font-extrabold uppercase tracking-tight">
          Live Database Connections
        </h1>
        <button className="bg-cobalt-signal text-white border-med border-ink-dark px-4 py-2 font-display font-extrabold text-xs uppercase shadow-sm hover:bg-yellow-signal hover:text-ink-dark cursor-pointer">
          + NEW CONNECTION
        </button>
      </div>

      <div className="grid grid-cols-[repeat(auto-fill,minmax(340px,1fr))] gap-4">
        <div className="bg-white border-thick border-ink-dark p-4.5 shadow-hard flex flex-col gap-3.5 border-t-[6px] border-t-emerald-pass">
          <div className="flex items-center justify-between border-b-med border-ink-dark pb-2">
            <span className="font-display font-extrabold text-base uppercase">Prod-Postgres-Primary</span>
            <span className="font-mono text-[11px] font-extrabold px-2 py-1 border-med border-emerald-pass bg-emerald-bg text-emerald-pass uppercase">
              CONNECTED
            </span>
          </div>
          <div className="font-mono text-xs font-semibold">HOST: localhost:5432 / DB: platform</div>
          <div className="font-mono text-xs font-semibold text-emerald-pass">ENCRYPTION: FERNET AES-256 (OK)</div>
          <div className="mt-auto flex gap-2 pt-2">
            <button className="bg-ink-dark text-white border-med border-ink-dark px-3 py-2 font-display font-extrabold text-xs uppercase shadow-sm hover:bg-yellow-signal hover:text-ink-dark cursor-pointer">
              TEST CONNECTION
            </button>
            <button className="bg-ink-dark text-white border-med border-ink-dark px-3 py-2 font-display font-extrabold text-xs uppercase shadow-sm hover:bg-yellow-signal hover:text-ink-dark cursor-pointer">
              SYNC SCHEMA
            </button>
          </div>
        </div>

        <div className="bg-white border-thick border-ink-dark p-4.5 shadow-hard flex flex-col gap-3.5 border-t-[6px] border-t-emerald-pass">
          <div className="flex items-center justify-between border-b-med border-ink-dark pb-2">
            <span className="font-display font-extrabold text-base uppercase">MySQL-Replica-Warehouse</span>
            <span className="font-mono text-[11px] font-extrabold px-2 py-1 border-med border-emerald-pass bg-emerald-bg text-emerald-pass uppercase">
              CONNECTED
            </span>
          </div>
          <div className="font-mono text-xs font-semibold">HOST: 10.0.4.12:3306 / DB: warehouse</div>
          <div className="font-mono text-xs font-semibold text-emerald-pass">ENCRYPTION: FERNET AES-256 (OK)</div>
          <div className="mt-auto flex gap-2 pt-2">
            <button className="bg-ink-dark text-white border-med border-ink-dark px-3 py-2 font-display font-extrabold text-xs uppercase shadow-sm hover:bg-yellow-signal hover:text-ink-dark cursor-pointer">
              TEST CONNECTION
            </button>
            <button className="bg-ink-dark text-white border-med border-ink-dark px-3 py-2 font-display font-extrabold text-xs uppercase shadow-sm hover:bg-yellow-signal hover:text-ink-dark cursor-pointer">
              SYNC SCHEMA
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
