"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { SearchBar } from "./SearchBar";
import { cn } from "@/lib/utils";

export function Navbar() {
  const pathname = usePathname();
  const isHome = pathname === "/";

  return (
    <nav className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/90 backdrop-blur-md">
      <div className="container mx-auto px-4 h-16 flex items-center gap-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <span className="text-2xl">⌚</span>
          <span className="font-bold text-white text-lg tracking-tight">
            Watch<span className="text-blue-400">Lens</span>
          </span>
        </Link>

        {/* Search bar — only show outside homepage */}
        {!isHome && (
          <div className="flex-1 max-w-xl">
            <SearchBar compact />
          </div>
        )}

        {/* Nav links */}
        <div className="ml-auto flex items-center gap-1">
          <Link
            href="/search"
            className={cn(
              "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
              pathname === "/search"
                ? "bg-blue-600 text-white"
                : "text-slate-400 hover:text-white hover:bg-slate-800"
            )}
          >
            Explorar
          </Link>
        </div>
      </div>
    </nav>
  );
}
