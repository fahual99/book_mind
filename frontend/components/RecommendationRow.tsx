"use client";

import BookCard from "./BookCard";

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

interface RecommendationRowProps {
  title: string;
  subtitle?: string;
  books: Book[];
  onBookClick?: (bookId: number) => void;
}

export default function RecommendationRow({ title, subtitle, books, onBookClick }: RecommendationRowProps) {
  if (!books || books.length === 0) return null;

  return (
    <section className="mb-10">
      <div className="flex items-end justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-[var(--color-text-primary)]">{title}</h2>
          {subtitle && (
            <p className="text-sm text-[var(--color-text-secondary)] mt-0.5">{subtitle}</p>
          )}
        </div>
      </div>
      <div className="scroll-row">
        {books.map((book) => (
          <BookCard
            key={book.bookId}
            book={book}
            onClick={() => onBookClick?.(book.bookId)}
          />
        ))}
      </div>
    </section>
  );
}
