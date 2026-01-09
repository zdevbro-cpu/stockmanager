import { useState, useEffect } from 'react';

export interface WatchlistItem {
    ticker: string;
    name: string;
    note: string;
    addedAt: string;
}

export function useWatchlist() {
    const [watchlist, setWatchlist] = useState<WatchlistItem[]>(() => {
        const stored = localStorage.getItem('stockmanager_watchlist');
        return stored ? JSON.parse(stored) : [];
    });

    useEffect(() => {
        localStorage.setItem('stockmanager_watchlist', JSON.stringify(watchlist));
    }, [watchlist]);

    const addStock = (ticker: string, name: string) => {
        if (watchlist.some(item => item.ticker === ticker)) return;
        setWatchlist(prev => [...prev, {
            ticker,
            name,
            note: '',
            addedAt: new Date().toISOString().split('T')[0]
        }]);
    };

    const removeStock = (ticker: string) => {
        setWatchlist(prev => prev.filter(item => item.ticker !== ticker));
    };

    const updateNote = (ticker: string, note: string) => {
        setWatchlist(prev => prev.map(item =>
            item.ticker === ticker ? { ...item, note } : item
        ));
    };

    return { watchlist, addStock, removeStock, updateNote };
}
