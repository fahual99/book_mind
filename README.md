# 📚 BookMind AI — Intelligent Book Recommendation System

A full-stack, AI-powered book recommendation web application featuring a **hybrid recommendation engine** that combines content-based filtering (FAISS + TF-IDF + numerical features) with user-based collaborative filtering. The system serves recommendations through a **GraphQL API** and presents them via a modern **Next.js** dark-themed UI.

---

## 🏗️ Tech Stack

### Backend

| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.10+ | Core backend language |
| **FastAPI** | latest | High-performance async web framework |
| **Uvicorn** | latest | ASGI server for FastAPI |
| **Strawberry GraphQL** | latest | GraphQL API layer (type-safe, FastAPI integration) |
| **SQLAlchemy** | latest | ORM for database operations |
| **SQLite** | 3.x | Lightweight relational database (user accounts & favorites) |
| **FAISS (faiss-cpu)** | latest | Facebook AI Similarity Search — dense vector nearest-neighbor lookup |
| **Sentence Transformers** | latest | Pre-trained transformer models for text embeddings |
| **scikit-learn** | latest | TF-IDF vectorization, StandardScaler for numerical features |
| **Pandas** | latest | Data cleaning, feature engineering pipeline |
| **NumPy** | latest | Numerical arrays (embeddings, matrices) |
| **joblib** | latest | Serialization of ML artifacts (TF-IDF vectorizer, scaler) |

### Frontend

| Technology | Version | Purpose |
|---|---|---|
| **Next.js** | 16.2.6 | React meta-framework (App Router, SSR, file-based routing) |
| **React** | 19.2.4 | UI component library |
| **TypeScript** | 5.x | Type-safe JavaScript |
| **Tailwind CSS** | 4.x | Utility-first CSS framework |
| **PostCSS** | latest | CSS processing pipeline |
| **Custom GraphQL Client** | — | Lightweight `fetch()`-based client (replaces Apollo for React 19 compatibility) |

### ML Models & Data Assets

| Asset | Format | Description |
|---|---|---|
| `embeddings.npy` | NumPy | Dense sentence-transformer embeddings (~8,700 books) |
| `embedded_book_ids.npy` | NumPy | Ordered book IDs aligned with embedding rows |
| `faiss.index` | FAISS binary | Pre-built cosine similarity index (IndexFlatIP) |
| `tfidf.pkl` | joblib/pickle | Fitted TF-IDF vectorizer |
| `scaler.pkl` | joblib/pickle | Fitted StandardScaler for numerical features |
| `books_enriched.csv` | CSV | Enriched book metadata (~10K books) |
| `ratings.csv` | CSV | User–book ratings for collaborative filtering |

---

## 📂 Project Structure

```
book_webapp/
├── backend/
│   ├── requirements.txt              # Python dependencies
│   └── app/
│       ├── __init__.py
│       ├── main.py                   # FastAPI entry point, data pipeline, ML loading
│       ├── database/
│       │   ├── connection.py         # SQLAlchemy engine + session (SQLite)
│       │   ├── models.py            # User & Favorite ORM models
│       │   └── crud.py             # Create/read operations for users & favorites
│       ├── graphql/
│       │   ├── schema.py           # Strawberry GraphQL schema + router
│       │   ├── types.py            # GraphQL type definitions
│       │   ├── queries.py          # Query resolvers (books, search, recommendations)
│       │   └── mutations.py        # Mutation resolvers (favorites, login)
│       └── recommender/
│           ├── content_based.py    # 3-signal content recommender (Dense + TF-IDF + Numerical)
│           ├── collaborative.py    # User-based collaborative filtering
│           ├── hybrid.py           # Dynamic weight blending + quality/diversity filtering
│           ├── diversity.py        # Author/genre diversity caps
│           └── embeddings.py       # Embedding utility service
├── frontend/
│   ├── package.json                # Node.js dependencies
│   ├── next.config.ts              # Next.js config (rewrites, image domains)
│   ├── tsconfig.json               # TypeScript configuration
│   ├── postcss.config.mjs          # PostCSS + Tailwind setup
│   ├── app/
│   │   ├── layout.tsx              # Root layout (Inter + Playfair Display fonts, dark theme)
│   │   ├── globals.css             # Global styles (glassmorphism, ambient orbs, animations)
│   │   ├── providers.tsx           # React context providers (auth, favorites)
│   │   ├── page.tsx                # Home page (featured books, recommendation rows)
│   │   ├── search/page.tsx         # Search results page
│   │   ├── favorites/page.tsx      # User favorites collection
│   │   └── profile/page.tsx        # User profile page
│   ├── components/
│   │   ├── Navbar.tsx              # Navigation bar with search
│   │   ├── BookCard.tsx            # Book display card component
│   │   ├── BookModal.tsx           # Detailed book modal with recommendations
│   │   ├── SearchBar.tsx           # Search input component
│   │   └── RecommendationRow.tsx   # Horizontal scrollable recommendation row
│   ├── graphql/
│   │   ├── queries.ts              # GraphQL query strings
│   │   └── mutations.ts            # GraphQL mutation strings
│   └── lib/
│       ├── graphql.ts              # Lightweight fetch-based GraphQL client
│       └── hooks.ts                # Custom React hooks (useQuery, useMutation)
├── models/                         # Pre-trained ML artifacts (*.npy, *.pkl, *.index)
├── dataset/                        # Source data (books_enriched.csv, ratings.csv)
├── notebooks/                      # Jupyter notebook (training & experimentation)
├── book_recommender.db             # SQLite database (auto-created)
└── README.md
```

