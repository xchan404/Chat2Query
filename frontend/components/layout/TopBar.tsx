"use client";

import React from "react";
import { useUIStore } from "@/lib/stores/uiStore";
import { useAuth } from "@/lib/auth/AuthProvider";

export function TopBar() {
  const openCmdk = useUIStore((state) => state.openCmdk);
  const { user, logout } = useAuth();

  return (
    <header className="flex items-center justify-between bg-white text-gray-900 px-4 border-b border-gray-300 h-12 shrink-0 select-none">
      {/* Product Title */}
      <div className="flex items-center gap-2.5 font-bold text-xs tracking-tight text-gray-900">
        <div className="w-2.5 h-2.5 bg-blue-600 rounded-sm" />
        <span className="font-semibold text-gray-900">Chat2Query</span>
        <span className="text-gray-400 font-normal">/</span>
        <span className="text-gray-600 font-medium">Enterprise Control Room</span>
        <span className="bg-gray-100 text-gray-600 text-[10px] px-1.5 py-0.5 font-mono font-medium rounded border border-gray-200 ml-1">
          v1.0
        </span>
      </div>

      {/* Global Search Input Trigger */}
      <div className="flex-1 max-w-md mx-6">
        <button
          id="topbar-cmdk-btn"
          onClick={openCmdk}
          className="w-full bg-gray-50 hover:bg-gray-100 text-gray-500 border border-gray-300 rounded-md px-3 py-1 text-xs flex items-center justify-between transition-colors cursor-pointer"
        >
          <span className="flex items-center gap-2 text-gray-500 font-normal">
            <svg className="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Search commands, connections, or documents...
          </span>
          <kbd className="bg-white text-gray-500 px-1.5 py-0.5 text-[10px] font-mono rounded border border-gray-300">
            Ctrl K
          </kbd>
        </button>
      </div>

      {/* User Info & Actions */}
      <div className="flex items-center gap-3 text-xs">
        {user && (
          <div className="flex items-center gap-2 text-gray-600">
            <span className="font-medium text-gray-800 bg-gray-100 px-2 py-0.5 rounded border border-gray-200">
              {user.username}
            </span>
            <span className="bg-blue-50 text-blue-700 text-[10px] font-semibold px-2 py-0.5 rounded border border-blue-200 uppercase">
              {user.roles[0] ?? "user"}
            </span>
          </div>
        )}

        {user && (
          <button
            id="topbar-logout-btn"
            onClick={logout}
            className="bg-white hover:bg-gray-50 text-gray-700 hover:text-red-700 border border-gray-300 rounded-md px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer"
          >
            Sign out
          </button>
        )}
      </div>
    </header>
  );
}
