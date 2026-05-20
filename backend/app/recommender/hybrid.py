import re
import numpy as np
import pandas as pd

from .content_based import ContentBasedRecommender
from .collaborative import CollaborativeRecommender
from .diversity import DiversityFilter

# ─────────────────────────────────────────────────────────────────
# Quality filter thresholds (matching notebook exactly)
# ─────────────────────────────────────────────────────────────────
QUALITY_MIN_RATING        = 3.8
QUALITY_MIN_RATINGS_COUNT = 500
QUALITY_MIN_PAGES         = 100

def _passes_quality_filter(book_row) -> bool:
    """Return True if the book meets minimum quality thresholds."""
    if book_row["average_rating"] < QUALITY_MIN_RATING:
        return False
    if book_row["ratings_count"] < QUALITY_MIN_RATINGS_COUNT:
        return False
    if pd.notna(book_row.get("pages")) and book_row["pages"] < QUALITY_MIN_PAGES:
        return False
    title_authors = str(book_row["title"]) + str(book_row["authors"])
    if re.search(r'summary|bookrags', title_authors, re.IGNORECASE):
        return False
    if re.search(r'#([2-9]|[1-9]\d+)', str(book_row["title"])):
        return False
    return True

def _clean_title_for_spinoff_check(title: str) -> str:
    """
    Strip series tags like '(The Hunger Games, #1)' from a dataset title
    so the spin-off regex matches the same way the notebook does when the
    user types a short search string like 'The hunger games'.
    """
    # Remove anything in parentheses at the end: "(The Hunger Games, #1)"
    cleaned = re.sub(r'\s*\([^)]*\)\s*$', '', title).strip()
    return cleaned


