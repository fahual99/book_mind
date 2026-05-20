import re
import pandas as pd

MAX_PER_AUTHOR = 3
MAX_PER_GENRE  = 3

class DiversityFilter:
    """
    Caps how many books from the same author / primary genre appear
    in the final top-K, and removes spin-offs of the input titles.
    Also enforces the quality filter, matching the notebook's
    apply_diversity_filter() exactly.

    Optimized for web via pre-computed O(1) dictionary lookups.
    """
    def __init__(self, books_df: pd.DataFrame, quality_book_ids: set | None = None):
        print("  Building Diversity Filter metadata cache...")
        self.book_metadata = {}

        # FIX: Store quality_book_ids so apply() can enforce it,
        # matching the notebook's `if book_id not in _quality_book_ids: continue`.
        self._quality_book_ids = quality_book_ids or set()

        # Pre-compute all lookups once at server startup
        for _, row in books_df.iterrows():
            bid = int(row["book_id"])

            # Parse authors
            raw_authors = str(row.get("authors", ""))
            cleaned_a = raw_authors.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
            authors = [x.strip() for x in cleaned_a.split(",") if x.strip()]

            # Parse genres
            raw_genres = str(row.get("genres", ""))
            cleaned_g = raw_genres.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
            genres = [x.strip() for x in cleaned_g.split(",") if x.strip()]

            self.book_metadata[bid] = {
                "title": str(row.get("title", "")).lower(),
                "authors": authors,
                "primary_genre": genres[0] if genres else "unknown"
            }

    def _is_spinoff_of_input(self, rec_title_lower: str, input_titles: list[str]) -> bool:
        for t in input_titles:
            pattern = r'\b' + re.escape(t.lower()) + r'\b'
            if re.search(pattern, rec_title_lower):
                return True
        return False

    def apply(
        self,
        sorted_results: list[tuple[int, float]],
        input_titles: list[str],
        input_book_ids: set,
        top_k: int,
    ) -> list[int]:
        """
        Filters recommendations for diversity and removes spin-offs.
        Matches notebook's apply_diversity_filter() exactly, including
        the quality gate (`if book_id not in _quality_book_ids: continue`).

        Parameters:
            sorted_results: list of tuples (book_id, score) sorted highest to lowest
            input_titles: list of raw titles the user typed/selected
            input_book_ids: set of book_ids to exclude (the inputs themselves)
            top_k: integer of how many final recommendations you want
        """
        selected_ids = []
        author_counts = {}
        genre_counts = {}

        # Pre-seed author_counts with input book authors so they are excluded
        for bid in input_book_ids:
            meta = self.book_metadata.get(bid)
            if meta:
                for a in meta["authors"]:
                    author_counts[a] = author_counts.get(a, 0) + 1

        for book_id, score in sorted_results:
            if len(selected_ids) >= top_k:
                break
            if book_id in input_book_ids:
                continue

            # FIX: Quality gate — matches notebook exactly.
            # Only skip if we actually have a quality set loaded.
            if self._quality_book_ids and book_id not in self._quality_book_ids:
                continue

            meta = self.book_metadata.get(book_id)
            if not meta:
                continue

            # Spin-off check
            if self._is_spinoff_of_input(meta["title"], input_titles):
                continue

            # Author cap
            if any(author_counts.get(a, 0) >= MAX_PER_AUTHOR for a in meta["authors"]):
                continue

            # Genre cap
            primary_genre = meta["primary_genre"]
            if genre_counts.get(primary_genre, 0) >= MAX_PER_GENRE:
                continue

            # Accept
            selected_ids.append(book_id)
            genre_counts[primary_genre] = genre_counts.get(primary_genre, 0) + 1
            for a in meta["authors"]:
                author_counts[a] = author_counts.get(a, 0) + 1

        return selected_ids