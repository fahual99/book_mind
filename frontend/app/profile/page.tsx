"use client";

import { useUser } from "@/app/providers";
import { useGraphQL } from "@/lib/hooks";
import { GET_USER_PROFILE, GET_STATS } from "@/graphql/queries";
import Link from "next/link";

export default function ProfilePage() {
  const { username, setUsername, favoriteIds } = useUser();

  const { data: profileData } = useGraphQL<{
    userProfile: { id: number; username: string; createdAt: string; favoritesCount: number } | null;
  }>(GET_USER_PROFILE, { username: username || "" }, { skip: !username });

  const { data: statsData } = useGraphQL<{
    stats: { totalBooks: number; totalAuthors: number; totalGenres: number; avgRating: number };
  }>(GET_STATS);

  if (!username) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">Please log in first</h2>
          <Link href="/" className="gradient-text text-lg hover:opacity-80 transition-all">Go to Login &rarr;</Link>
        </div>
      </div>
    );
  }

  const profile = profileData?.userProfile;
  const stats = statsData?.stats;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Profile Card */}
      <div className="glass-card p-8 mb-8 text-center">
        <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-[var(--color-accent-1)] to-[var(--color-accent-3)] flex items-center justify-center text-3xl font-bold text-white">
          {username[0].toUpperCase()}
        </div>
        <h1 className="text-2xl font-bold mb-1">{username}</h1>
        <p className="text-[var(--color-text-secondary)] text-sm mb-4">
          Member since {profile?.createdAt ? new Date(profile.createdAt).toLocaleDateString() : "today"}
        </p>

        <div className="flex justify-center gap-8 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold gradient-text">{favoriteIds.length}</div>
            <div className="text-xs text-[var(--color-text-muted)]">Favorites</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold gradient-text">{stats?.totalBooks?.toLocaleString() || "\u2014"}</div>
            <div className="text-xs text-[var(--color-text-muted)]">Books Available</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold gradient-text">{stats?.totalGenres || "\u2014"}</div>
            <div className="text-xs text-[var(--color-text-muted)]">Genres</div>
          </div>
        </div>

        <div className="flex justify-center gap-3">
          <Link href="/favorites" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[var(--color-accent-1)]/15 text-[var(--color-accent-1)] font-medium text-sm border border-[var(--color-accent-1)]/30 no-underline hover:bg-[var(--color-accent-1)]/25 transition-all">
            View Favorites
          </Link>
          <button onClick={() => setUsername(null)} className="px-5 py-2.5 rounded-xl bg-white/5 text-[var(--color-text-secondary)] font-medium text-sm border border-[var(--color-border)] hover:bg-white/10 hover:text-white transition-all">
            Switch User
          </button>
        </div>
      </div>

      {/* About */}
      <div className="glass-card p-8">
        <h2 className="text-xl font-bold mb-4">About <span className="gradient-text">BookMind AI</span></h2>
        <div className="space-y-4">
          {[
            { icon: "\uD83E\uDDE0", title: "Hybrid Recommendation Engine", desc: "Combines content-based (FAISS + SentenceTransformer embeddings) with collaborative filtering from user ratings for highly accurate recommendations." },
            { icon: "\uD83D\uDD0D", title: "Semantic Search", desc: "384-dimensional embeddings enable semantic understanding of book descriptions beyond simple keyword matching." },
            { icon: "\uD83D\uDCCA", title: "GraphQL API", desc: "Strawberry GraphQL provides a flexible API layer with real-time queries and mutations for favorites management." },
            { icon: "\uD83D\uDCBE", title: "Persistent Profiles", desc: "SQLite database stores your username and favorites permanently \u2014 they persist even when the app restarts." },
          ].map((item) => (
            <div key={item.title} className="flex gap-4 p-4 rounded-xl bg-white/3 hover:bg-white/5 transition-all">
              <div className="text-2xl flex-shrink-0">{item.icon}</div>
              <div>
                <h3 className="font-semibold text-sm mb-0.5">{item.title}</h3>
                <p className="text-sm text-[var(--color-text-secondary)]">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
