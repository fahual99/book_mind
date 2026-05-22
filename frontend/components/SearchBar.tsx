"use client";

import { useState, useCallback } from "react";

interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
}

export default function SearchBar({ onSearch, placeholder = "Search by title, author, or keyword..." }: SearchBarProps) {
  const [value, setValue] = useState("");

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = e.target.value;
      setValue(val);
      // Debounce
      const timeout = setTimeout(() => onSearch(val), 350);
      return () => clearTimeout(timeout);
    },
    [onSearch]
  );

  const handleClear = () => {
    setValue("");
    onSearch("");
  };

  return (
    <div className="relative max-w-2xl mx-auto">
      <div className="relative flex items-center">
        <svg
          className="absolute left-4 text-[var(--color-text-muted)]"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.3-4.3" />
        </svg>
        <input
          type="text"
          value={value}
          onChange={handleChange}
          placeholder={placeholder}
          className="w-full pl-12 pr-12 py-3.5 rounded-2xl bg-[var(--color-bg-card)] border border-[var(--color-border)] text-[var(--color-text-primary)] text-sm outline-none transition-all duration-300 focus:border-[var(--color-accent-1)] focus:shadow-[0_0_0_3px_rgba(99,102,241,0.15)] placeholder:text-[var(--color-text-muted)]"
          id="search-input"
        />
        {value && (
          <button
            onClick={handleClear}
            className="absolute right-4 w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-[var(--color-text-secondary)] hover:text-white hover:bg-white/20 transition-all"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
}
