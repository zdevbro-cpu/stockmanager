import { createContext, useContext, useMemo, useState } from "react";
import { loadJson, saveJson } from "../lib/storage";

export type WatchlistItem = {
  ticker: string;
  note?: string;
  addedAt: string;
};

type WatchlistContextValue = {
  items: WatchlistItem[];
  addTicker: (ticker: string) => void;
  removeTicker: (ticker: string) => void;
  setNote: (ticker: string, note: string) => void;
  hasTicker: (ticker: string) => boolean;
};

const WatchlistContext = createContext<WatchlistContextValue | null>(null);

const STORAGE_KEY = "stockmanager.watchlist";

export const WatchlistProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const [items, setItems] = useState<WatchlistItem[]>(
    loadJson<WatchlistItem[]>(STORAGE_KEY, [])
  );

  const persist = (next: WatchlistItem[]) => {
    setItems(next);
    saveJson(STORAGE_KEY, next);
  };

  const addTicker = (ticker: string) => {
    const normalized = ticker.trim();
    if (!normalized) return;
    if (items.some((item) => item.ticker === normalized)) return;
    persist([
      ...items,
      { ticker: normalized, addedAt: new Date().toISOString() },
    ]);
  };

  const removeTicker = (ticker: string) => {
    persist(items.filter((item) => item.ticker !== ticker));
  };

  const setNote = (ticker: string, note: string) => {
    persist(
      items.map((item) =>
        item.ticker === ticker ? { ...item, note } : item
      )
    );
  };

  const hasTicker = (ticker: string) =>
    items.some((item) => item.ticker === ticker);

  const value = useMemo(
    () => ({ items, addTicker, removeTicker, setNote, hasTicker }),
    [items]
  );

  return (
    <WatchlistContext.Provider value={value}>
      {children}
    </WatchlistContext.Provider>
  );
};

export const useWatchlist = () => {
  const context = useContext(WatchlistContext);
  if (!context) {
    throw new Error("WatchlistProvider가 필요합니다.");
  }
  return context;
};
