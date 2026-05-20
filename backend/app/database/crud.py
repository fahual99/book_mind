"""
CRUD operations for Users and Favorites.
"""

from sqlalchemy.orm import Session
from .models import User, Favorite


# ── Users ──────────────────────────────────────────────────────────

def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, username: str) -> User:
    user = User(username=username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_user(db: Session, username: str) -> User:
    user = get_user_by_username(db, username)
    if not user:
        user = create_user(db, username)
    return user


# ── Favorites ──────────────────────────────────────────────────────

def get_favorites(db: Session, user_id: int) -> list[Favorite]:
    return db.query(Favorite).filter(Favorite.user_id == user_id).all()


def get_favorite_book_ids(db: Session, user_id: int) -> list[int]:
    favs = db.query(Favorite.book_id).filter(Favorite.user_id == user_id).all()
    return [f[0] for f in favs]


def add_favorite(db: Session, user_id: int, book_id: int) -> bool:
    existing = db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.book_id == book_id
    ).first()
    if existing:
        return False
    fav = Favorite(user_id=user_id, book_id=book_id)
    db.add(fav)
    db.commit()
    return True


def remove_favorite(db: Session, user_id: int, book_id: int) -> bool:
    fav = db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.book_id == book_id
    ).first()
    if not fav:
        return False
    db.delete(fav)
    db.commit()
    return True


def is_favorite(db: Session, user_id: int, book_id: int) -> bool:
    return db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.book_id == book_id
    ).first() is not None
