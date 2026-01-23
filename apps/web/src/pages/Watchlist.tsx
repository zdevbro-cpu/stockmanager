import { useEffect, useMemo, useState } from 'react';
import { useWatchlist } from '../hooks/useWatchlist';
import { useSettings } from '../contexts/SettingsContext';
import { createApiClient } from '../lib/apiClient';

type SearchResult = {
    id: number;
    name: string;
    ticker: string;
    sector?: string | null;
    market?: string | null;
};

type Quote = {
    ticker: string;
    close: number | null;
    prev_close: number | null;
    change: number | null;
    change_percent: number | null;
    trade_date: string | null;
};

export default function Watchlist() {
    const { apiBaseUrl } = useSettings();
    const api = useMemo(() => createApiClient(apiBaseUrl), [apiBaseUrl]);
    const { watchlist, addStock, removeStock, updateNote } = useWatchlist();
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<SearchResult[]>([]);
    const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
    const [isSearching, setIsSearching] = useState(false);
    const [quotes, setQuotes] = useState<Record<string, Quote>>({});
    const [isLoadingQuotes, setIsLoadingQuotes] = useState(false);
    const [nameMap, setNameMap] = useState<Record<string, string>>({});

    const handleAdd = (e: React.FormEvent) => {
        e.preventDefault();
        const pick = selectedResult ?? (results.length === 1 ? results[0] : null);
        if (pick) {
            addStock(pick.ticker, pick.name);
            setQuery('');
            setResults([]);
            setSelectedResult(null);
        }
    };

    useEffect(() => {
        if (!query.trim()) {
            setResults([]);
            setSelectedResult(null);
            return;
        }
        let cancelled = false;
        setIsSearching(true);
        const handle = setTimeout(async () => {
            try {
                const response = await api.get<SearchResult[]>('/companies/search', {
                    params: { q: query.trim() },
                });
                if (!cancelled) {
                    setResults(response.data || []);
                    setSelectedResult(null);
                }
            } catch (error) {
                if (!cancelled) {
                    setResults([]);
                }
            } finally {
                if (!cancelled) {
                    setIsSearching(false);
                }
            }
        }, 250);
        return () => {
            cancelled = true;
            clearTimeout(handle);
        };
    }, [api, query]);

    useEffect(() => {
        const tickers = watchlist.map((item) => item.ticker).filter(Boolean);
        if (tickers.length === 0) {
            setQuotes({});
            return;
        }
        let cancelled = false;
        setIsLoadingQuotes(true);
        api.get<{ items: Quote[] }>('/prices/quotes', {
            params: { tickers: tickers.join(',') },
        })
            .then((response) => {
                if (cancelled) return;
                const next: Record<string, Quote> = {};
                (response.data?.items || []).forEach((entry) => {
                    next[entry.ticker] = entry;
                });
                setQuotes(next);
            })
            .catch(() => {
                if (!cancelled) {
                    setQuotes({});
                }
            })
            .finally(() => {
                if (!cancelled) {
                    setIsLoadingQuotes(false);
                }
            });
        return () => {
            cancelled = true;
        };
    }, [api, watchlist]);

    useEffect(() => {
        const targets = watchlist
            .filter((item) => !item.name || item.name === item.ticker)
            .map((item) => item.ticker)
            .filter(Boolean);
        if (targets.length === 0) return;
        let cancelled = false;
        const fetchNames = async () => {
            const entries = await Promise.all(
                targets.map(async (ticker) => {
                    try {
                        const response = await api.get<SearchResult[]>('/companies/search', {
                            params: { q: ticker },
                        });
                        const first = (response.data || [])[0];
                        return first?.name ? [ticker, first.name] as const : null;
                    } catch {
                        return null;
                    }
                })
            );
            if (cancelled) return;
            const next: Record<string, string> = { ...nameMap };
            entries.forEach((entry) => {
                if (!entry) return;
                const [ticker, name] = entry;
                next[ticker] = name;
            });
            setNameMap(next);
        };
        fetchNames();
        return () => {
            cancelled = true;
        };
    }, [api, watchlist, nameMap]);

    const formatNumber = (value: number | null, digits = 0) => {
        if (value === null || value === undefined || Number.isNaN(value)) {
            return '-';
        }
        return value.toLocaleString(undefined, {
            minimumFractionDigits: digits,
            maximumFractionDigits: digits,
        });
    };

    const getChangeTone = (value: number | null) => {
        if (value === null || value === undefined || Number.isNaN(value)) {
            return 'text-text-subtle';
        }
        if (value > 0) return 'text-emerald-300';
        if (value < 0) return 'text-rose-300';
        return 'text-text-subtle';
    };

    return (
        <div className="flex flex-col gap-8 max-w-5xl mx-auto">
            <h1 className="text-2xl font-bold text-white">관심종목 (Watchlist)</h1>

            <div className="bg-card-dark border border-border-dark rounded-xl p-6">
                <h2 className="text-lg font-bold text-white mb-4">새 종목 추가</h2>
                <form onSubmit={handleAdd} className="flex flex-col md:flex-row gap-4 items-end">
                    <div className="flex flex-col gap-2 flex-1 w-full relative">
                        <label className="text-xs font-bold text-text-subtle">종목 검색 (티커 또는 종목명)</label>
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="예: 005930 또는 삼성전자"
                            className="bg-background-dark border border-border-dark rounded-lg px-4 py-2 text-white outline-none focus:border-primary w-full"
                        />
                        {query.trim().length > 0 && (
                            <div className="absolute top-[72px] left-0 right-0 bg-[#0f1716] border border-border-dark rounded-lg shadow-xl z-10 overflow-hidden">
                                {isSearching ? (
                                    <div className="px-4 py-3 text-sm text-text-subtle">검색 중...</div>
                                ) : results.length === 0 ? (
                                    <div className="px-4 py-3 text-sm text-text-subtle">검색 결과가 없습니다.</div>
                                ) : (
                                    <ul className="max-h-60 overflow-y-auto">
                                        {results.map((item) => (
                                            <li
                                                key={`${item.ticker}-${item.id}`}
                                                className={`px-4 py-3 text-sm text-white cursor-pointer flex items-center justify-between ${selectedResult?.ticker === item.ticker ? 'bg-white/10' : 'hover:bg-white/5'}`}
                                                onMouseDown={(event) => {
                                                    event.preventDefault();
                                                    setSelectedResult(item);
                                                    setQuery(item.name);
                                                    setResults([]);
                                                }}
                                            >
                                                <span className="font-semibold">{item.name}</span>
                                                <span className="text-text-subtle">{item.ticker}</span>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                        )}
                    </div>
                    <button
                        type="submit"
                        className="bg-primary hover:bg-blue-600 text-white font-bold px-6 py-2 rounded-lg transition-colors whitespace-nowrap h-[42px] w-full md:w-auto"
                    >
                        추가
                    </button>
                </form>
            </div>

            <div className="bg-card-dark border border-border-dark rounded-xl overflow-hidden">
                {watchlist.length === 0 ? (
                    <div className="p-10 text-center text-text-subtle">
                        등록된 관심종목이 없습니다.
                        <button
                            onClick={() => addStock('005930', '삼성전자')}
                            className="block mx-auto mt-4 text-primary hover:underline"
                        >
                            삼성전자 예시 추가
                        </button>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="bg-[#151e1d] border-b border-border-dark text-text-subtle">
                                    <th className="px-6 py-4 text-left font-bold w-52">종목명 (Ticker)</th>
                                    <th className="px-6 py-4 text-right font-bold w-32">Prev Close</th>
                                    <th className="px-6 py-4 text-right font-bold w-32">Last Price</th>
                                    <th className="px-6 py-4 text-right font-bold w-32">Change</th>
                                    <th className="px-6 py-4 text-left font-bold">Memo</th>
                                    <th className="px-6 py-4 text-right font-bold w-32">Added</th>
                                    <th className="px-6 py-4 text-right font-bold w-24">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border-dark/50">
                                {watchlist.map((item) => {
                                    const quote = quotes[item.ticker];
                                    const change = quote?.change ?? null;
                                    const changePercent = quote?.change_percent ?? null;
                                    return (
                                        <tr key={item.ticker} className="hover:bg-white/5 transition-colors">
                                            <td className="px-6 py-4">
                                                <div className="flex flex-col">
                                                    <span className="text-white font-bold">
                                                        {item.name && item.name !== item.ticker
                                                            ? item.name
                                                            : (nameMap[item.ticker] || item.ticker)}
                                                    </span>
                                                    <span className="text-xs text-text-subtle">{item.ticker}</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-right text-text-subtle">
                                                {formatNumber(quote?.prev_close ?? null)}
                                            </td>
                                            <td className="px-6 py-4 text-right text-white">
                                                {formatNumber(quote?.close ?? null)}
                                            </td>
                                            <td className={`px-6 py-4 text-right font-semibold ${getChangeTone(change)}`}>
                                                {change === null
                                                    ? '-'
                                                    : `${change > 0 ? '+' : ''}${formatNumber(change, 2)}${
                                                          changePercent !== null
                                                              ? ` (${changePercent > 0 ? '+' : ''}${formatNumber(changePercent, 2)}%)`
                                                              : ''
                                                      }`}
                                            </td>
                                            <td className="px-6 py-4">
                                                <input
                                                    type="text"
                                                    value={item.note}
                                                    onChange={(e) => updateNote(item.ticker, e.target.value)}
                                                    placeholder="메모를 입력하세요."
                                                    className="bg-transparent border-b border-transparent focus:border-primary outline-none text-gray-300 w-full placeholder:text-gray-600"
                                                />
                                            </td>
                                            <td className="px-6 py-4 text-right text-text-subtle text-xs">
                                                {item.addedAt}
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <button
                                                    onClick={() => removeStock(item.ticker)}
                                                    className="text-red-500 hover:text-red-400 p-1 hover:bg-red-500/10 rounded transition-colors"
                                                >
                                                    <span className="material-symbols-outlined text-[20px]">delete</span>
                                                </button>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                        {isLoadingQuotes && (
                            <div className="px-6 py-3 text-xs text-text-subtle border-t border-border-dark">
                                가격 정보를 불러오는 중입니다...
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

