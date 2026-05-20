"""
GraphQL query resolvers.
"""

import strawberry
from typing import Optional

from .types import (
    Book, PaginatedBooks, BookRecommendation, RecommendationResult,
    ProfileRecommendationResult, ProfileSummary, GenreCount, DatasetStats,
    UserProfile,
)


def make_query(app_state):
    """Create the Query type with access to app state."""

    @strawberry.type
    class Query:

        @strawberry.field
        def books(
            self,
            page: int = 1,
            per_page: int = 20,
            genre: Optional[str] = None,
            search: Optional[str] = None,
            sort_by: str = "title",
            sort_order: str = "asc",
        ) -> PaginatedBooks:
            """Get paginated books with optional filtering."""
            df = app_state["df"]
            filtered = df.copy()

            if genre:
                filtered = filtered[filtered["genres"].str.contains(genre, case=False, na=False)]
            if search:
                filtered = filtered[
                    filtered["title"].str.contains(search, case=False, na=False) |
                    filtered["authors"].str.contains(search, case=False, na=False)
                ]

            # Sort
            sort_col = sort_by if sort_by in filtered.columns else "title"
            filtered = filtered.sort_values(sort_col, ascending=(sort_order == "asc"), na_position="last")

            total = len(filtered)
            total_pages = max(1, (total + per_page - 1) // per_page)
            start = (page - 1) * per_page
            end = start + per_page
            paginated = filtered.iloc[start:end]

            books = [_row_to_book(row) for _, row in paginated.iterrows()]
            return PaginatedBooks(
                books=books, total=total, page=page,
                per_page=per_page, total_pages=total_pages
            )

        @strawberry.field
        def book(self, book_id: int) -> Optional[Book]:
            """Get a single book by book_id."""
            df = app_state["df"]
            match = df[df["book_id"] == book_id]
            if match.empty:
                return None
            return _row_to_book(match.iloc[0])

        @strawberry.field
        def recommend(self, book_id: int, n: int = 8, method: str = "hybrid") -> Optional[RecommendationResult]:
            """Get recommendations for a book."""
            df = app_state["df"]
            recommender = app_state["hybrid_recommender"]
            content_rec = app_state["content_recommender"]

            match = df[df["book_id"] == book_id]
            if match.empty:
                return None

            book_idx = match.index[0]
            dataset_idx = df.index.get_loc(book_idx)

            if method == "content":
                recs = content_rec.recommend_by_index(dataset_idx, n=n)
            else:
                recs = recommender.recommend_by_index(dataset_idx, book_id=book_id, n=n)

            rec_books = []
            for r in recs:
                idx = r["dataset_idx"]
                if idx < len(df):
                    row = df.iloc[idx]
                    rec_books.append(BookRecommendation(
                        book=_row_to_book(row),
                        similarity=r["similarity"],
                        method=r["method"]
                    ))

            return RecommendationResult(
                query_book=_row_to_book(match.iloc[0]),
                recommendations=rec_books,
                method=method.upper()
            )

        @strawberry.field
        def homepage_books(self) -> list[Book]:
            """Get featured books for the homepage (top-rated)."""
            df = app_state["df"]
            top = df.nlargest(20, "ratings_count")
            return [_row_to_book(row) for _, row in top.iterrows()]

        @strawberry.field
        def trending_books(self) -> list[Book]:
            """Get trending books (high ratings + recent)."""
            df = app_state["df"]
            scored = df.copy()
            scored["trend_score"] = scored["average_rating"] * scored["ratings_count"]
            top = scored.nlargest(20, "trend_score")
            return [_row_to_book(row) for _, row in top.iterrows()]

        @strawberry.field
        def genre_books(self, genre: str, limit: int = 20) -> list[Book]:
            """Get books by genre."""
            df = app_state["df"]
            filtered = df[df["genres"].str.contains(genre, case=False, na=False)]
            top = filtered.nlargest(limit, "average_rating")
            return [_row_to_book(row) for _, row in top.iterrows()]

        @strawberry.field
        def genres(self) -> list[GenreCount]:
            """Get all genres with counts."""
            import ast
            df = app_state["df"]
            genre_counts = {}
            for g_str in df["genres"]:
                try:
                    g_list = ast.literal_eval(g_str)
                    for g in g_list:
                        genre_counts[g] = genre_counts.get(g, 0) + 1
                except:
                    pass
            sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
            return [GenreCount(genre=g, count=c) for g, c in sorted_genres]

        @strawberry.field
        def stats(self) -> DatasetStats:
            """Get dataset statistics."""
            import ast
            df = app_state["df"]
            genre_counts = {}
            for g_str in df["genres"]:
                try:
                    g_list = ast.literal_eval(g_str)
                    for g in g_list:
                        genre_counts[g] = genre_counts.get(g, 0) + 1
                except:
                    pass
            sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)

            return DatasetStats(
                total_books=len(df),
                total_authors=df["authors"].nunique(),
                total_genres=len(genre_counts),
                avg_rating=round(float(df["average_rating"].mean()), 2),
                genre_distribution=[GenreCount(genre=g, count=c) for g, c in sorted_genres[:15]]
            )

        @strawberry.field
        def search_books(self, query: str, n: int = 20) -> list[Book]:
            """Search books by title, author, or description."""
            df = app_state["df"]
            mask = (
                df["title"].str.contains(query, case=False, na=False) |
                df["authors"].str.contains(query, case=False, na=False) |
                df["description"].str.contains(query, case=False, na=False)
            )
            results = df[mask].head(n)
            return [_row_to_book(row) for _, row in results.iterrows()]

        @strawberry.field
        def user_profile(self, username: str) -> Optional[UserProfile]:
            """Get user profile info."""
            from ..database import get_or_create_user, get_favorite_book_ids, SessionLocal
            db = SessionLocal()
            try:
                user = get_or_create_user(db, username)
                favs = get_favorite_book_ids(db, user.id)
                return UserProfile(
                    id=user.id,
                    username=user.username,
                    created_at=str(user.created_at),
                    favorites_count=len(favs)
                )
            finally:
                db.close()

        @strawberry.field
        def user_favorites(self, username: str) -> list[Book]:
            """Get a user's favorited books."""
            from ..database import get_or_create_user, get_favorite_book_ids, SessionLocal
            df = app_state["df"]
            db = SessionLocal()
            try:
                user = get_or_create_user(db, username)
                fav_ids = get_favorite_book_ids(db, user.id)
                if not fav_ids:
                    return []
                fav_books = df[df["book_id"].isin(fav_ids)]
                return [_row_to_book(row) for _, row in fav_books.iterrows()]
            finally:
                db.close()

        @strawberry.field
        def user_recommendations(self, username: str, n: int = 12, method: str = "hybrid") -> Optional[ProfileRecommendationResult]:
            """Get personalized recommendations based on user favorites."""
            import ast
            from ..database import get_or_create_user, get_favorite_book_ids, SessionLocal
            df = app_state["df"]
            recommender = app_state["hybrid_recommender"]
            content_rec = app_state["content_recommender"]

            db = SessionLocal()
            try:
                user = get_or_create_user(db, username)
                fav_ids = get_favorite_book_ids(db, user.id)
            finally:
                db.close()

            if not fav_ids:
                return None

            fav_books = df[df["book_id"].isin(fav_ids)]
            if fav_books.empty:
                return None

            # Get dataset indices
            fav_indices = [df.index.get_loc(idx) for idx in fav_books.index]

            if method == "content":
                recs = content_rec.recommend_by_multiple(fav_indices, n=n)
            else:
                recs = recommender.recommend_by_profile(fav_indices, fav_ids, n=n)

            rec_books = []
            for r in recs:
                idx = r["dataset_idx"]
                if idx < len(df):
                    row = df.iloc[idx]
                    rec_books.append(BookRecommendation(
                        book=_row_to_book(row),
                        similarity=r["similarity"],
                        method=r["method"]
                    ))

            # Profile summary
            all_genres = []
            for g_str in fav_books["genres"]:
                try:
                    all_genres.extend(ast.literal_eval(g_str))
                except:
                    pass
            from collections import Counter
            genre_counter = Counter(all_genres)
            top_genres = [g for g, _ in genre_counter.most_common(5)]

            summary = ProfileSummary(
                total_books=len(fav_books),
                top_genres=top_genres,
                avg_rating=round(float(fav_books["average_rating"].mean()), 2),
                avg_pages=int(fav_books["pages"].fillna(0).mean())
            )

            return ProfileRecommendationResult(
                selected_books=[_row_to_book(row) for _, row in fav_books.iterrows()],
                recommendations=rec_books,
                profile_summary=summary,
                method=method.upper()
            )

    return Query


def _row_to_book(row) -> Book:
    """Convert a DataFrame row to a Book GraphQL type."""
    import pandas as pd
    return Book(
        book_id=int(row["book_id"]),
        title=str(row["title"]),
        authors=str(row["authors"]),
        average_rating=round(float(row["average_rating"]), 2) if pd.notna(row["average_rating"]) else 0.0,
        genres=str(row["genres"]),
        description=str(row["description"]) if pd.notna(row.get("description")) else None,
        image_url=str(row["image_url"]) if pd.notna(row.get("image_url")) else None,
        small_image_url=str(row["small_image_url"]) if pd.notna(row.get("small_image_url")) else None,
        isbn=str(row["isbn"]) if pd.notna(row.get("isbn")) else None,
        original_publication_year=int(row["original_publication_year"]) if pd.notna(row.get("original_publication_year")) else None,
        pages=int(row["pages"]) if pd.notna(row.get("pages")) else None,
        ratings_count=int(row["ratings_count"]) if pd.notna(row.get("ratings_count")) else 0,
        language_code=str(row["language_code"]) if pd.notna(row.get("language_code")) else None,
    )
