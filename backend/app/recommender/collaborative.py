"""
Collaborative filtering using USER-BASED approach (matching notebook).

The notebook builds a sparse user-item rating matrix and finds similar
users via cosine similarity, then aggregates their ratings as a
weighted mean.  The CF weight scales dynamically based on coverage.

This replaces the old item-based CF approach.
"""

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity


CF_NEIGHBOURS = 50       # how many similar users to aggregate over
CF_MIN_NEIGHBOURS = 5    # minimum needed to trust the CF score


class CollaborativeRecommender:
    """User-based collaborative filtering using the ratings dataset.

    Matches the notebook's approach exactly:
      1. Filter to active users (>=10 ratings) and popular books (>=10 ratings)
      2. Build a sparse user-item matrix (rows=users, cols=books, values=rating)
      3. For a "query user" (defined by liked books), find K most similar
         real users via cosine similarity
      4. Aggregate neighbour ratings as weighted mean, normalised to [0,1]
      5. CF weight scales dynamically with coverage ratio (0 to 0.5)
    """

    def __init__(self, ratings_df: pd.DataFrame, book_id_to_idx: dict, n_books: int, df: pd.DataFrame = None):
        self.book_id_to_idx = book_id_to_idx
        self.idx_to_book_id = {v: k for k, v in book_id_to_idx.items()}
        self.n_books = n_books
        self.df = df

        print("  Building user-based collaborative filtering model...")

        # ── Filter to active users (>=10 ratings) ──
        user_counts = ratings_df['user_id'].value_counts()
        active_users = user_counts[user_counts >= 10].index
        filtered = ratings_df[ratings_df['user_id'].isin(active_users)]

        # ── Filter to popular books (>=10 ratings) ──
        book_counts = filtered['book_id'].value_counts()
        popular_books = book_counts[book_counts >= 10].index
        filtered = filtered[filtered['book_id'].isin(popular_books)]

        # ── Build sparse user-item matrix ──
        all_user_ids = filtered["user_id"].unique()
        all_book_ids = filtered["book_id"].unique()

        self.user_to_idx = {uid: i for i, uid in enumerate(all_user_ids)}
        self.cf_book_to_idx = {bid: i for i, bid in enumerate(all_book_ids)}
        self.cf_idx_to_book = {i: bid for bid, i in self.cf_book_to_idx.items()}

        n_users = len(all_user_ids)
        n_books_cf = len(all_book_ids)

        row_arr = filtered["user_id"].map(self.user_to_idx).values
        col_arr = filtered["book_id"].map(self.cf_book_to_idx).values
        data_arr = filtered["rating"].values.astype(np.float32)

        self.user_item_matrix = csr_matrix(
            (data_arr, (row_arr, col_arr)),
            shape=(n_users, n_books_cf)
        )

        print(f"  User-based CF model ready: {n_users:,} users × {n_books_cf:,} books, "
              f"{self.user_item_matrix.nnz:,} ratings")

    def _build_query_user_vector(self, liked_book_ids: list[int]):
        """Build a (1, n_books_cf) sparse vector for the query user."""
        col_indices, values = [], []
        for bid in liked_book_ids:
            if bid in self.cf_book_to_idx:
                col_indices.append(self.cf_book_to_idx[bid])
                values.append(5.0)
        if not col_indices:
            return None
        n_books_cf = self.user_item_matrix.shape[1]
        return csr_matrix(
            (values, ([0] * len(col_indices), col_indices)),
            shape=(1, n_books_cf)
        )

    def get_cf_scores(self, liked_book_ids: list[int], candidate_book_ids: list[int]) -> tuple[dict, float]:
        """
        Get CF scores for candidate books.

        Parameters
        ----------
        liked_book_ids    : list[int]  — book_ids the user said they like
        candidate_book_ids: list[int]  — book_ids we want CF scores for

        Returns
        -------
        dict { book_id -> float [0..1] }  — CF score (0 if not enough neighbours)
        float                             — cf_weight to apply (0.0 if CF unreliable)
        """
        query_vec = self._build_query_user_vector(liked_book_ids)
        if query_vec is None:
            return {}, 0.0

        # Cosine similarity between query user and every real user
        similarities = cosine_similarity(query_vec, self.user_item_matrix)[0]

        # Pick the top-K neighbours (exclude exact zeros — no overlap)
        top_k_idx = np.argsort(similarities)[::-1][:CF_NEIGHBOURS]
        top_k_idx = [i for i in top_k_idx if similarities[i] > 0]

        if len(top_k_idx) < CF_MIN_NEIGHBOURS:
            return {}, 0.0

        top_sims = np.array([similarities[i] for i in top_k_idx])
        neighbour_ratings = self.user_item_matrix[top_k_idx, :]

        # Weighted mean rating across neighbours for each candidate book
        cf_scores = {}
        for bid in candidate_book_ids:
            if bid not in self.cf_book_to_idx:
                cf_scores[bid] = 0.0
                continue
            col = self.cf_book_to_idx[bid]
            ratings_col = neighbour_ratings[:, col].toarray().flatten()
            rated_mask = ratings_col > 0
            if rated_mask.sum() == 0:
                cf_scores[bid] = 0.0
            else:
                w = top_sims[rated_mask]
                r = ratings_col[rated_mask]
                cf_scores[bid] = float(np.dot(w, r) / (w.sum() * 5.0 + 1e-9))

        # cf_weight proportional to coverage
        covered = sum(1 for v in cf_scores.values() if v > 0)
        coverage_ratio = covered / max(len(candidate_book_ids), 1)
        cf_weight = 0.5 * coverage_ratio

        return cf_scores, cf_weight

    # ── Legacy interface for single-book recommendation ──
    def recommend_by_book_id(self, book_id: int, n: int = 10) -> list[dict]:
        """Get collaboratively similar books (legacy interface)."""
        # Build candidate list from all books
        candidate_ids = list(self.cf_book_to_idx.keys())
        cf_scores, _ = self.get_cf_scores([book_id], candidate_ids)
        if not cf_scores:
            return []

        ranked = sorted(cf_scores.items(), key=lambda x: x[1], reverse=True)
        results = []
        for bid, score in ranked:
            if bid == book_id or score <= 0:
                continue
            if bid not in self.book_id_to_idx:
                continue
            results.append({
                "dataset_idx": self.book_id_to_idx[bid],
                "similarity": round(float(score), 4),
                "method": "Collaborative (User-Based)"
            })
            if len(results) >= n:
                break
        return results

    # ── Legacy interface for multi-book recommendation ──
    def recommend_by_favorites(self, book_ids: list[int], n: int = 10) -> list[dict]:
        """Get recommendations based on a list of favorited book IDs."""
        candidate_ids = list(self.cf_book_to_idx.keys())
        cf_scores, _ = self.get_cf_scores(book_ids, candidate_ids)
        if not cf_scores:
            return []

        exclude = set(book_ids)
        ranked = sorted(cf_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for bid, score in ranked:
            if bid in exclude or score <= 0:
                continue
            if bid not in self.book_id_to_idx:
                continue
            results.append({
                "dataset_idx": self.book_id_to_idx[bid],
                "similarity": round(float(score), 4),
                "method": "Collaborative (User-Based)"
            })
            if len(results) >= n:
                break
        return results