class HybridRecommender:
    """
    Hybrid recommender matching the notebook's recommend() function exactly.
    Integrated with the optimized DiversityFilter for fast web performance.
    """
    def __init__(
        self,
        content_recommender: ContentBasedRecommender,
        collaborative_recommender: CollaborativeRecommender | None = None,
        diversity_filter: DiversityFilter | None = None,
        df: pd.DataFrame = None,
    ):
        self.content = content_recommender
        self.collab  = collaborative_recommender
        self.diversity_filter = diversity_filter
        self.df      = df

        # ── Pre-compute the row mapping ONCE at startup ──
        if df is not None:
            self.bid_to_row_idx = {int(bid): i for i, bid in enumerate(df["book_id"].values)}
        else:
            self.bid_to_row_idx = {}

        # ── Pre-compute quality mask ONCE at startup ──
        self._quality_book_ids: set = set()
        if df is not None:
            quality_mask = df.apply(_passes_quality_filter, axis=1)
            self._quality_book_ids = set(df.loc[quality_mask, "book_id"])
            print(f"    -> Quality filter: {len(self._quality_book_ids):,} / {len(df):,} books pass")

    def recommend_by_index(self, book_idx: int, book_id: int | None = None, n: int = 10) -> list[dict]:
        """Hybrid recommendation for a single book."""
        if self.df is None:
            return self._fallback_content_only(book_idx, n)

        exclude_ids = {book_id} if book_id is not None else set()
        # FIX: Strip series tags so spin-off check matches the way the notebook
        # does when the user types a short title like "The hunger games".
        # Dataset title "The Hunger Games (The Hunger Games, #1)" → "The Hunger Games"
        input_titles = [_clean_title_for_spinoff_check(str(self.df.iloc[book_idx]["title"]))]

        content_scores = self.content.get_content_scores([book_idx], exclude_ids)
        if not content_scores:
            return []

        # FIX: Quality filter AFTER getting content scores, matching notebook Step 2→3 order.
        # candidate_ids is the quality-filtered subset used for CF and final blending,
        # but content_scores (the full FAISS pool) is normalized BEFORE this filtering.
        candidate_ids = [bid for bid in content_scores if bid in self._quality_book_ids]
        if not candidate_ids:
            candidate_ids = list(content_scores.keys())

        cf_scores, cf_weight = {}, 0.0
        liked_ids = [book_id] if book_id is not None else []
        if self.collab and liked_ids:
            cf_scores, cf_weight = self.collab.get_cf_scores(liked_ids, candidate_ids)
        content_weight = 1.0 - cf_weight

        results = self._blend_scores(content_scores, cf_scores, candidate_ids, content_weight, cf_weight)
        return self._apply_filters(results, input_titles, exclude_ids, n)

    def recommend_by_profile(self, book_indices: list[int], book_ids: list[int], n: int = 10) -> list[dict]:
        """Hybrid recommendation for a user profile (multiple books)."""
        if self.df is None:
            return self._fallback_content_only_multi(book_indices, n)

        exclude_ids  = set(book_ids)
        # FIX: Strip series tags so spin-off check works correctly.
        input_titles = [_clean_title_for_spinoff_check(str(self.df.iloc[i]["title"])) for i in book_indices]

        content_scores = self.content.get_content_scores(book_indices, exclude_ids)
        if not content_scores:
            return []

        # FIX: Quality filter AFTER content scores, same as notebook recommend() Step 2→3.
        candidate_ids = [bid for bid in content_scores if bid in self._quality_book_ids]
        if not candidate_ids:
            candidate_ids = list(content_scores.keys())

        cf_scores, cf_weight = {}, 0.0
        if self.collab:
            cf_scores, cf_weight = self.collab.get_cf_scores(book_ids, candidate_ids)
        content_weight = 1.0 - cf_weight

        results = self._blend_scores(content_scores, cf_scores, candidate_ids, content_weight, cf_weight)
        return self._apply_filters(results, input_titles, exclude_ids, n)

    def _blend_scores(
        self,
        content_scores: dict,
        cf_scores: dict,
        candidate_ids: list[int],
        content_weight: float,
        cf_weight: float,
    ) -> list[tuple]:
        """
        Blend content and CF scores using the notebook's exact formula.

        CRITICAL: min/max normalization uses ALL content_scores keys (the full
        FAISS pool), NOT just candidate_ids. This matches notebook Step 4 exactly.
        The notebook normalizes first, then loops over candidate_ids for blending.
        """
        # FIX: Normalize over the full FAISS pool (all content_scores),
        # not just the quality-filtered candidate_ids subset.
        if content_scores:
            max_c = max(content_scores.values())
            min_c = min(content_scores.values())
        else:
            max_c, min_c = 1.0, 0.0
        range_c = max_c - min_c + 1e-9

        results = []
        for bid in candidate_ids:
            c = (content_scores.get(bid, 0.0) - min_c) / range_c  # normalised [0,1]
            f = cf_scores.get(bid, 0.0)                            # already [0,1]
            score = content_weight * c + cf_weight * f
            results.append((bid, score, c, f))

        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def _apply_filters(
        self,
        sorted_results: list[tuple],
        input_titles: list[str],
        input_book_ids: set,
        top_k: int,
    ) -> list[dict]:
        """
        Delegates to the optimized DiversityFilter class.
        Note: quality filtering is already enforced via candidate_ids upstream,
        and DiversityFilter.apply() also checks _quality_book_ids for safety.
        """
        if not self.diversity_filter or self.df is None:
            return self._results_to_dicts(sorted_results[:top_k])

        # Convert to the format DiversityFilter expects: [(bid, score), ...]
        diversity_input = [(bid, score) for bid, score, _, _ in sorted_results]

        print("\n--- RAW SCORES BEFORE DIVERSITY FILTER (top 20) ---")
        for bid, score in diversity_input[:20]:
            row_idx = self.bid_to_row_idx.get(bid, -1)
            if row_idx >= 0 and self.df is not None:
                title = self.df.iloc[row_idx]["title"]
                print(f"  {score:.4f}  {title}")

        # Apply high-performance O(1) filter
        final_ids = self.diversity_filter.apply(
            sorted_results=diversity_input,
            input_titles=input_titles,
            input_book_ids=input_book_ids,
            top_k=top_k,
        )

        if not final_ids:
            return self._results_to_dicts(sorted_results[:top_k])

        # Map the accepted IDs back to full dictionary outputs
        score_lookup = {bid: (score, c, f) for bid, score, c, f in sorted_results}

        out = []
        for bid in final_ids:
            score, c, f = score_lookup[bid]
            row_idx = self.bid_to_row_idx.get(bid, -1)

            method_parts = ["Content"]
            if f > 0:
                method_parts.append("CF")

            out.append({
                "dataset_idx":   row_idx,
                "similarity":    round(score, 4),
                "content_score": round(c, 4),
                "cf_score":      round(f, 4),
                "method":        f"Hybrid ({'+'.join(method_parts)})",
            })
        return out

    def _results_to_dicts(self, results: list[tuple]) -> list[dict]:
        """Fallback formatter if diversity filter is missing."""
        out = []
        for bid, score, c, f in results:
            idx = self.bid_to_row_idx.get(bid, -1)
            method_parts = ["Content"]
            if f > 0:
                method_parts.append("CF")
            out.append({
                "dataset_idx":   idx,
                "similarity":    round(score, 4),
                "content_score": round(c, 4),
                "cf_score":      round(f, 4),
                "method":        f"Hybrid ({'+'.join(method_parts)})",
            })
        return out

    def _fallback_content_only(self, book_idx: int, n: int) -> list[dict]:
        recs = self.content.recommend_by_index(book_idx, n=n)
        for r in recs:
            r["content_score"] = r["similarity"]
            r["cf_score"] = 0.0
        return recs

    def _fallback_content_only_multi(self, book_indices: list[int], n: int) -> list[dict]:
        recs = self.content.recommend_by_multiple(book_indices, n=n)
        for r in recs:
            r["content_score"] = r["similarity"]
            r["cf_score"] = 0.0
        return recs