"""
GraphQL mutation resolvers.
"""

import strawberry
from .types import UserProfile


def make_mutation(app_state):
    """Create the Mutation type with access to app state."""

    @strawberry.type
    class Mutation:

        @strawberry.mutation
        def demo_login(self, username: str) -> UserProfile:
            """Login or create a demo user. No authentication required."""
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

        @strawberry.mutation
        def add_favorite(self, username: str, book_id: int) -> bool:
            """Add a book to user's favorites."""
            from ..database import get_or_create_user, add_favorite as db_add_fav, SessionLocal
            db = SessionLocal()
            try:
                user = get_or_create_user(db, username)
                return db_add_fav(db, user.id, book_id)
            finally:
                db.close()

        @strawberry.mutation
        def remove_favorite(self, username: str, book_id: int) -> bool:
            """Remove a book from user's favorites."""
            from ..database import get_or_create_user, remove_favorite as db_rem_fav, SessionLocal
            db = SessionLocal()
            try:
                user = get_or_create_user(db, username)
                return db_rem_fav(db, user.id, book_id)
            finally:
                db.close()

        @strawberry.mutation
        def toggle_favorite(self, username: str, book_id: int) -> bool:
            """Toggle a book's favorite status. Returns True if now favorited."""
            from ..database import (
                get_or_create_user, is_favorite as db_is_fav,
                add_favorite as db_add_fav, remove_favorite as db_rem_fav,
                SessionLocal
            )
            db = SessionLocal()
            try:
                user = get_or_create_user(db, username)
                if db_is_fav(db, user.id, book_id):
                    db_rem_fav(db, user.id, book_id)
                    return False
                else:
                    db_add_fav(db, user.id, book_id)
                    return True
            finally:
                db.close()

    return Mutation
