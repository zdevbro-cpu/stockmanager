import { useState } from 'react';
import { useRecommendations } from '../hooks/useStockData';
import ExplainDrawer from '../components/ExplainDrawer';
import clsx from 'clsx';

export default function Recommendations() {
    const { data: recommendations } = useRecommendations();
    const [selectedItem, setSelectedItem] = useState<any>(null);

    return (
        <div className="flex flex-col gap-6 max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white">Algorithm Recommendation</h1>
                    <p className="text-text-subtle text-sm mt-1">
                        전략: prod_v1 (v1.0) • 기준일: 2023-10-24
                    </p>
                </div>
                <div className="flex gap-2">
                    <select className="bg-card-dark border border-border-dark text-white text-sm rounded-lg px-3 py-2 outline-none focus:border-primary">
                        <option>prod_v1 (Active)</option>
                        <option>test_v2 (Beta)</option>
                    </select>
                    <button className="bg-card-dark float-right border border-border-dark hover:bg-white/5 text-white p-2 rounded-lg">
                        <span className="material-symbols-outlined">download</span>
                    </button>
                </div>
            </div>

            {/* Table Card */}
            <div className="bg-card-dark border border-border-dark rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-[#151e1d] text-text-subtle border-b border-border-dark">
                            <tr>
                                <th className="px-6 py-4 text-left font-bold w-16">Rank</th>
                                <th className="px-6 py-4 text-left font-bold">Ticker</th>
                                <th className="px-6 py-4 text-left font-bold">Name</th>
                                <th className="px-6 py-4 text-center font-bold">Signal</th>
                                <th className="px-6 py-4 text-right font-bold">Weight</th>
                                <th className="px-6 py-4 text-right font-bold">Score</th>
                                <th className="px-6 py-4 text-right font-bold">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark">
                            {recommendations?.map((item: any) => (
                                <tr key={item.ticker} className="group hover:bg-white/5 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/20 text-primary font-bold text-sm">
                                            {item.rank}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-text-subtle font-mono">{item.ticker}</td>
                                    <td className="px-6 py-4 font-bold text-white">{item.name}</td>
                                    <td className="px-6 py-4 text-center">
                                        <span className={clsx(
                                            "px-2 py-1 rounded text-xs font-bold uppercase",
                                            item.target === 'BUY' ? "text-green-500 bg-green-500/10 border border-green-500/20" :
                                                item.target === 'SELL' ? "text-red-500 bg-red-500/10 border border-red-500/20" :
                                                    "text-yellow-500 bg-yellow-500/10 border border-yellow-500/20"
                                        )}>
                                            {item.target}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right text-lg font-display font-bold text-white">{item.weight}</td>
                                    <td className="px-6 py-4 text-right font-bold text-primary">{item.score}</td>
                                    <td className="px-6 py-4 text-right">
                                        <button
                                            onClick={() => setSelectedItem(item)}
                                            className="px-4 py-2 bg-primary hover:bg-primary/80 text-white rounded-lg text-xs font-bold transition-colors"
                                        >
                                            Explain
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Explain Drawer */}
            <ExplainDrawer
                isOpen={!!selectedItem}
                onClose={() => setSelectedItem(null)}
                data={selectedItem}
            />
        </div>
    );
}
