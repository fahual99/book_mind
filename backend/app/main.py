"""
=============================================================================
  Book Recommendation System - FastAPI Backend
  Hybrid Recommendation Engine with GraphQL API
=============================================================================

Main application entry point. Loads ML assets, initializes the recommendation
engine, sets up SQLite database, and serves the Strawberry GraphQL API.

Data cleaning, feature engineering, TF-IDF, and numerical matrix construction
replicate the notebook pipeline EXACTLY so that content scores match.

Key fixes vs previous version
──────────────────────────────
1. Full notebook cleaning pipeline applied at startup:
     - clean_text() (strip non-ASCII)
     - Drop boxed sets / collections / omnibus / vol. / volume titles
     - Coerce numeric columns, drop rows with nulls in essential columns
     - Drop pages < 100, summary titles, bookrags authors
     - reset_index(drop=True)
     - remove_noise() → clean_description column
     - deduplicate_descriptions() (drop empty + mismatched descriptions)
   This reproduces the notebook's 8,767-book dataset so that the saved
   embeddings.npy (which was encoded from that cleaned dataset) aligns
   with df row-for-row.

2. features column uses raw description[:300], NOT clean_description,
   matching the notebook's Cell 20 exactly.

3. _blend_scores() normalizes content scores over ALL content_scores keys
   (the full FAISS candidate pool), not just the quality-filtered subset.
   This matches the notebook's recommend() Step 4 exactly.
"""

import os
import re
import sys
import warnings
import numpy as np
import pandas as pd
import joblib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR   = os.path.dirname(BASE_DIR)
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATASET_DIR = os.path.join(BASE_DIR, "dataset")

