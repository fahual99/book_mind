"""
Strawberry GraphQL type definitions.
"""

import strawberry
from typing import Optional


@strawberry.type
class Book:
    book_id: int
    title: str
    authors: str
    average_rating: float
    genres: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    small_image_url: Optional[str] = None
    isbn: Optional[str] = None
    original_publication_year: Optional[int] = None
    pages: Optional[int] = None
    ratings_count: int = 0
    language_code: Optional[str] = None
    is_favorite: bool = False


@strawberry.type
class BookRecommendation:
    book: Book
    similarity: float
    method: str


@strawberry.type
class UserProfile:
    id: int
    username: str
    created_at: str
    favorites_count: int


@strawberry.type
class ProfileSummary:
    total_books: int
    top_genres: list[str]
    avg_rating: float
    avg_pages: int


@strawberry.type
class PaginatedBooks:
    books: list[Book]
    total: int
    page: int
    per_page: int
    total_pages: int


@strawberry.type
class RecommendationResult:
    query_book: Book
    recommendations: list[BookRecommendation]
    method: str


@strawberry.type
class ProfileRecommendationResult:
    selected_books: list[Book]
    recommendations: list[BookRecommendation]
    profile_summary: ProfileSummary
    method: str


@strawberry.type
class GenreCount:
    genre: str
    count: int


@strawberry.type
class DatasetStats:
    total_books: int
    total_authors: int
    total_genres: int
    avg_rating: float
    genre_distribution: list[GenreCount]