---

## 🔧 Prerequisites

- **Python** 3.10 or higher
- **Node.js** 18 or higher (with npm)
- **Git** (for cloning)

---

## 🚀 Local Development Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd book_webapp
```

### 2. Backend Setup

```bash
cd backend

# Create and activate a virtual environment (recommended)
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend

# Install Node.js dependencies
npm install
```

### 4. Run the Application

**Option A — Run both servers manually:**

```bash
# Terminal 1: Start the backend (from /backend directory)
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Start the frontend (from /frontend directory)
npm run dev
```

**Option B — Use the batch script (Windows):**

```bash
# From root directory
run.bat
```

The app will be available at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **GraphQL Playground:** http://localhost:8000/graphql
- **Health Check:** http://localhost:8000/api/health

---

## 🌐 External Hosting / Deployment

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_BACKEND_URL` | `http://localhost:8000` | Backend API URL (set in frontend) |

### Option 1: Railway / Render (Recommended for Full-Stack)

#### Backend Deployment

1. Create a new service pointing to the `backend/` directory
2. **Build command:** `pip install -r requirements.txt`
3. **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Upload the `models/` and `dataset/` directories as persistent storage or include them in the repo
5. Set the port environment variable if required by the platform

#### Frontend Deployment

1. Create a new service pointing to the `frontend/` directory
2. **Build command:** `npm install && npm run build`
3. **Start command:** `npm start`
4. Set environment variable: `NEXT_PUBLIC_BACKEND_URL=https://your-backend-url.com`
5. Update `next.config.ts` → `allowedDevOrigins` with your production domain

#### Important Notes for Deployment

- The `models/` directory contains ~27 MB of ML artifacts that **must be accessible** to the backend at runtime
- The `dataset/` directory contains ~82 MB of CSV data loaded at startup
- The `book_recommender.db` SQLite file is auto-created on first run
- For production, consider switching SQLite to **PostgreSQL** using the `DATABASE_URL` pattern
- CORS origins in `main.py` must be updated to include your production frontend URL

### Option 2: Vercel (Frontend) + Railway/Render (Backend)

#### Frontend on Vercel

1. Import the `frontend/` directory as a new Vercel project
2. Framework preset: **Next.js**
3. Set environment variable: `NEXT_PUBLIC_BACKEND_URL=https://your-backend-url.com`
4. Deploy

#### Backend on Railway/Render

Follow the backend steps from Option 1 above.

### Option 3: Docker (Self-Hosted)

Create a `Dockerfile` for each service:

**Backend `Dockerfile`:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY models/ ./models/
COPY dataset/ ./dataset/

WORKDIR /app/backend

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend `Dockerfile`:**
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./

ARG NEXT_PUBLIC_BACKEND_URL
ENV NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL

RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

**`docker-compose.yml`:**
```yaml
version: "3.8"
services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models
      - ./dataset:/app/dataset

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
      args:
        NEXT_PUBLIC_BACKEND_URL: http://backend:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

---

## 🔌 API Overview

### GraphQL Endpoint: `/graphql`

**Queries:**
- `books(limit, offset)` — Paginated book catalog
- `book(id)` — Single book details
- `searchBooks(query)` — Full-text search across titles, authors, genres
- `recommendations(bookId, limit)` — Hybrid recommendations for a given book
- `userRecommendations(userId, limit)` — Personalized recommendations based on favorites

**Mutations:**
- `addFavorite(userId, bookId)` — Add a book to favorites
- `removeFavorite(userId, bookId)` — Remove a book from favorites

### REST Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | API info |
| `GET` | `/api/health` | Health check with system stats |
| `POST` | `/api/demo-login?username=` | Demo user login/registration |

---

## 🤖 Recommendation Engine

The hybrid recommender uses a **3-signal content scoring** pipeline:

| Signal | Weight | Method |
|---|---|---|
| **Dense Embeddings** | 40% | Sentence-transformer vectors → FAISS cosine similarity |
| **TF-IDF** | 40% | Sparse text features (title, authors, genres, description) |
| **Numerical Features** | 20% | Scaled metadata (rating, popularity, pages, book age, etc.) |

**Post-processing:**
- **Quality filter:** min rating ≥ 3.8, min ratings count ≥ 500, min pages ≥ 100
- **Diversity filter:** author/genre caps to prevent result homogeneity
- **Collaborative blending:** dynamic weight between content (70-100%) and collaborative (0-30%) scores based on neighbor coverage

---

## 📋 Checklist Before Deploying

- [ ] Update CORS origins in `backend/app/main.py` with your production URL
- [ ] Set `NEXT_PUBLIC_BACKEND_URL` environment variable in frontend
- [ ] Upload `models/` directory (all `.npy`, `.pkl`, `.index` files)
- [ ] Upload `dataset/` directory (`books_enriched.csv`, `ratings.csv`)
- [ ] Update `allowedDevOrigins` in `frontend/next.config.ts` (or remove it for production)
- [ ] Consider replacing SQLite with PostgreSQL for production use
- [ ] Set up persistent storage for `book_recommender.db` if using ephemeral containers

---

## 📄 License

This project was developed as an academic Machine Learning course project.