# ── App Setup ─────────────────────────────────────────────────────
app = FastAPI(
    title="Book Recommendation API",
    description="Hybrid book recommendation system with FAISS, TF-IDF, and GraphQL",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://book-mind-five.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("=" * 60)
print("  BOOK RECOMMENDATION SYSTEM - FastAPI Backend")
print("  Loading data and ML assets...")
print("=" * 60)

# ══════════════════════════════════════════════════════════════════
#  STEP 1 — Load raw dataset (same columns as notebook Cell 1)
# ══════════════════════════════════════════════════════════════════

BOOKS_PATH   = os.path.join(DATASET_DIR, "books_enriched.csv")
RATINGS_PATH = os.path.join(DATASET_DIR, "ratings.csv")

def clean_text(text):
    if isinstance(text, str):
        # Encode to ascii, ignoring errors (removes non-ascii), then decode back to string
        return text.encode('ascii', 'ignore').decode('ascii')
    return text

books = pd.read_csv(BOOKS_PATH, encoding="utf-8")

# Keep only the columns the notebook uses (Cell 2)
books = books[[
    "book_id", "title", "authors", "description", "genres",
    "ratings_1", "ratings_2", "ratings_3", "ratings_4", "ratings_5",
    "average_rating", "ratings_count", "pages",
    "original_publication_year", "image_url",
]]

# Fill string columns (Cell 3)
books["description"] = books["description"].fillna("")
books["genres"]      = books["genres"].fillna("")
books["authors"]     = books["authors"].fillna("")

print(f"  Raw dataset loaded: {len(books):,} books")

# ══════════════════════════════════════════════════════════════════
#  STEP 2 — Cleaning pipeline (notebook Cell 4, exact match)
# ══════════════════════════════════════════════════════════════════


# 1. Apply clean_text function to relevant string columns
for col in ['title', 'authors', 'description', 'genres']:
    books[col] = books[col].apply(clean_text)

books = books[~books['title'].str.contains('boxed set|collection|omnibus|vol\.|volume', case=False, na=False)]

# 2. Convert numerical columns to appropriate types and handle errors/missing values
# average_rating
books['average_rating'] = pd.to_numeric(books['average_rating'], errors='coerce')
# ratings_count
books['ratings_count'] = pd.to_numeric(books['ratings_count'], errors='coerce').astype('Int64') # Use Int64 for nullable integer
# pages
books['pages'] = pd.to_numeric(books['pages'], errors='coerce').astype('Int64') # Use Int64 for nullable integer
# original_publication_year
books['original_publication_year'] = pd.to_numeric(books['original_publication_year'], errors='coerce').astype('Int64')

# 3. Drop rows with missing values in essential columns after type conversion
# Define essential columns that cannot be null
essential_columns = ['book_id', 'title', 'authors', 'average_rating', 'ratings_count', 'pages', 'original_publication_year']
books.dropna(subset=essential_columns, inplace=True)

# 4. Re-apply pruning filters (from previous requests)
initial_pruning_count = len(books)
books = books[~books['title'].str.contains('summary', case=False, na=False)]
books = books[~books['authors'].str.contains('bookrags', case=False, na=False)]
books = books[books['pages'] >= 100] # Ensure pages are also numeric and >= 100

print(f"Number of books after cleaning and pruning: {len(books)}")

# Reset index after dropping rows to ensure a continuous index
books.reset_index(drop=True, inplace=True)


print(f"Number of books after cleaning and pruning: {len(books)}")

# ══════════════════════════════════════════════════════════════════
#  STEP 3 — remove_noise() on descriptions (notebook Cell 5-6)
# ══════════════════════════════════════════════════════════════════
def remove_noise(text, max_words=300):
    if pd.isna(text):
        return ""

    text = str(text)

    # =========================================================
    # CLEANING PATTERNS
    # =========================================================

    patterns = [

        # -------------------------------------------------
        # Alternate cover junk (expanded)
        # -------------------------------------------------
        r"(?:this\s+is\s+)?an?\s*alternate\s*cover\s*edition(?:\s*of)?(?:\s*(?:this\s+)?isbn)?.*?(?=\.|$|\n)",
        r"alternative\s*cover\s*edition.*?(?=\.|$)",
        r"alternate\s*cover.*?(?=\.|$)",
        r"also\s*see\s*:\s*alternate\s*cover\s*editions?.*?(?=\.|$)",
        r"you\s*can\s*find\s*an?\s*alternative?\s*cover.*?(?=\.|$)",
        r"for\s+(?:the\s+)?1st\s+printing\s+edition\s+of\s+this\s+isbn.*?(?=\.|$)",
        r"see\s+here\.?",
        r"earlier\s+cover\s+edition.*?(?=\.|$)",
        r"alternate\s+cover\s+for\s+/?\s*\d+",

        # -------------------------------------------------
        # ISBN / ASIN (expanded)
        # -------------------------------------------------
        r"\(?isbn[- ]?(?:10|13)?[:\s]?[\dXx\-]{5,}\)?",
        r"isbn13?\s*here",
        r"\b(?:asin|b0)[A-Z0-9]{8,}\b",
        r"/\s*978[\d\-]{10,}",

        # -------------------------------------------------
        # Bestseller marketing phrases (UPDATED)
        # -------------------------------------------------
        r"(?:#?\s*1\s+)?(?:new\s+york\s+times|nyt|national|international|usa\s+today|wall\s+street\s+journal|indie|world-?wide|global)\s+best\s*sellers?",
        r"(?:the\s+)?(?:instant|phenomenal|blockbuster|runaway)?\s*(?:#?\s*1\s+)?(?:new\s+york\s+times|nyt)\s+best\s*selling\s+(?:series|author|novel|book|debut)?",
        r"(?:#?\s*1\s+)?best\s*sellers?",
        r"instant\s+best\s*sellers?",
        r"best\s*selling\s+(?:series|author|novel|book|debut)",

        # -------------------------------------------------
        # Motion picture / TV / adaptation promos (UPDATED)
        # -------------------------------------------------
        r"[^.!?]*\bmajor\s+motion\s+picture[^.!?]*(?:[.!?]|$)",
        r"(?:the\s+)?(?:basis|inspiration|story|author)\s+(?:for|that|featured\s+in|behind)[^.!?]*(?:movie|film|tv\s+series|netflix)[^.!?]*(?:[.!?]|$)",
        r"(?:now|soon|currently)\s+(?:to\s+be\s+)?(?:a|in|an)[^.!?]*(?:movie|film|tv\s+series|netflix)[^.!?]*(?:[.!?]|$)",
        r"read\s+it\s+before\s+it\s+hits\s+(?:theaters?|cinemas?)[^.!?]*(?:[.!?]|$)",
        r"in\s+theaters?\s+\w+\s+\d{4}[^.!?]*(?:[.!?]|$)",

        # -------------------------------------------------
        # Edition / Cover fluff (UPDATED)
        # -------------------------------------------------
        r"[^.!?]*\brevised\s+and\s+expanded\s+edition\b[^.!?]*(?:[.!?]|$)",
        r"[^.!?]*\bincludes\s+\d+\s+new\s+pages\b[^.!?]*(?:[.!?]|$)",

        # -------------------------------------------------
        # Award / accolade boilerplate
        # -------------------------------------------------
        r"winner\s+of\s+(?:the\s+)?[^.]{0,60}(?:award|prize)[^.]*\.",
        r"(?:national\s+book\s+award|pulitzer\s+prize|booker\s+prize|hugo\s+award|nebula\s+award|edgar\s+award|newbery)[^.]*(?:winner|finalist|nominee)[^.]*\.",
        r"(?:finalist|nominee|winner)\s+for\s+(?:the\s+)?[^.]{0,60}(?:award|prize)[^.]*\.",
        r"named\s+(?:one\s+of\s+)?(?:the\s+)?best\s+(?:books?|novels?)[^.]*(?:by|of)[^.]*\.",
        r"named\s+to\s+numerous\s+state\s+reading\s+lists[^.]*\.",

        # -------------------------------------------------
        # Librarian / publisher / series notes
        # -------------------------------------------------
        r"librarian'?s?\s*note\s*:.*?(?=\.|$)",
        r"publisher'?s?\s*note\s*:.*?(?=\.|$)",
        r"also\s+see\s*:.*?(?=\.|$)",
        r"page\s+numbers?\s+source\s+isbn.*?(?=\.|$)",
        r"note\s*:\s*all\s+information\s+herein[^.]*\.",
        r"\*+[^*]+\*+",

        # -------------------------------------------------
        # Back cover / edition notes
        # -------------------------------------------------
        r"\(back\s+cover\)",
        r"\(front\s+flap\)",
        r"--this\s+text\s+refers\s+to[^.]*\.",

        # -------------------------------------------------
        # Goodreads URLs / metadata
        # -------------------------------------------------
        r"https?:\/\/\S+",
        r"www\.\S+",
        r"goodreads\.\S+",

        # -------------------------------------------------
        # Critic quotes / blurbs
        # Two patterns: double-quote and em-dash styles
        # e.g. "Hilariously funny" -- USA Today
        # e.g. Brilliant. —The New York Times
        # -------------------------------------------------
        r'"[^"]{0,120}"\s*[-—–]+\s*[A-Z][^\n"]{0,80}',
        r'[-—–]{1,2}\s*(?:the\s+)?[A-Z][a-zA-Z\s]{3,40}(?:times|post|review|journal|tribune|herald|magazine|press|weekly|daily|observer|guardian|globe|chronicle|digest)\b[^\n.]{0,60}',

        # -------------------------------------------------
        # Praise / blurb section headers
        # -------------------------------------------------
        r"praise\s+for\s+[^:]{0,60}:.*?(?=\n|\Z)",

        # -------------------------------------------------
        # Malformed leftovers
        # -------------------------------------------------
        r"\.\.+",
        r"\[\s*ACE\s*\]",
        r"ACE\s*#\d+",
        r"~\s*$",
    ]

    for pattern in patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE | re.DOTALL)

    # =========================================================
    # FIX SPACING
    # =========================================================

    # FIX: Only split on clear word boundaries, not Mc/Mac/O' names
    # lowerCaseUpperCase -> lowerCase UpperCase
    # but skip Mc/Mac prefixes and O' contractions
    text = re.sub(
        r"(?<![Mm][ac]|O')([a-z])([A-Z])",
        r"\1 \2",
        text
    )

    # punctuation spacing
    text = re.sub(r"([.!?])([A-Za-z])", r"\1 \2", text)

    # remove spaces before punctuation
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)

    # =========================================================
    # CLEAN UP PUNCTUATION ARTIFACTS
    # Left after regex removal, e.g:
    #   ", and"  at start  ->  "And"
    #   "( )"    empty     ->  ""
    #   " -- "   dangling  ->  " "
    #   ": "     leading   ->  ""
    # =========================================================

    # remove empty parentheses / brackets
    text = re.sub(r"\(\s*\)", " ", text)
    text = re.sub(r"\[\s*\]", " ", text)

    # remove dangling dashes (with no word on one side)
    text = re.sub(r"(?<!\w)\s*[-—–]{1,2}\s*(?!\w)", " ", text)

    # remove leading conjunctions/punctuation at sentence start
    # e.g. ", and foo" -> "foo" | ". But" already fine
    text = re.sub(r"(?:^|(?<=\.))\s*[,;:\-—–]+\s*", " ", text)

    # collapse repeated punctuation like "!!" or ",,"
    text = re.sub(r"([.,!?;:])\1+", r"\1", text)

    # normalize whitespace
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    # strip leading punctuation at the very start of the string
    text = re.sub(r"^[^A-Za-z0-9\"'(]+", "", text)

    # =========================================================
    # REMOVE DUPLICATE SENTENCES
    # =========================================================

    sentences = re.split(r'(?<=[.!?])\s+', text)
    seen = set()
    unique_sentences = []

    for sentence in sentences:
        normalized = sentence.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_sentences.append(sentence.strip())

    text = " ".join(unique_sentences)

    # =========================================================
    # LIMIT DESCRIPTION LENGTH
    # =========================================================

    words = text.split()
    text = " ".join(words[:max_words])

    return text

