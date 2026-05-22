"use client";

import { gqlMutate } from "@/lib/graphql";
import { TOGGLE_FAVORITE } from "@/graphql/mutations";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";

// ── User Context ──
interface UserContextType {
  username: string | null;
  setUsername: (name: string | null) => void;
  favoriteIds: number[];
  setFavoriteIds: (ids: number[]) => void;
  toggleFavorite: (bookId: number) => Promise<void>;
  isFavorite: (bookId: number) => boolean;
}

const UserContext = createContext<UserContextType>({
  username: null,
  setUsername: () => {},
  favoriteIds: [],
  setFavoriteIds: () => {},
  toggleFavorite: async () => {},
  isFavorite: () => false,
});

export const useUser = () => useContext(UserContext);

// ── Toast Context ──
interface Toast {
  id: number;
  message: string;
  type: "success" | "error" | "info";
}

interface ToastContextType {
  showToast: (message: string, type?: "success" | "error" | "info") => void;
}

const ToastContext = createContext<ToastContextType>({
  showToast: () => {},
});

export const useToast = () => useContext(ToastContext);

// ── Provider Component ──
export function Providers({ children }: { children: ReactNode }) {
  const [username, setUsername] = useState<string | null>(null);
  const [favoriteIds, setFavoriteIds] = useState<number[]>([]);
  const [toasts, setToasts] = useState<Toast[]>([]);

  // Load username from localStorage
  useEffect(() => {
    const stored = localStorage.getItem("bookapp_username");
    if (stored) {
      setUsername(stored);
      loadFavorites(stored);
    }
  }, []);

  const loadFavorites = async (name: string) => {
    try {
      const res = await fetch(
        `/api/demo-login?username=${encodeURIComponent(name)}`,
        { method: "POST" }
      );
      const data = await res.json();
      setFavoriteIds(data.favorite_book_ids || []);
    } catch {
      // Silently fail
    }
  };

  const handleSetUsername = (name: string | null) => {
    setUsername(name);
    if (name) {
      localStorage.setItem("bookapp_username", name);
      loadFavorites(name);
    } else {
      localStorage.removeItem("bookapp_username");
      setFavoriteIds([]);
    }
  };

  const toggleFavorite = async (bookId: number) => {
    if (!username) return;
    try {
      const data = await gqlMutate<{ toggleFavorite: boolean }>(
        TOGGLE_FAVORITE,
        { username, bookId }
      );
      const isNowFavorite = data.toggleFavorite;
      if (isNowFavorite) {
        setFavoriteIds((prev) => [...prev, bookId]);
        showToast("Added to favorites!", "success");
      } else {
        setFavoriteIds((prev) => prev.filter((id) => id !== bookId));
        showToast("Removed from favorites", "info");
      }
    } catch {
      showToast("Failed to update favorite", "error");
    }
  };

  const isFavorite = (bookId: number) => favoriteIds.includes(bookId);

  const showToast = (message: string, type: "success" | "error" | "info" = "info") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  };

  return (
    <UserContext.Provider
      value={{
        username,
        setUsername: handleSetUsername,
        favoriteIds,
        setFavoriteIds,
        toggleFavorite,
        isFavorite,
      }}
    >
      <ToastContext.Provider value={{ showToast }}>
        {children}
        {/* Toast Container */}
        <div className="fixed bottom-6 right-6 flex flex-col gap-2 z-[1000]">
          {toasts.map((toast) => (
            <div key={toast.id} className={`toast ${toast.type}`}>
              {toast.message}
            </div>
          ))}
        </div>
      </ToastContext.Provider>
    </UserContext.Provider>
  );
}
