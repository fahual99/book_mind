import os
import numpy as np
import faiss
from sklearn.metrics.pairwise import cosine_similarity

_INDEX_FILENAME = "faiss.index"

DENSE_W = 0.40
TFIDF_W = 0.40
NUMERIC_W = 0.20
FAISS_TOPK = 40


class ContentBasedRecommender:
    def __init__(
        self,
        embeddings: np.ndarray,
        tfidf_matrix=None,
        numerical_matrix: np.ndarray | None = None,
        df=None,
        models_dir: str | None = None,
        use_cache: bool = False,
    ):
        self.tfidf_matrix = tfidf_matrix
        self.numerical_matrix = numerical_matrix
        self.df = df

        # ─────────────────────────────────────────────
        # Precompute book_id -> dataframe row mapping
        # ─────────────────────────────────────────────
        if self.df is not None:
            self.bid_to_row = {
                int(bid): i
                for i, bid in enumerate(self.df["book_id"].values)
            }
        else:
            self.bid_to_row = {}

        # ─────────────────────────────────────────────
        # Paths
        # ─────────────────────────────────────────────
        index_path = (
            os.path.join(models_dir, _INDEX_FILENAME)
            if models_dir else None
        )

        # ─────────────────────────────────────────────
        # Normalize embeddings passed from main.py
        # ─────────────────────────────────────────────
        norms = np.linalg.norm(
            embeddings,
            axis=1,
            keepdims=True
        )

        norms = np.where(norms == 0, 1, norms)

        self.embeddings = (
            embeddings / norms
        ).astype(np.float32)

        self.n_books = self.embeddings.shape[0]

        # ─────────────────────────────────────────────
        # Load cached FAISS index (optional)
        # ─────────────────────────────────────────────
        if (
            use_cache and
            index_path and
            os.path.exists(index_path)
        ):
            self.faiss_index = faiss.read_index(index_path)

            print(
                f"    -> Loaded cached FAISS index: "
                f"{self.faiss_index.ntotal} vectors"
            )

        else:
            # ─────────────────────────────────────────
            # Build new FAISS index from embeddings
            # ─────────────────────────────────────────
            dim = self.embeddings.shape[1]

            self.faiss_index = faiss.IndexFlatIP(dim)

            self.faiss_index.add(self.embeddings)

            print(
                f"    -> Built FAISS index: "
                f"{self.faiss_index.ntotal} vectors"
            )

            # ─────────────────────────────────────────
            # Optional cache save
            # ─────────────────────────────────────────
            if use_cache and index_path:
                faiss.write_index(
                    self.faiss_index,
                    index_path
                )

    def get_content_scores(
        self,
        input_indices: list[int],
        exclude_book_ids: set
    ) -> dict:
        """
        Compute content scores using:
            Dense embeddings 40%
            TF-IDF            40%
            Numerical         20%
        """

        # ─────────────────────────────────────────────
        # Dense mean query vector
        # ─────────────────────────────────────────────
        mean_dense = (
            self.embeddings[input_indices]
            .mean(axis=0, keepdims=True)
            .astype(np.float32)
        )

        faiss.normalize_L2(mean_dense)

        # ─────────────────────────────────────────────
        # TF-IDF mean vector
        # ─────────────────────────────────────────────
        if self.tfidf_matrix is not None:
            mean_tfidf = np.asarray(
                self.tfidf_matrix[input_indices]
                .mean(axis=0)
            )

        # ─────────────────────────────────────────────
        # Numerical mean vector
        # ─────────────────────────────────────────────
        if self.numerical_matrix is not None:
            mean_numeric = (
                self.numerical_matrix[input_indices]
                .mean(axis=0, keepdims=True)
            )

        # ─────────────────────────────────────────────
        # Dense similarity search via FAISS
        # ─────────────────────────────────────────────
        search_k = FAISS_TOPK + len(input_indices)

        sims_dense_vals, sims_dense_idx = (
            self.faiss_index.search(
                mean_dense,
                search_k
            )
        )

        dense_scores = {}

        for sim, row_idx in zip(
            sims_dense_vals[0],
            sims_dense_idx[0]
        ):
            row_idx = int(row_idx)

            if row_idx < 0 or row_idx >= self.n_books:
                continue

            bid = int(
                self.df["book_id"].values[row_idx]
            )

            if bid not in exclude_book_ids:
                dense_scores[bid] = float(sim)

        candidate_ids = list(dense_scores.keys())

        if not candidate_ids:
            return {}

        # ─────────────────────────────────────────────
        # TF-IDF + Numerical Similarities
        # ─────────────────────────────────────────────
        if (
            self.tfidf_matrix is not None and
            self.numerical_matrix is not None
        ):
            cand_rows = [
                self.bid_to_row[bid]
                for bid in candidate_ids
            ]

            # TF-IDF cosine similarity
            cand_tfidf = self.tfidf_matrix[cand_rows]

            tfidf_sims = cosine_similarity(
                mean_tfidf,
                cand_tfidf
            )[0]

            # Numerical cosine similarity
            cand_numeric = self.numerical_matrix[cand_rows]

            numeric_sims = cosine_similarity(
                mean_numeric,
                cand_numeric
            )[0]

            # ─────────────────────────────────────────
            # Weighted blend
            # ─────────────────────────────────────────
            combined = {}

            for i, bid in enumerate(candidate_ids):
                d = dense_scores.get(bid, 0.0)
                t = float(tfidf_sims[i])
                n = float(numeric_sims[i])

                combined[bid] = (
                    DENSE_W * d +
                    TFIDF_W * t +
                    NUMERIC_W * n
                )

            return combined

        # Dense-only fallback
        return dense_scores