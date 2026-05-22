"use client";

import { useState, useEffect } from "react";
import { useGraphQL } from "@/lib/hooks";
import { GET_RECOMMENDATIONS } from "@/graphql/queries";
import BookCard from "./BookCard";
import { useUser } from "@/app/providers";

interface BookModalProps {
  bookId: number | null;
  onClose: () => void;
}

interface RecBook {
  bookId: number;
  title: string;
  authors: string;
  averageRating: number;
  genres: string;
  imageUrl?: string | null;
  originalPublicationYear?: number | null;
  pages?: number | null;
  ratingsCount?: number;
}

interface RecResult {
  recommend: {
    queryBook: RecBook & { description?: string | null };
    recommendations: { book: RecBook; similarity: number; method: string }[];
    method: string;
  } | null;
}

export default function BookModal({ bookId, onClose }: BookModalProps) {
  const [imgError, setImgError] = useState(false);
  const { toggleFavorite, isFavorite, username } = useUser();

  const { data, loading } = useGraphQL<RecResult>(
    GET_RECOMMENDATIONS,
    { bookId, n: 8, method: "hybrid" },
    { skip: !bookId }
  );

  useEffect(() => {
    setImgError(false);
  }, [bookId]);

  if (!bookId) return null;

  const book = data?.recommend?.queryBook;
  const recommendations = data?.recommend?.recommendations || [];
  const isFav = book ? isFavorite(book.bookId) : false;

  // Parse genres
  let genreList: string[] = [];
  if (book?.genres) {
    try {
      genreList = JSON.parse(book.genres.replace(/'/g, '"'));
    } catch {
      genreList = [book.genres];
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Close */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-[var(--color-text-secondary)] hover:text-white hover:bg-white/20 transition-all z-20"
        >
          &times;
        </button>

        {loading && !book ? (
          <div className="flex items-center justify-center py-20">
            <div className="spinner" />
          </div>
        ) : book ? (
          <div className="p-6">
            {/* Header */}
            <div className="flex gap-6 mb-6">
              {/* Cover */}
              <div className="flex-shrink-0 w-36 rounded-xl overflow-hidden">
                {!imgError && book.imageUrl ? (
                  <img
                    src={book.imageUrl}
                    alt={book.title}
                    className="w-full aspect-[2/3] object-cover"
                    onError={() => setImgError(true)}
                  />
                ) : (
                  <div className="w-full aspect-[2/3] bg-[var(--color-bg-card)] rounded-xl flex items-center justify-center">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.3">
                      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                    </svg>
                  </div>
                )}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {genreList.map((g) => (
                    <span key={g} className="genre-tag">{g}</span>
                  ))}
                </div>
                <h2 className="text-2xl font-bold mb-1 leading-tight">{book.title}</h2>
                <p className="text-[var(--color-text-secondary)] mb-3">
                  by {book.authors?.replace(/[\[\]']/g, "")}
                </p>

                {/* Meta grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="glass-card p-2.5 text-center">
                    <div className="text-lg font-bold text-[var(--color-accent-4)]">{book.averageRating?.toFixed(1)}</div>
                    <div className="text-[0.65rem] text-[var(--color-text-muted)]">Rating</div>
                  </div>
                  <div className="glass-card p-2.5 text-center">
                    <div className="text-lg font-bold">{book.originalPublicationYear || "\u2014"}</div>
                    <div className="text-[0.65rem] text-[var(--color-text-muted)]">Year</div>
                  </div>
                  <div className="glass-card p-2.5 text-center">
                    <div className="text-lg font-bold">{book.pages || "\u2014"}</div>
                    <div className="text-[0.65rem] text-[var(--color-text-muted)]">Pages</div>
                  </div>
                  <div className="glass-card p-2.5 text-center">
                    <div className="text-lg font-bold">{(book.ratingsCount || 0).toLocaleString()}</div>
                    <div className="text-[0.65rem] text-[var(--color-text-muted)]">Ratings</div>
                  </div>
                </div>

                {/* Favorite button */}
                {username && (
                  <button
                    onClick={() => toggleFavorite(book.bookId)}
                    className={`mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      isFav
                        ? "bg-[var(--color-accent-3)]/20 text-[var(--color-accent-3)] border border-[var(--color-accent-3)]/30"
                        : "bg-[var(--color-accent-1)]/15 text-[var(--color-accent-1)] border border-[var(--color-accent-1)]/30 hover:bg-[var(--color-accent-1)]/25"
                    }`}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill={isFav ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2">
                      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                    </svg>
                    {isFav ? "Remove from Favorites" : "Add to Favorites"}
                  </button>
                )}
              </div>
            </div>

            {/* Description */}
            {book.description && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] mb-2">Description</h3>
                <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed line-clamp-4">{book.description}</p>
              </div>
            )}

            {/* Similar Books */}
            {recommendations.length > 0 && (
              <div>
                <h3 className="flex items-center gap-2 text-base font-bold mb-4">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                  </svg>
                  Similar Books
                  <span className="text-xs font-normal text-[var(--color-text-muted)] ml-1">({data?.recommend?.method})</span>
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {recommendations.slice(0, 8).map((rec) => (
                    <BookCard key={rec.book.bookId} book={rec.book} similarity={rec.similarity} />
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}
