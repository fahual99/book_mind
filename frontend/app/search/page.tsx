"use client";

import { useState } from "react";
import { useLazyGraphQL } from "@/lib/hooks";
import { SEARCH_BOOKS } from "@/graphql/queries";
import BookCard from "@/components/BookCard";
import BookModal from "@/components/BookModal";
import { useUser } from "@/app/providers";
import Link from "next/link";

interface Book {
  bookId: number;
  title: string;
  authors: string;
  averageRating: number;
  genres: string;
  imageUrl?: string | null;
  smallImageUrl?: string | null;
  ratingsCount?: number;
  originalPublicationYear?: number | null;
}

export default function SearchPage() {
  const { username } = useUser();
  const [query, setQuery] = useState("");
  const [selectedBookId, setSelectedBookId] = useState<number | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const { execute: searchBooks, data, loading } = useLazyGraphQL<{ searchBooks: Book[] }>(SEARCH_BOOKS);

  if (!username) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">Please log in first</h2>
          <Link href="/" className="gradient-text text-lg hover:opacity-80 transition-all">Go to Login &rarr;</Link>
        </div>
      </div>
    );
  }

  const handleSearch = () => {
    if (query.trim()) {
      searchBooks({ query: query.trim(), n: 30 });
      setHasSearched(true);
    }
  };

  const results = data?.searchBooks || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-3xl sm:text-4xl font-bold mb-2">
          <span className="gradient-text">Search</span> Books
        </h1>
        <p className="text-[var(--color-text-secondary)]">Search across titles, authors, and descriptions</p>
      </div>

      {/* Search Bar */}
      <div className="max-w-2xl mx-auto mb-10">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <svg className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder={'Try: "dark fantasy", "Stephen King", "dystopian adventure"...'}
              className="w-full pl-12 pr-4 py-3.5 rounded-2xl bg-[var(--color-bg-card)] border border-[var(--color-border)] text-[var(--color-text-primary)] text-sm outline-none transition-all focus:border-[var(--color-accent-1)] focus:shadow-[0_0_0_3px_rgba(99,102,241,0.15)] placeholder:text-[var(--color-text-muted)]"
              autoFocus
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={!query.trim()}
            className="px-6 py-3.5 rounded-2xl bg-gradient-to-r from-[var(--color-accent-1)] to-[var(--color-accent-2)] text-white font-semibold text-sm hover:opacity-90 disabled:opacity-40 transition-all"
          >
            Search
          </button>
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div className="flex justify-center py-20"><div className="spinner" /></div>
      ) : results.length > 0 ? (
        <>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold">{results.length} results found</h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {results.map((book) => (
              <BookCard key={book.bookId} book={book} onClick={() => setSelectedBookId(book.bookId)} />
            ))}
          </div>
        </>
      ) : hasSearched ? (
        <div className="text-center py-20">
          <p className="text-[var(--color-text-secondary)]">No books found for &quot;{query}&quot;</p>
        </div>
      ) : (
        <div className="text-center py-20 text-[var(--color-text-muted)]">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="mx-auto mb-4 opacity-30">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <p>Start typing to search for books</p>
        </div>
      )}

      {selectedBookId && <BookModal bookId={selectedBookId} onClose={() => setSelectedBookId(null)} />}
    </div>
  );
}
