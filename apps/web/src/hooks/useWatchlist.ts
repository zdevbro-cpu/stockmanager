import { useState, useEffect, useCallback } from 'react';
import { useSettings } from '../contexts/SettingsContext';
import { createApiClient } from '../lib/apiClient';

export interface WatchlistItem {
    ticker: string;
    name: string;
    note: string;
    addedAt: string;
}

const CACHE_KEY = 'stockmanager_watchlist_cache';

const loadCache = () => {
    const stored = localStorage.getItem(CACHE_KEY);
    if (!stored) return [] as WatchlistItem[];
    try {
        return JSON.parse(stored) as WatchlistItem[];
    } catch {
        return [] as WatchlistItem[];
    }
};

const mergeItems = (serverItems: WatchlistItem[], cachedItems: WatchlistItem[]) => {
    const map = new Map<string, WatchlistItem>();
    cachedItems.forEach((item) => map.set(item.ticker, item));
    serverItems.forEach((item) => {
        const existing = map.get(item.ticker);
        map.set(item.ticker, {
            ticker: item.ticker,
            name: item.name || existing?.name || '',
            note: item.note || existing?.note || '',
            addedAt: item.addedAt || existing?.addedAt || ''
        });
    });
    return Array.from(map.values());
};

export function useWatchlist() {
    const { apiBaseUrl } = useSettings();
    const [watchlistId, setWatchlistId] = useState<number | null>(null);
    const [watchlist, setWatchlist] = useState<WatchlistItem[]>(() => loadCache());

    const migrateLocalWatchlist = useCallback(async (listId: number) => {
        const stored = localStorage.getItem('stockmanager_watchlist');
        if (!stored) return false;
        let parsed: WatchlistItem[] = [];
        try {
            parsed = JSON.parse(stored) as WatchlistItem[];
        } catch (error) {
            return false;
        }
        if (!parsed.length) return false;
        if (!apiBaseUrl) return false;
        const client = createApiClient(apiBaseUrl);
        for (const item of parsed) {
            await client.post(`/watchlists/${listId}/items`, { ticker: item.ticker, name: item.name });
            if (item.note) {
                await client.put(`/watchlists/${listId}/items/${encodeURIComponent(item.ticker)}`, { note: item.note });
            }
        }
        localStorage.removeItem('stockmanager_watchlist');
        return true;
    }, [apiBaseUrl]);

    const fetchWatchlist = useCallback(async () => {
        if (!apiBaseUrl) return;
        const client = createApiClient(apiBaseUrl);
        const resp = await client.get('/watchlists');
        const items = resp.data?.items || [];
        let id = items[0]?.watchlist_id as number | undefined;
        if (!id) {
            const created = await client.post('/watchlists', { name: '관심종목' });
            id = created.data?.watchlist_id;
        }
        setWatchlistId(id ?? null);
        if (!id) {
            setWatchlist([]);
            return;
        }
        const listResp = await client.get(`/watchlists/${id}/items`);
        let rows = listResp.data?.items || [];
        if (rows.length === 0) {
            const migrated = await migrateLocalWatchlist(id);
            if (migrated) {
                const reloaded = await client.get(`/watchlists/${id}/items`);
                rows = reloaded.data?.items || [];
            }
        }
        const serverItems = rows.map((item: any) => ({
            ticker: item.ticker,
            name: item.name || '',
            note: item.note || '',
            addedAt: item.added_at || ''
        }));
        const merged = mergeItems(serverItems, loadCache());
        setWatchlist(merged);
    }, [apiBaseUrl, migrateLocalWatchlist]);

    useEffect(() => {
        fetchWatchlist().catch((error) => {
            console.error('Failed to fetch watchlist', error);
            setWatchlist([]);
            setWatchlistId(null);
        });
    }, [fetchWatchlist]);

    const addStock = async (ticker: string, name: string) => {
        if (watchlist.some(item => item.ticker === ticker)) return;
        const next = [...watchlist, {
            ticker,
            name,
            note: '',
            addedAt: new Date().toISOString().split('T')[0]
        }];
        setWatchlist(next);
        localStorage.setItem(CACHE_KEY, JSON.stringify(next));
        if (!watchlistId || !apiBaseUrl) return;
        const client = createApiClient(apiBaseUrl);
        try {
            await client.post(`/watchlists/${watchlistId}/items`, { ticker, name });
            await fetchWatchlist();
        } catch {
            // Keep optimistic result
        }
    };

    const removeStock = async (ticker: string) => {
        const next = watchlist.filter(item => item.ticker !== ticker);
        setWatchlist(next);
        localStorage.setItem(CACHE_KEY, JSON.stringify(next));
        if (!watchlistId || !apiBaseUrl) return;
        const client = createApiClient(apiBaseUrl);
        try {
            await client.delete(`/watchlists/${watchlistId}/items/${encodeURIComponent(ticker)}`);
            await fetchWatchlist();
        } catch {
            // Keep optimistic result
        }
    };

    const updateNote = async (ticker: string, note: string) => {
        const next = watchlist.map(item =>
            item.ticker === ticker ? { ...item, note } : item
        );
        setWatchlist(next);
        localStorage.setItem(CACHE_KEY, JSON.stringify(next));
        if (!watchlistId || !apiBaseUrl) return;
        const client = createApiClient(apiBaseUrl);
        try {
            await client.put(`/watchlists/${watchlistId}/items/${encodeURIComponent(ticker)}`, { note });
            await fetchWatchlist();
        } catch {
            // Keep optimistic result
        }
    };

    return { watchlist, addStock, removeStock, updateNote };
}
