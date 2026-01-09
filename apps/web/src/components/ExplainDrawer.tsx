import { useEffect, useRef } from 'react';
import clsx from 'clsx';
import { RECOMENDATIONS } from '../lib/mockData';

interface ExplainDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    data: typeof RECOMENDATIONS[0] | null;
}

export default function ExplainDrawer({ isOpen, onClose, data }: ExplainDrawerProps) {
    const drawerRef = useRef<HTMLDivElement>(null);

    // Close on escape
    useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [onClose]);

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
                            {data.name}
                            <span className="text-sm font-normal text-text-subtle">({data.ticker})</span>
                        </h2>
                        <span className={clsx(
                            "text-xs font-bold px-2 py-0.5 rounded",
                            data.target === 'BUY' ? "bg-green-500/20 text-green-500" : "bg-yellow-500/20 text-yellow-500"
                        )}>
                            {data.target} Signal
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
                                <p className="text-2xl font-bold text-primary">{data.score}</p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-400">Target Weight</p>
                                <p className="text-2xl font-bold text-white">{data.weight}</p>
                            </div>
                        </div>
                    </div>

                    {/* Contributing Factors (Mock) */}
                    <div>
                        <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                            <span className="material-symbols-outlined text-primary">fact_check</span>
                            기여 요인 (Alpha Factors)
                        </h3>
                        <div className="flex flex-col gap-2">
                            {/* Mock Item 1 */}
                            <div className="flex justify-between items-center p-3 rounded-lg bg-white/5 hover:bg-white/10">
                                <span className="text-sm text-gray-300">기관 수급 모멘텀</span>
                                <span className="text-sm font-bold text-green-400">+12.5</span>
                            </div>
                            {/* Mock Item 2 */}
                            <div className="flex justify-between items-center p-3 rounded-lg bg-white/5 hover:bg-white/10">
                                <span className="text-sm text-gray-300">이익 전망치 상향</span>
                                <span className="text-sm font-bold text-green-400">+8.2</span>
                            </div>
                            {/* Mock Item 3 */}
                            <div className="flex justify-between items-center p-3 rounded-lg bg-white/5 hover:bg-white/10">
                                <span className="text-sm text-gray-300">밸류에이션 부담</span>
                                <span className="text-sm font-bold text-red-400">-4.0</span>
                            </div>
                        </div>
                    </div>

                    {/* Constraints / Risks */}
                    <div>
                        <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                            <span className="material-symbols-outlined text-yellow-500">warning</span>
                            리스크 및 제약조건
                        </h3>
                        <div className="p-3 rounded-lg border border-yellow-500/20 bg-yellow-500/5 text-sm text-yellow-200">
                            단기 과매수 구간 진입 가능성 존재 (RSI &gt; 70)
                        </div>
                    </div>

                    {/* JSON View (Collapsible) */}
                    <div className="pt-4 border-t border-border-dark">
                        <details className="group">
                            <summary className="flex items-center gap-2 cursor-pointer text-xs text-text-subtle hover:text-white font-mono list-none">
                                <span className="material-symbols-outlined text-[16px] transition-transform group-open:rotate-90">chevron_right</span>
                                View Raw JSON
                            </summary>
                            <pre className="mt-2 p-3 rounded bg-black/50 text-xs text-green-400 overflow-x-auto font-mono">
                                {JSON.stringify(data, null, 2)}
                            </pre>
                        </details>
                    </div>
                </div>

                <div className="p-4 border-t border-border-dark bg-card-dark">
                    <button className="w-full py-3 rounded-lg bg-primary hover:bg-blue-600 text-white font-bold transition-colors">
                        Add to Watchlist
                    </button>
                </div>
            </div>
        </div>
    );
}