books["clean_description"] = books["description"].apply(remove_noise)
print(f"  Description noise removed")

# ══════════════════════════════════════════════════════════════════
#  STEP 4 — Deduplicate descriptions (notebook Cell 7-8)
# ══════════════════════════════════════════════════════════════════

def deduplicate_descriptions(df, description_col="clean_description", title_col="title"):
    """
    Handles three distinct problems after cleaning:

    1. Empty descriptions   → dropped, logged separately
    2. Mismatched descriptions (diff titles, same desc) → ALL dropped, logged separately
    3. True duplicates (same title, same desc)          → First kept, rest dropped
    """
    df = df.copy()

    # ── 1. Empty descriptions ─────────────────────────────────────────────
    empty_mask = df[description_col].str.strip().eq("") | df[description_col].isna()
    empty_df = df[empty_mask][[title_col, description_col]].copy()

    non_empty_df = df[~empty_mask].copy()

    # ── 2. Identify ALL rows that share a description ─────────────────────
    # keep=False marks EVERY row that is part of a duplicate cluster
    all_dupes_mask = non_empty_df[description_col].duplicated(keep=False)
    all_dupes_df = non_empty_df[all_dupes_mask].copy()

    # Count how many unique titles are associated with each duplicated description
    title_counts = all_dupes_df.groupby(description_col)[title_col].transform('nunique')

    # ── 3. Mismatched Duplicates (Data Corruption) ────────────────────────
    # If a description belongs to >1 unique title, it's corrupted. Drop ALL.
    mismatch_mask = title_counts > 1
    mismatch_df = all_dupes_df[mismatch_mask].copy()

    # ── 4. True Duplicates (Safe to keep first) ───────────────────────────
    # If a description belongs to exactly 1 title, it's just a standard duplicate row.
    true_dupe_df = all_dupes_df[~mismatch_mask].copy()

    # Identify the ones we are actually dropping (the 2nd, 3rd, etc. occurrences)
    true_dupes_dropped_mask = true_dupe_df[description_col].duplicated(keep="first")
    true_dupes_dropped_df = true_dupe_df[true_dupes_dropped_mask].copy()

    # ── 5. Build Final Clean Dataset ──────────────────────────────────────
    # Start with non-empty, drop ALL mismatches, and drop the redundant true duplicates
    drop_indices = mismatch_df.index.union(true_dupes_dropped_df.index)
    df_clean = non_empty_df.drop(index=drop_indices).reset_index(drop=True)

    # ── Logging ───────────────────────────────────────────────────────────
    print("=" * 70)
    print(f"  EMPTY DESCRIPTIONS: {len(empty_df)} rows dropped")
    print("=" * 70)

    print("\n" + "=" * 70)
    print(f"  CORRUPT MISMATCHES (All Dropped): {len(mismatch_df)} rows")
    print("=" * 70)
    if not mismatch_df.empty:
        mismatch_df["preview"] = mismatch_df[description_col].str[:80]
        # Sort by description so you can easily see the clusters of corrupted rows
        print(mismatch_df.sort_values(description_col)[[title_col, "preview"]].to_string())

    print("\n" + "=" * 70)
    print(f"  TRUE DUPES (Extras Dropped): {len(true_dupes_dropped_df)} rows")
    print("=" * 70)

    print("\n" + "=" * 70)
    summary = {
        "original_rows":   len(df),
        "empty_dropped":   len(empty_df),
        "mismatches_dropped": len(mismatch_df),
        "true_dupes_dropped": len(true_dupes_dropped_df),
        "remaining_rows":  len(df_clean),
    }
    for k, v in summary.items():
        print(f"  {k:<25} {v}")
    print("=" * 70)

    return df_clean, summary


