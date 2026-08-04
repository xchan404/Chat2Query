"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth/AuthProvider";

const navItems = [
  {
    href: "/chat",
    label: "Chat & Evidence",
    num: "01",
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>
    ),
  },
  {
    href: "/connections",
    label: "Live Connections",
    num: "02",
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
      </svg>
    ),
  },
  {
    href: "/knowledge",
    label: "Knowledge Bases",
    num: "03",
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
  },
  {
    href: "/permissions",
    label: "Permissions Matrix",
    num: "04",
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
  {
    href: "/audit",
    label: "Audit Trail Logs",
    num: "05",
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 17v-2m3 2v-4m3 2v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const isAdmin = user?.roles?.includes("admin");
  const filteredNavItems = navItems.filter(
    (item) => item.href !== "/audit" || isAdmin
  );

  return (
    <aside className="bg-gray-50 border-r border-gray-300 flex flex-col p-3 max-[860px]:p-2 gap-4 w-60 max-[860px]:w-14 shrink-0 select-none">
      {/* Navigation Label */}
      <div className="text-[10px] font-semibold uppercase text-gray-500 tracking-wider pl-2 max-[860px]:hidden">
        Navigation
      </div>

      {/* Navigation List */}
      <nav className="flex flex-col gap-1">
        {filteredNavItems.map((item) => {
          const isActive = pathname === item.href || (pathname === "/" && item.href === "/chat");
          return (
            <Link
              key={item.href}
              href={item.href}
              title={item.label}
              className={`flex items-center justify-between max-[860px]:justify-center w-full px-2.5 py-2 rounded-md text-xs transition-colors ${
                isActive
                  ? "bg-gray-200/90 text-gray-900 font-semibold border-l-2 border-blue-600 pl-2"
                  : "text-gray-700 hover:bg-gray-100 hover:text-gray-900 font-normal"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <span className={isActive ? "text-blue-600" : "text-gray-500"}>
                  {item.icon}
                </span>
                <span className="max-[860px]:hidden">{item.label}</span>
              </div>
              <span
                className={`font-mono text-[10px] max-[860px]:hidden ${
                  isActive ? "text-blue-700 font-bold" : "text-gray-400"
                }`}
              >
                {item.num}
              </span>
            </Link>
          );
        })}
      </nav>

      {/* Footer System Readiness */}
      <div className="mt-auto pt-3 border-t border-gray-200">
        <div className="flex items-center gap-2 max-[860px]:justify-center text-[11px] bg-white border border-gray-200 rounded-md p-2 text-gray-700">
          <div className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
          <span className="max-[860px]:hidden font-mono text-[10px] text-gray-600 font-medium">
            ONLINE • PG16
          </span>
        </div>
      </div>
    </aside>
  );
}
