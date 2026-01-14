import { useEffect, useMemo, useState } from 'react';
import { useSignals } from '../hooks/useStockData';
import { useWatchlist } from '../hooks/useWatchlist';
import { useSettings } from '../contexts/SettingsContext';
import { createApiClient } from '../lib/apiClient';
import clsx from 'clsx';

type Quote = {
    ticker: string;
    close: number | null;
    prev_close: number | null;
    change: number | null;
    change_percent: number | null;
    trade_date: string | null;
};

export default function Signals() {
    const [horizon, setHorizon] = useState('1D');
    const { watchlist } = useWatchlist();
    const tickers = watchlist.map((item) => item.ticker);
    const { data: signals } = useSignals({ horizon, tickers });
    const { apiBaseUrl } = useSettings();
    const api = useMemo(() => createApiClient(apiBaseUrl), [apiBaseUrl]);
    const [quotes, setQuotes] = useState<Record<string, Quote>>({});

    useEffect(() => {
        if (tickers.length === 0) {
            setQuotes({});
            return;
        }
        let cancelled = false;
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
            });
        return () => {
            cancelled = true;
        };
    }, [api, tickers]);

    const formatNumber = (value: number | null, digits = 0) => {
        if (value === null || value === undefined || Number.isNaN(value)) {
            return '-';
        }
        return value.toLocaleString(undefined, {
            minimumFractionDigits: digits,
            maximumFractionDigits: digits,
        });
    };
    const formatRange = (low?: number | null, high?: number | null) => {
        if (low === null || low === undefined || high === null || high === undefined) {
            return '-';
        }
        return `${formatNumber(low, 0)} ~ ${formatNumber(high, 0)}`;
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
        <div className="flex flex-col gap-6 max-w-7xl mx-auto">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-white">매매신호 (Signals)</h1>

                <div className="flex bg-card-dark border border-border-dark rounded-lg p-1">
                    {['1D', '3D', '1W'].map((h) => (
                        <button
                            key={h}
                            onClick={() => setHorizon(h)}
                            className={clsx(
                                "px-4 py-1.5 rounded-md text-sm font-bold transition-all",
                                horizon === h ? "bg-primary text-white shadow-lg" : "text-text-subtle hover:text-white"
                            )}
                        >
                            {h}
                        </button>
                    ))}
                </div>
            </div>

            <div className="bg-card-dark border border-border-dark rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="bg-[#151e1d] border-b border-border-dark text-text-subtle">
                                <th className="px-6 py-4 text-center font-bold">종목 (Ticker)</th>
                                <th className="px-6 py-4 text-center font-bold">전일가</th>
                                <th className="px-6 py-4 text-center font-bold">현재가</th>
                                <th className="px-6 py-4 text-center font-bold">등락폭</th>
                                <th className="px-6 py-4 text-center font-bold">신호</th>
                                <th className="px-6 py-4 text-center font-bold">발생 사유</th>
                                <th className="px-6 py-4 text-center font-bold">목표가 범위</th>
                                <th className="px-6 py-4 text-center font-bold">Horizon</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark/50">
                            {signals?.map((signal: any, i: number) => {
                                const quote = quotes[signal.ticker];
                                const change = quote?.change ?? null;
                                const changePercent = quote?.change_percent ?? null;
                                return (
                                    <tr key={i} className="hover:bg-white/5 transition-colors group">
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col">
                                                <span className="text-white font-bold">{signal.name}</span>
                                                <span className="text-xs text-text-subtle">{signal.ticker}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-right text-text-subtle">
                                            {formatNumber(quote?.prev_close ?? null)}
                                        </td>
                                        <td className="px-6 py-4 text-right text-white font-mono">
                                            {formatNumber(quote?.close ?? null)}
                                        </td>
                                        <td className={`px-6 py-4 text-right font-semibold ${getChangeTone(change)}`}>
                                            {change === null
                                                ? '-'
                                                : `${change > 0 ? '+' : ''}${formatNumber(change, 0)}${
                                                          changePercent !== null
                                                              ? ` (${changePercent > 0 ? '+' : ''}${formatNumber(changePercent, 2)}%)`
                                                              : ''
                                                      }`}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <span
                                                className={clsx(
                                                    "px-3 py-1 rounded-full text-xs font-bold ring-1 ring-inset",
                                                    signal.type === 'BUY'
                                                        ? "bg-green-500/10 text-green-400 ring-green-500/30"
                                                        : signal.type === 'SELL'
                                                          ? "bg-red-500/10 text-red-400 ring-red-500/30"
                                                          : "bg-yellow-500/10 text-yellow-400 ring-yellow-500/30"
                                                )}
                                            >
                                                {signal.type}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-gray-300">{signal.reason}</td>
                                        <td className="px-6 py-4 text-center text-white text-sm">
                                            {formatRange(signal.target_price_low, signal.target_price_high)}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <span className="px-2 py-0.5 rounded bg-white/10 text-xs text-text-subtle font-mono">
                                                {signal.horizon}
                                            </span>
                                        </td>
                                    </tr>
                                );
                            })}
                            {(!signals || signals.length === 0) && (
                                <tr>
                                    <td colSpan={8} className="px-6 py-10 text-center text-text-subtle">
                                        관심종목이 없거나 생성된 신호가 없습니다.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