books, summary = deduplicate_descriptions(books, description_col="clean_description")

# ══════════════════════════════════════════════════════════════════
#  STEP 5 — Verify alignment with saved embeddings
# ══════════════════════════════════════════════════════════════════

embeddings = np.load(os.path.join(MODELS_DIR, "embeddings.npy"))
print(f"  Loaded embeddings: {embeddings.shape}")

# ── Align df to exactly the books that were embedded ─────────────
# The notebook may have produced a slightly different row count than
# the webapp's cleaning pipeline (pandas version differences, OS
# locale, etc.).  The only reliable anchor is the ordered list of
# book_ids saved from the notebook immediately after encoding.
#
# To generate this file, run ONE extra cell in your Colab notebook
# right after the SentenceTransformer encoding cell:
#
#   import numpy as np
#   np.save("models/embedded_book_ids.npy",
#           books["book_id"].values.astype(np.int64))
#
# Then download it and place it in your models/ directory.

EMBEDDED_IDS_PATH = os.path.join(MODELS_DIR, "embedded_book_ids.npy")

embedded_ids = np.load(EMBEDDED_IDS_PATH).tolist()
embedded_ids_set = set(embedded_ids)

# Align df to exactly the books that were embedded, in the same order
books = books[books["book_id"].isin(embedded_ids_set)].copy()

