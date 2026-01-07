"use client";

import Link from "next/link";
import { Map, Home, FileText, Sparkles, Search } from "lucide-react";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export function Header() {
  const pathname = usePathname();

  const navItems = [
    { href: "/", label: "Dashboard", icon: Home },
    { href: "/upload", label: "Upload", icon: FileText },
    { href: "/lookup", label: "Find Results", icon: Search },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/20 glass shadow-lg shadow-blue-500/5">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-20 items-center justify-between">
          <Link href="/" className="flex items-center space-x-3 group">
            <div className="relative p-3 rounded-2xl bg-gradient-to-br from-blue-500 via-green-500 to-red-500 group-hover:scale-105 transition-transform duration-300 shadow-lg">
              <Map className="h-7 w-7 text-white relative z-10" />
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-600 via-green-600 to-red-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300 blur-sm"></div>
            </div>
            <div className="flex flex-col">
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 via-green-600 to-red-600 bg-clip-text text-transparent">
                Ultimate Sellers Portal
              </span>
              <span className="text-xs text-slate-600 font-medium flex items-center gap-1">
                <Sparkles className="h-3 w-3 text-blue-500" />
                AI-Powered Land Intelligence
              </span>
            </div>
          </Link>

          <nav className="flex items-center space-x-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "relative flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold transition-all duration-300 overflow-hidden",
                    isActive
                      ? "text-white shadow-lg"
                      : "text-slate-700 hover:text-slate-900 hover:bg-white/50"
                  )}
                >
                  {isActive && (
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-500 via-green-500 to-red-500 animate-pulse"></div>
                  )}
                  <Icon className={cn("h-5 w-5 relative z-10", isActive && "text-white")} />
                  <span className="relative z-10">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}
