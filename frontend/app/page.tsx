"use client";

import { useState } from "react";
import { useGraphQL } from "@/lib/hooks";
import {
  GET_HOMEPAGE_BOOKS,
  GET_TRENDING_BOOKS,
  GET_GENRE_BOOKS,
  GET_STATS,
  GET_GENRES,
  GET_BOOKS,
} from "@/graphql/queries";
import BookCard from "@/components/BookCard";
import RecommendationRow from "@/components/RecommendationRow";
import SearchBar from "@/components/SearchBar";
import BookModal from "@/components/BookModal";
import { useUser } from "./providers";

// ── Book type ──
interface Book {
  bookId: number;
  title: string;
  authors: string;
  averageRating: number;
  genres: string;
  imageUrl?: string | null;
  smallImageUrl?: string | null;
  originalPublicationYear?: number | null;
  pages?: number | null;
  ratingsCount?: number;
  languageCode?: string | null;
}

// Login Screen
function LoginScreen() {
  const { setUsername } = useUser();
  const [input, setInput] = useState("");

  const handleLogin = () => {
    if (input.trim()) {
      setUsername(input.trim());
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="login-card">
        <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-[var(--color-accent-1)] to-[var(--color-accent-3)] flex items-center justify-center">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            <path d="M8 7h8M8 11h6" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold mb-2">
          Welcome to <span className="gradient-text">BookMind AI</span>
        </h1>
        <p className="text-[var(--color-text-secondary)] text-sm mb-6">
          Enter a username to start discovering your next favorite book.
          <br />
          No password required.
        </p>
        <div className="flex flex-col gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter your username..."
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
            autoFocus
          />
          <button
            onClick={handleLogin}
            disabled={!input.trim()}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-[var(--color-accent-1)] to-[var(--color-accent-2)] text-white font-semibold text-sm transition-all hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Get Started
          </button>
        </div>
      </div>
    </div>
  );
}

// Main Page Content
function DiscoverPage() {
  const [selectedBookId, setSelectedBookId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [browsePage, setBrowsePage] = useState(1);
  const [selectedGenre, setSelectedGenre] = useState("");
  const [sortBy, setSortBy] = useState("average_rating");
  const [sortOrder, setSortOrder] = useState("desc");

  const { data: statsData } = useGraphQL<{ stats: { totalBooks: number; totalAuthors: number; totalGenres: number; avgRating: number } }>(GET_STATS);
  const { data: genresData } = useGraphQL<{ genres: { genre: string; count: number }[] }>(GET_GENRES);
  const { data: homepageData, loading: loadingHomepage } = useGraphQL<{ homepageBooks: Book[] }>(GET_HOMEPAGE_BOOKS);
  const { data: trendingData } = useGraphQL<{ trendingBooks: Book[] }>(GET_TRENDING_BOOKS);

  // Featured genre rows
  const { data: fantasyData } = useGraphQL<{ genreBooks: Book[] }>(GET_GENRE_BOOKS, { genre: "fantasy", limit: 20 });
  const { data: romanceData } = useGraphQL<{ genreBooks: Book[] }>(GET_GENRE_BOOKS, { genre: "romance", limit: 20 });
  const { data: scifiData } = useGraphQL<{ genreBooks: Book[] }>(GET_GENRE_BOOKS, { genre: "science-fiction", limit: 20 });
  const { data: mysteryData } = useGraphQL<{ genreBooks: Book[] }>(GET_GENRE_BOOKS, { genre: "mystery", limit: 20 });

  // Browse mode
  const isBrowsing = searchQuery || selectedGenre;
  const { data: browseData, loading: loadingBrowse } = useGraphQL<{
    books: { books: Book[]; total: number; page: number; totalPages: number };
  }>(
    GET_BOOKS,
    {
      page: browsePage,
      perPage: 24,
      genre: selectedGenre || undefined,
      search: searchQuery || undefined,
      sortBy,
      sortOrder,
    },
    { skip: !isBrowsing }
  );

  const stats = statsData?.stats;
  const genres = genresData?.genres || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
      {/* Hero */}
      <section className="pt-12 pb-10 text-center">
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-4" style={{ fontFamily: "var(--font-display)" }}>
          Discover Your Next
          <br />
          <span className="gradient-text">Favorite Book</span>
        </h1>
        <p className="text-[var(--color-text-secondary)] text-lg max-w-2xl mx-auto mb-8">
          Powered by FAISS Vector Search &amp; Hybrid Recommendation, an AI that understands what you love to read.
        </p>

        {/* Search */}
        <SearchBar onSearch={(q) => { setSearchQuery(q); setBrowsePage(1); }} />

        {/* Stats */}
        {stats && (
          <div className="flex items-center justify-center gap-8 mt-8 flex-wrap">
            {[
              { value: stats.totalBooks.toLocaleString(), label: "Books" },
              { value: stats.totalAuthors.toLocaleString(), label: "Authors" },
              { value: stats.totalGenres, label: "Genres" },
              { value: stats.avgRating, label: "Avg Rating" },
            ].map((s) => (
              <div key={s.label} className="text-center">
                <div className="text-2xl font-bold gradient-text">{s.value}</div>
                <div className="text-xs text-[var(--color-text-muted)]">{s.label}</div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Filters bar */}
      {isBrowsing && (
        <div className="flex flex-wrap gap-3 mb-6 items-end">
          <div>
            <label className="text-xs text-[var(--color-text-muted)] block mb-1">Genre</label>
            <select
              value={selectedGenre}
              onChange={(e) => { setSelectedGenre(e.target.value); setBrowsePage(1); }}
              className="px-3 py-2 rounded-lg bg-[var(--color-bg-card)] border border-[var(--color-border)] text-sm text-[var(--color-text-primary)] outline-none"
            >
              <option value="">All Genres</option>
              {genres.map((g) => (
                <option key={g.genre} value={g.genre}>
                  {g.genre} ({g.count})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-[var(--color-text-muted)] block mb-1">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 rounded-lg bg-[var(--color-bg-card)] border border-[var(--color-border)] text-sm text-[var(--color-text-primary)] outline-none"
            >
              <option value="title">Title</option>
              <option value="average_rating">Rating</option>
              <option value="ratings_count">Popularity</option>
              <option value="original_publication_year">Year</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-[var(--color-text-muted)] block mb-1">Order</label>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="px-3 py-2 rounded-lg bg-[var(--color-bg-card)] border border-[var(--color-border)] text-sm text-[var(--color-text-primary)] outline-none"
            >
              <option value="asc">Ascending</option>
              <option value="desc">Descending</option>
            </select>
          </div>
          <button
            onClick={() => { setSearchQuery(""); setSelectedGenre(""); }}
            className="px-3 py-2 rounded-lg bg-white/5 border border-[var(--color-border)] text-sm text-[var(--color-text-secondary)] hover:text-white transition-all"
          >
            Clear Filters
          </button>
        </div>
      )}

      {/* Browse Results */}
      {isBrowsing ? (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">
              {searchQuery ? `Results for "${searchQuery}"` : selectedGenre || "All Books"}
            </h2>
            {browseData?.books && (
              <span className="text-sm text-[var(--color-text-muted)]">{browseData.books.total} books</span>
            )}
          </div>

          {loadingBrowse ? (
            <div className="flex justify-center py-20">
              <div className="spinner" />
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {browseData?.books?.books?.map((book) => (
                  <BookCard key={book.bookId} book={book} onClick={() => setSelectedBookId(book.bookId)} />
                ))}
              </div>

              {/* Pagination */}
              {browseData?.books?.totalPages && browseData.books.totalPages > 1 && (
                <div className="flex justify-center gap-2 mt-8">
                  {browsePage > 1 && (
                    <button onClick={() => setBrowsePage(browsePage - 1)} className="px-4 py-2 rounded-lg bg-[var(--color-bg-card)] border border-[var(--color-border)] text-sm hover:bg-white/5 transition-all">
                      &larr; Prev
                    </button>
                  )}
                  {Array.from({ length: Math.min(5, browseData.books.totalPages) }, (_, i) => {
                    const start = Math.max(1, browsePage - 2);
                    const page = start + i;
                    if (page > browseData.books.totalPages) return null;
                    return (
                      <button
                        key={page}
                        onClick={() => setBrowsePage(page)}
                        className={`px-4 py-2 rounded-lg text-sm border transition-all ${page === browsePage
                            ? "bg-[var(--color-accent-1)] border-[var(--color-accent-1)] text-white"
                            : "bg-[var(--color-bg-card)] border-[var(--color-border)] hover:bg-white/5"
                          }`}
                      >
                        {page}
                      </button>
                    );
                  })}
                  {browsePage < browseData.books.totalPages && (
                    <button onClick={() => setBrowsePage(browsePage + 1)} className="px-4 py-2 rounded-lg bg-[var(--color-bg-card)] border border-[var(--color-border)] text-sm hover:bg-white/5 transition-all">
                      Next &rarr;
                    </button>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      ) : (
        /* Homepage Rows */
        <>
          {/* Genre Chips */}
          <div className="flex flex-wrap gap-2 mb-8 justify-center">
            {genres.slice(0, 15).map((g) => (
              <button
                key={g.genre}
                onClick={() => setSelectedGenre(g.genre)}
                className="px-4 py-1.5 rounded-full bg-[var(--color-bg-card)] border border-[var(--color-border)] text-sm text-[var(--color-text-secondary)] hover:border-[var(--color-accent-1)]/40 hover:text-[var(--color-accent-1)] transition-all"
              >
                {g.genre}
              </button>
            ))}
          </div>

          {loadingHomepage ? (
            <div className="flex justify-center py-20">
              <div className="spinner" />
            </div>
          ) : (
            <>
              <RecommendationRow title="🔥 Popular Books" subtitle="Most rated books in the collection" books={homepageData?.homepageBooks || []} onBookClick={setSelectedBookId} />
              <RecommendationRow title="📈 Trending Now" subtitle="High ratings meet high popularity" books={trendingData?.trendingBooks || []} onBookClick={setSelectedBookId} />
              <RecommendationRow title="🐉 Fantasy" subtitle="Epic worlds and magical adventures" books={fantasyData?.genreBooks || []} onBookClick={setSelectedBookId} />
              <RecommendationRow title="💕 Romance" subtitle="Love stories that captivate" books={romanceData?.genreBooks || []} onBookClick={setSelectedBookId} />
              <RecommendationRow title="🚀 Science Fiction" subtitle="Explore the future and beyond" books={scifiData?.genreBooks || []} onBookClick={setSelectedBookId} />
              <RecommendationRow title="🔍 Mystery" subtitle="Unravel the clues" books={mysteryData?.genreBooks || []} onBookClick={setSelectedBookId} />
            </>
          )}
        </>
      )}

      {/* Book Modal */}
      {selectedBookId && (
        <BookModal bookId={selectedBookId} onClose={() => setSelectedBookId(null)} />
      )}
    </div>
  );
}

export default function HomePage() {
  const { username } = useUser();
  if (!username) return <LoginScreen />;
  return <DiscoverPage />;
}
