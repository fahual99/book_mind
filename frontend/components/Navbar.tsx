"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUser } from "@/app/providers";

const navLinks = [
  {
    href: "/",
    label: "Discover",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.3-4.3" />
      </svg>
    ),
  },
  {
    href: "/favorites",
    label: "Favorites",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
      </svg>
    ),
  },
  {
    href: "/profile",
    label: "Profile",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    ),
  },
  {
    href: "/search",
    label: "Search",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
      </svg>
    ),
  },
];

export default function Navbar() {
  const pathname = usePathname();
  const { username, favoriteIds } = useUser();

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-xl bg-[var(--color-bg-primary)]/80 border-b border-[var(--color-border)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <Link href="/" className="flex items-center gap-2 no-underline">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[var(--color-accent-1)] to-[var(--color-accent-3)] flex items-center justify-center">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
              </svg>
            </div>
            <span className="text-lg font-bold text-[var(--color-text-primary)]">
              Book<span className="gradient-text">Mind</span>{" "}
              <span className="text-xs font-medium px-1.5 py-0.5 rounded-md bg-[var(--color-accent-1)]/20 text-[var(--color-accent-1)]">
                AI
              </span>
            </span>
          </Link>

          {/* Nav Links */}
          <div className="flex items-center gap-1">
            {navLinks.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 no-underline ${
                    isActive
                      ? "bg-[var(--color-accent-1)]/15 text-[var(--color-accent-1)]"
                      : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-white/5"
                  }`}
                >
                  {link.icon}
                  <span className="hidden sm:inline">{link.label}</span>
                  {link.label === "Favorites" && favoriteIds.length > 0 && (
                    <span className="inline-flex items-center justify-center w-5 h-5 text-[0.65rem] font-bold rounded-full bg-[var(--color-accent-3)] text-white">
                      {favoriteIds.length}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>

          {/* User Badge */}
          {username && (
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-[var(--color-border)]">
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[var(--color-accent-1)] to-[var(--color-accent-2)] flex items-center justify-center text-xs font-bold text-white">
                {username[0].toUpperCase()}
              </div>
              <span className="text-sm text-[var(--color-text-secondary)]">{username}</span>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
