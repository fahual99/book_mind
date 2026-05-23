"use client";

import { useState } from "react";
import { useGraphQL } from "@/lib/hooks";
import { GET_USER_FAVORITES, GET_USER_RECOMMENDATIONS } from "@/graphql/queries";
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

interface RecBook {
  book: Book;
  similarity: number;
  method: string;
}

export default function FavoritesPage() {
  const { username, favoriteIds } = useUser();
  const [selectedBookId, setSelectedBookId] = useState<number | null>(null);
  const [showRecs, setShowRecs] = useState(false);

  const { data: favData, loading: loadingFavs } = useGraphQL<{ userFavorites: Book[] }>(
    GET_USER_FAVORITES,
    { username: username || "" },
    { skip: !username }
  );

  const { data: recsData, loading: loadingRecs } = useGraphQL<{
    userRecommendations: {
      recommendations: RecBook[];
      profileSummary: { totalBooks: number; avgRating: number; avgPages: number; topGenres: string[] };
      method: string;
    } | null;
  }>(
    GET_USER_RECOMMENDATIONS,
    { username: username || "", n: 12, method: "hybrid" },
    { skip: !username || !showRecs }
  );

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

  const favorites = (favData?.userFavorites || []).filter((book) => favoriteIds.includes(book.bookId));
  const recommendations = recsData?.userRecommendations;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="text-center mb-10">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-[var(--color-accent-3)] to-[var(--color-accent-2)] flex items-center justify-center">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </svg>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold mb-2">
          Your <span className="gradient-text">Favorites</span>
        </h1>
        <p className="text-[var(--color-text-secondary)]">Books you love, your AI recommendations are built from these</p>
      </div>

      {loadingFavs ? (
        <div className="flex justify-center py-20"><div className="spinner" /></div>
      ) : favorites.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-white/5 flex items-center justify-center">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.3">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold mb-2">No favorites yet</h3>
          <p className="text-[var(--color-text-secondary)] mb-6">Browse books and click the heart icon to add them to your favorites.</p>
          <Link href="/" className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-[var(--color-accent-1)] to-[var(--color-accent-2)] text-white font-semibold text-sm no-underline hover:opacity-90 transition-all">
            Discover Books
          </Link>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-10">
            {favorites.map((book) => (
              <BookCard key={book.bookId} book={book} onClick={() => setSelectedBookId(book.bookId)} />
            ))}
          </div>

          {!showRecs && (
            <div className="text-center mb-10">
              <button
                onClick={() => setShowRecs(true)}
                className="inline-flex items-center gap-3 px-8 py-4 rounded-2xl bg-gradient-to-r from-[var(--color-accent-1)] to-[var(--color-accent-3)] text-white font-bold text-base hover:opacity-90 transition-all pulse-glow"
              >
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                </svg>
                Get AI Recommendations
              </button>
            </div>
          )}

          {showRecs && (
            <div className="mt-10">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold"><span className="gradient-text">Recommended For You</span></h2>
                <p className="text-sm text-[var(--color-text-secondary)] mt-1">Based on your {favoriteIds.length} favorite{favoriteIds.length !== 1 ? "s" : ""}</p>
              </div>

              {recommendations?.profileSummary && (
                <div className="glass-card p-6 mb-6 max-w-2xl mx-auto">
                  <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] mb-3">Profile Insights</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-xl font-bold gradient-text">{recommendations.profileSummary.totalBooks}</div>
                      <div className="text-xs text-[var(--color-text-muted)]">Books</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-bold gradient-text">{recommendations.profileSummary.avgRating}</div>
                      <div className="text-xs text-[var(--color-text-muted)]">Avg Rating</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-bold gradient-text">{recommendations.profileSummary.avgPages}</div>
                      <div className="text-xs text-[var(--color-text-muted)]">Avg Pages</div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm font-bold gradient-text">{recommendations.profileSummary.topGenres?.[0] || "\u2014"}</div>
                      <div className="text-xs text-[var(--color-text-muted)]">Top Genre</div>
                    </div>
                  </div>
                </div>
              )}

              {loadingRecs ? (
                <div className="flex flex-col items-center py-10">
                  <div className="spinner mb-3" />
                  <p className="text-sm text-[var(--color-text-secondary)]">AI is analyzing your taste...</p>
                </div>
              ) : recommendations?.recommendations ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  {recommendations.recommendations.map((rec) => (
                    <BookCard key={rec.book.bookId} book={rec.book} similarity={rec.similarity} onClick={() => setSelectedBookId(rec.book.bookId)} />
                  ))}
                </div>
              ) : (
                <p className="text-center text-[var(--color-text-secondary)]">No recommendations available yet.</p>
              )}
            </div>
          )}
        </>
      )}

      {selectedBookId && <BookModal bookId={selectedBookId} onClose={() => setSelectedBookId(null)} />}
    </div>
  );
}