id_to_emb_pos = {bid: pos for pos, bid in enumerate(embedded_ids)}
books["_emb_pos"] = books["book_id"].map(id_to_emb_pos)
books = books.sort_values("_emb_pos").drop(columns=["_emb_pos"]).reset_index(drop=True)

# Trim embeddings to match (in case webapp dropped extra rows the notebook kept)
embeddings = embeddings[[id_to_emb_pos[bid] for bid in books["book_id"].values]]

print(f"  ✓ Aligned: {len(books):,} books, {embeddings.shape[0]:,} embeddings — match: {len(books) == embeddings.shape[0]}")

book_id_to_idx = {int(bid): i for i, bid in enumerate(books["book_id"].values)}
n_books = len(books)


print(f"  embedded_book_ids.npy count: {len(embedded_ids)}")
print(f"  embeddings.npy shape: {embeddings.shape}")
print(f"  books after alignment: {len(books)}")
print(f"  First 5 book_ids in books: {books['book_id'].values[:5].tolist()}")
print(f"  First 5 embedded_ids: {embedded_ids[:5]}")
# ══════════════════════════════════════════════════════════════════
#  STEP 6 — Feature Engineering (notebook Cells 14-20)
# ══════════════════════════════════════════════════════════════════

print("  Engineering features (matching notebook pipeline)...")

