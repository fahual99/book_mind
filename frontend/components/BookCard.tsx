"use client";

import { useState } from "react";
import { useUser } from "@/app/providers";

interface BookCardProps {
  book: {
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
  };
  similarity?: number;
  method?: string;
  onClick?: () => void;
}

export default function BookCard({ book, similarity, method, onClick }: BookCardProps) {
  const [imgError, setImgError] = useState(false);
  const { toggleFavorite, isFavorite, username } = useUser();
  const isFav = isFavorite(book.bookId);

  const stars = Math.round(book.averageRating || 0);
  const imageUrl = !imgError && book.imageUrl ? book.imageUrl : null;

  // Parse genres
  let genreList: string[] = [];
  try {
    genreList = JSON.parse(book.genres.replace(/'/g, '"'));
  } catch {
    genreList = [book.genres];
  }

  return (
    <div className="book-card group" onClick={onClick}>
      {/* Image */}
      <div className="relative overflow-hidden">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={book.title}
            className="book-card-image"
            loading="lazy"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="placeholder-book">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.3">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
          </div>
        )}

        {/* Favorite Button */}
        {username && (
          <button
            className={`favorite-btn ${isFav ? "active" : ""}`}
            onClick={(e) => {
              e.stopPropagation();
              toggleFavorite(book.bookId);
            }}
            title={isFav ? "Remove from favorites" : "Add to favorites"}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill={isFav ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
          </button>
        )}

        {/* Similarity Badge */}
        {similarity !== undefined && (
          <div className="similarity-badge">
            {(similarity * 100).toFixed(0)}% match
          </div>
        )}
      </div>

      {/* Body */}
      <div className="book-card-body">
        <div className="book-card-title">{book.title}</div>
        <div className="book-card-author">
          {book.authors.replace(/[\[\]']/g, "")}
        </div>
        <div className="flex items-center justify-between mt-1">
          <div className="book-card-rating">
            {[...Array(5)].map((_, i) => (
              <span key={i} className={i < stars ? "star-filled" : "star-empty"}>
                ★
              </span>
            ))}
            <span className="text-[var(--color-text-muted)] ml-1">
              {book.averageRating?.toFixed(1)}
            </span>
          </div>
          {book.originalPublicationYear && (
            <span className="text-[0.65rem] text-[var(--color-text-muted)]">
              {book.originalPublicationYear}
            </span>
          )}
        </div>
        {genreList.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {genreList.slice(0, 2).map((g) => (
              <span key={g} className="genre-tag">
                {g}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
