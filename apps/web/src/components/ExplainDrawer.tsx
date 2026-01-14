import { useEffect, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { RECOMENDATIONS } from '../lib/mockData';
import { useWatchlist } from '../hooks/useWatchlist';

interface ExplainDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    data: typeof RECOMENDATIONS[0] | null;
}

export default function ExplainDrawer({ isOpen, onClose, data }: ExplainDrawerProps) {
    const drawerRef = useRef<HTMLDivElement>(null);
    const { watchlist, addStock } = useWatchlist();
    const navigate = useNavigate();

    // Close on escape
    useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [onClose]);

    const safeData: any = data ?? {};
    const weightValue = safeData.weight ?? safeData.target_weight;
    const formattedWeight = typeof weightValue === 'number'
        ? `${(weightValue <= 1 ? weightValue * 100 : weightValue).toFixed(1)}%`
        : (weightValue ?? '-');
    const signal = safeData.target ?? safeData.signal ?? safeData.rationale?.signal ?? 'N/A';
    const displayName = safeData.name ?? safeData.name_ko ?? '-';
    const rationale = safeData.rationale ?? null;
    const formattedScore = typeof safeData.score === 'number' ? safeData.score.toFixed(3) : safeData.score ?? '-';
    const formatNumber = (value?: number | null) => {
        if (value === null || value === undefined) return '-';
        return Number(value).toLocaleString('en-US');
    };
    const targetRange = safeData.target_price_low && safeData.target_price_high
        ? `${formatNumber(safeData.target_price_low)} ~ ${formatNumber(safeData.target_price_high)}`
        : '-';
    const targetBasis = safeData.target_price_basis?.basis ?? null;
    const alreadyAdded = useMemo(() => {
        return !!safeData.ticker && watchlist.some(item => item.ticker === safeData.ticker);
    }, [watchlist, safeData.ticker]);
    const contribs = useMemo(() => {
        const items = rationale?.factors?.contrib;
        return Array.isArray(items) ? items : [];
    }, [rationale]);
    const filterRules = useMemo(() => {
        const items = rationale?.filters?.rules;
        return Array.isArray(items) ? items : [];
    }, [rationale]);
    const riskFlags = useMemo(() => {
        const items = rationale?.event_risk?.flags;
        return Array.isArray(items) ? items : [];
    }, [rationale]);

    if (!isOpen || !data) return null;

    return (
        <div className="fixed inset-0 z-[60] flex justify-end">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            ></div>

            {/* Drawer */}
            <div
                ref={drawerRef}
                className="relative w-full max-w-md h-full bg-background-dark border-l border-border-dark shadow-2xl flex flex-col transform transition-transform duration-300"
            >
                <div className="flex items-center justify-between p-4 border-b border-border-dark bg-card-dark">
                    <div>
                        <h2 className="text-lg font-bold text-white flex items-center gap-2">
                            {displayName}
                            <span className="text-sm font-normal text-text-subtle">({safeData.ticker})</span>
                        </h2>
                        <span className={clsx(
                            "text-xs font-bold px-2 py-0.5 rounded",
                            signal === 'BUY' ? "bg-green-500/20 text-green-500" : "bg-yellow-500/20 text-yellow-500"
                        )}>
                            {signal} Signal
                        </span>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors text-white">
                        <span className="material-symbols-outlined">close</span>
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-6">
                    {/* Summary Section */}
                    <div className="bg-card-dark rounded-xl p-4 border border-border-dark">
                        <h3 className="text-sm font-bold text-text-subtle mb-3 uppercase tracking-wider">Analysis Summary</h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <p className="text-xs text-gray-400">Total Score</p>
                                <p className="text-2xl font-bold text-primary">{formattedScore}</p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-400">Target Weight</p>
                                <p className="text-2xl font-bold text-white">{formattedWeight}</p>
                            </div>
                        </div>
                        <div className="mt-4">
                            <p className="text-xs text-gray-400">Target Range</p>
                            <p className="text-lg font-bold text-white">{targetRange}</p>
                            {targetBasis && (
                                <p className="text-[11px] text-text-subtle mt-1">Basis: {targetBasis}</p>
                            )}
                        </div>
                    </div>

                    {/* Contributing Factors */}
                    <div>
                        <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                            <span className="material-symbols-outlined text-primary">fact_check</span>
                            Contributing Factors
                        </h3>
                        <div className="flex flex-col gap-2">
                            {contribs.length === 0 ? (
                                <div className="text-sm text-text-subtle">No factor details available.</div>
                            ) : contribs.map((item: any) => (
                                <div key={`${item.factor}-${item.contribution}`} className="flex justify-between items-center p-3 rounded-lg bg-white/5 hover:bg-white/10">
                                    <span className="text-sm text-gray-300">{item.factor}</span>
                                    <span className={clsx(
                                        "text-sm font-bold",
                                        Number(item.contribution) >= 0 ? "text-green-400" : "text-red-400"
                                    )}>
                                        {Number(item.contribution).toFixed(3)}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Constraints / Risks */}
                    <div>
                        <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                            <span className="material-symbols-outlined text-yellow-500">warning</span>
                            Constraints / Risks
                        </h3>
                        {filterRules.length === 0 && riskFlags.length === 0 ? (
                            <div className="p-3 rounded-lg border border-yellow-500/20 bg-yellow-500/5 text-sm text-yellow-200">
                                No constraint details available.
                            </div>
                        ) : (
                            <div className="flex flex-col gap-2">
                                {filterRules.map((rule: any) => (
                                    <div key={rule.name} className="p-3 rounded-lg border border-yellow-500/20 bg-yellow-500/5 text-sm text-yellow-200">
                                        {rule.name}: {rule.passed ? 'PASS' : 'FAIL'} (value {rule.value}, threshold {rule.threshold})
                                    </div>
                                ))}
                                {riskFlags.map((flag: any) => (
                                    <div key={flag} className="p-3 rounded-lg border border-yellow-500/20 bg-yellow-500/5 text-sm text-yellow-200">
                                        Risk: {flag}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* JSON View (Collapsible) */}
                    <div className="pt-4 border-t border-border-dark">
                        <details className="group">
                            <summary className="flex items-center gap-2 cursor-pointer text-xs text-text-subtle hover:text-white font-mono list-none">
                                <span className="material-symbols-outlined text-[16px] transition-transform group-open:rotate-90">chevron_right</span>
                                View Raw JSON
                            </summary>
                            <pre className="mt-2 p-3 rounded bg-black/50 text-xs text-green-400 overflow-x-auto font-mono">
                                {JSON.stringify(rationale ?? data, null, 2)}
                            </pre>
                        </details>
                    </div>
                </div>

                <div className="p-4 border-t border-border-dark bg-card-dark">
                    <button
                        onClick={() => {
                            addStock(data.ticker, displayName);
                            onClose();
                            navigate('/recommendations');
                        }}
                        disabled={alreadyAdded}
                        className={clsx(
                            "w-full py-3 rounded-lg font-bold transition-colors",
                            alreadyAdded ? "bg-gray-700 text-gray-300 cursor-not-allowed" : "bg-primary hover:bg-blue-600 text-white"
                        )}
                    >
                        {alreadyAdded ? 'Added to Watchlist' : 'Add to Watchlist'}
                    </button>
                </div>
            </div>
        </div>
    );
}