CURRENT_YEAR = 2026

books["book_age"] = CURRENT_YEAR - books["original_publication_year"]
books["book_age"] = books["book_age"].fillna(books["book_age"].median())

books["popularity_score"] = books["average_rating"] * np.log1p(books["ratings_count"])

books["genre_count"] = (
    books["genres"]
    .fillna("")
    .apply(lambda x: 0 if x == "" else len(x.split(",")))
)

books["positive_ratio"] = (
    (books["ratings_4"] + books["ratings_5"]) /
    books["ratings_count"].replace(0, 1)
)

books["controversy_score"] = (
    (books["ratings_1"] + books["ratings_5"]) /
    books["ratings_count"]
)

author_pop = books.groupby("authors")["ratings_count"].mean()
books["author_popularity"] = np.log1p(books["authors"].map(author_pop))

# FIX: features uses raw description[:300], NOT clean_description.
# This matches notebook Cell 20 exactly. The TF-IDF vectorizer was
# fitted on this column in the notebook, so the webapp must reproduce
# it identically when calling tfidf_vectorizer.transform().
books["features"] = (
    books["title"] + " " +
    books["title"] + " " +
    books["authors"] + " " +
    books["genres"] + " " +
    books["genres"] + " " +
    books["genres"] + " " +
    books["clean_description"].str[:300]
)


books["ratings_count_log"] = np.log1p(books["ratings_count"])

print("  Engineered 7 numerical features")




# ══════════════════════════════════════════════════════════════════
#  STEP 7 — TF-IDF matrix (transform with saved vectorizer)
# ══════════════════════════════════════════════════════════════════

tfidf_vectorizer = joblib.load(os.path.join(MODELS_DIR, "tfidf.pkl"))
print(f"  Loaded TF-IDF vectorizer: vocab size={len(tfidf_vectorizer.vocabulary_)}")

tfidf_matrix = tfidf_vectorizer.transform(books["features"])
print(f"  TF-IDF matrix: {tfidf_matrix.shape}")

# ══════════════════════════════════════════════════════════════════
#  STEP 8 — Numerical matrix (transform with saved scaler)
# ══════════════════════════════════════════════════════════════════

scaler = joblib.load(os.path.join(MODELS_DIR, "scaler.pkl"))
print("  Loaded StandardScaler")

num_cols = [
    "average_rating", "pages", "book_age", "ratings_count_log",
    "popularity_score", "genre_count", "positive_ratio",
    "controversy_score", "author_popularity",
]

books["pages"] = books["pages"].fillna(books["pages"].median())
scaled_cols = [c + "_scaled" for c in num_cols]
books[scaled_cols] = scaler.transform(books[num_cols].fillna(0))

numerical_matrix = books[scaled_cols].fillna(0).values.astype(np.float32)
print(f"  Numerical matrix: {numerical_matrix.shape}")

# ══════════════════════════════════════════════════════════════════
#  STEP 9 — Initialize Recommenders
# ══════════════════════════════════════════════════════════════════

# FIX: book_id_to_idx and n_books were defined only inside the
# commented-out STEP 5 block. Define them here unconditionally so
# CollaborativeRecommender can be constructed correctly.
book_id_to_idx = {int(bid): i for i, bid in enumerate(books["book_id"].values)}
n_books = len(books)

