import { useState } from 'react';
import { useSignals } from '../hooks/useStockData';
import clsx from 'clsx';

export default function Signals() {
    const { data: signals } = useSignals();
    const [horizon, setHorizon] = useState('1D');

    return (
        <div className="flex flex-col gap-6 max-w-7xl mx-auto">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-white">매매신호 (Signals)</h1>

                {/* Horizon Tabs */}
                <div className="flex bg-card-dark border border-border-dark rounded-lg p-1">
                    {['1D', '3D', '1W'].map(h => (
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
                                <th className="px-6 py-4 text-left font-bold">발생일자</th>
                                <th className="px-6 py-4 text-left font-bold">종목 (Ticker)</th>
                                <th className="px-6 py-4 text-center font-bold">유형 (Type)</th>
                                <th className="px-6 py-4 text-right font-bold">현재가</th>
                                <th className="px-6 py-4 text-left font-bold">발생 사유 (Reason)</th>
                                <th className="px-6 py-4 text-center font-bold">Horizon</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark/50">
                            {signals?.map((signal: any, i: number) => (
                                <tr key={i} className="hover:bg-white/5 transition-colors group">
                                    <td className="px-6 py-4 text-text-subtle">{signal.date}</td>
                                    <td className="px-6 py-4">
                                        <div className="flex flex-col">
                                            <span className="text-white font-bold">{signal.name}</span>
                                            <span className="text-xs text-text-subtle">{signal.ticker}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        <span className={clsx(
                                            "px-3 py-1 rounded-full text-xs font-bold ring-1 ring-inset",
                                            signal.type === 'BUY' ? "bg-green-500/10 text-green-400 ring-green-500/30" :
                                                signal.type === 'SELL' ? "bg-red-500/10 text-red-400 ring-red-500/30" :
                                                    "bg-yellow-500/10 text-yellow-400 ring-yellow-500/30"
                                        )}>
                                            {signal.type}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right font-mono text-white">
                                        {signal.price}
                                    </td>
                                    <td className="px-6 py-4 text-gray-300">
                                        {signal.reason}
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        <span className="px-2 py-0.5 rounded bg-white/10 text-xs text-text-subtle font-mono">
                                            {signal.horizon}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