from .recommender import ContentBasedRecommender, HybridRecommender

content_recommender = ContentBasedRecommender(
    embeddings,
    tfidf_matrix=tfidf_matrix,
    numerical_matrix=numerical_matrix,
    df=books,
    models_dir=MODELS_DIR,
)
print("  Content-based recommender ready (3-signal: Dense 40% + TF-IDF 40% + Numerical 20%)")

collab_recommender = None
try:
    if os.path.exists(RATINGS_PATH):
        ratings_df = pd.read_csv(RATINGS_PATH)
        print(f"  Loaded {len(ratings_df):,} ratings")
        from .recommender import CollaborativeRecommender
        collab_recommender = CollaborativeRecommender(
            ratings_df, book_id_to_idx, n_books, df=books
        )
except Exception as e:
    print(f"  [!] Collaborative recommender skipped: {e}")

# FIX: Build DiversityFilter and pass quality_book_ids so it can
# enforce the quality gate inside apply(), matching the notebook's
# apply_diversity_filter() which checks `if book_id not in _quality_book_ids`.
from .recommender import DiversityFilter

# Reuse the same quality mask logic as HybridRecommender so they're in sync.
# FIX: Define quality thresholds directly here instead of importing from recommender
QUALITY_MIN_RATING        = 3.8
QUALITY_MIN_RATINGS_COUNT = 500
QUALITY_MIN_PAGES         = 100

def _passes_quality_filter_local(book_row):
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

_quality_mask = books.apply(_passes_quality_filter_local, axis=1)
_quality_book_ids = set(books.loc[_quality_mask, "book_id"])

diversity_filter = DiversityFilter(books, quality_book_ids=_quality_book_ids)

hybrid_recommender = HybridRecommender(
    content_recommender,
    collab_recommender,
    diversity_filter=diversity_filter,
    df=books,
)
print("  Hybrid recommender ready (dynamic weight blending + quality/diversity filters)")

# ══════════════════════════════════════════════════════════════════
#  STEP 10 — Initialize Database
# ══════════════════════════════════════════════════════════════════

from .database.connection import init_db
init_db()
print("  SQLite database initialized")

# ── App State ────────────────────────────────────────────────────
app_state = {
    "df": books,
    "embeddings": embeddings,
    "tfidf_vectorizer": tfidf_vectorizer,
    "scaler": scaler,
    "content_recommender": content_recommender,
    "collab_recommender": collab_recommender,
    "hybrid_recommender": hybrid_recommender,
}

# ── GraphQL Router ───────────────────────────────────────────────
from .graphql.schema import create_graphql_router
graphql_router = create_graphql_router(app_state)
app.include_router(graphql_router, prefix="/graphql")

# ── REST API Endpoints ───────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Book Recommendation API", "graphql": "/graphql"}


@app.get("/api/health")
def health():
    rebuilt_index = content_recommender.faiss_index
    return {
        "status": "ok",
        "books": len(books),
        "embeddings": embeddings.shape[0],
        "faiss_vectors": rebuilt_index.ntotal,
        "faiss_type": "IndexFlatIP (cosine)",
        "l2_normalized": True,
        "tfidf_shape": list(tfidf_matrix.shape),
        "numerical_shape": list(numerical_matrix.shape),
        "signals": "Dense 40% + TF-IDF 40% + Numerical 20%",
    }


@app.post("/api/demo-login")
def demo_login(username: str):
    """Demo login endpoint - creates or returns existing user."""
    from .database import get_or_create_user, get_favorite_book_ids, SessionLocal
    db = SessionLocal()
    try:
        user = get_or_create_user(db, username)
        favs = get_favorite_book_ids(db, user.id)
        return {
            "id": user.id,
            "username": user.username,
            "created_at": str(user.created_at),
            "favorites_count": len(favs),
            "favorite_book_ids": favs,
        }
    finally:
        db.close()


print("=" * 60)
print("  Server ready! GraphQL at http://localhost:8000/graphql")
print("=" * 60)