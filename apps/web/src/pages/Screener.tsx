import { useState } from 'react';
import { INDUSTRY_RANKINGS, RECOMENDATIONS, THEME_RANKINGS } from '../lib/mockData';
import clsx from 'clsx';

// Mock large list for the table
const MOCK_SCREENER_RESULTS = [
    ...RECOMENDATIONS.map(r => ({ ...r, market: 'KOSPI', price: 72000, turnover: 500000000, sector: '반도체' })),
    { rank: 6, ticker: '005490', name: 'POSCO홀딩스', market: 'KOSPI', price: 450000, turnover: 300000000, sector: '철강', target: 'WAIT', score: 60, weight: '0%' },
    { rank: 7, ticker: '035720', name: '카카오', market: 'KOSPI', price: 54300, turnover: 150000000, sector: '서비스', target: 'HOLD', score: 55, weight: '0%' },
    { rank: 8, ticker: '247540', name: '에코프로비엠', market: 'KOSDAQ', price: 280000, turnover: 800000000, sector: '2차전지', target: 'BUY', score: 82, weight: '0%' },
    { rank: 9, ticker: '068270', name: '셀트리온', market: 'KOSPI', price: 180000, turnover: 120000000, sector: '의약품', target: 'WAIT', score: 58, weight: '0%' },
    // Duplicate for scroll
    { rank: 10, ticker: '000270', name: '기아', market: 'KOSPI', price: 95000, turnover: 220000000, sector: '자동차', target: 'BUY', score: 75, weight: '0%' },
];

export default function Screener() {
    const [priceMin, setPriceMin] = useState<string>('');
    const [selectedIndustries, setSelectedIndustries] = useState<string[]>([]);
    const [selectedThemes, setSelectedThemes] = useState<string[]>([]);

    const toggleIndustry = (name: string) => {
        if (selectedIndustries.includes(name)) {
            setSelectedIndustries(selectedIndustries.filter(i => i !== name));
        } else {
            setSelectedIndustries([...selectedIndustries, name]);
        }
    };

    const toggleTheme = (name: string) => {
        if (selectedThemes.includes(name)) {
            setSelectedThemes(selectedThemes.filter(t => t !== name));
        } else {
            setSelectedThemes([...selectedThemes, name]);
        }
    };

    return (
        <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-140px)]">
            {/* Filter Panel (Left) */}
            <aside className="w-full lg:w-72 flex-shrink-0 bg-card-dark border border-border-dark rounded-xl p-4 flex flex-col gap-6 overflow-y-auto">
                <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold text-white">필터 (Filters)</h2>
                    <button className="text-xs text-primary font-bold hover:underline">초기화</button>
                </div>

                {/* Price Filter */}
                <div className="flex flex-col gap-2">
                    <label className="text-sm font-bold text-text-subtle">최소 주가 (KRW)</label>
                    <input
                        type="number"
                        placeholder="예: 10000"
                        value={priceMin}
                        onChange={(e) => setPriceMin(e.target.value)}
                        className="bg-background-dark border border-border-dark rounded-lg px-3 py-2 text-white focus:border-primary outline-none"
                    />
                </div>

                {/* Industry Filter */}
                <div className="flex flex-col gap-2">
                    <label className="text-sm font-bold text-text-subtle">업종 (Industry)</label>
                    <div className="flex flex-col gap-1 max-h-40 overflow-y-auto pr-1">
                        {INDUSTRY_RANKINGS.map((ind) => (
                            <label key={ind.name} className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer hover:text-white">
                                <input
                                    type="checkbox"
                                    className="rounded border-border-dark bg-background-dark text-primary focus:ring-primary"
                                    checked={selectedIndustries.includes(ind.name)}
                                    onChange={() => toggleIndustry(ind.name)}
                                />
                                {ind.name}
                            </label>
                        ))}
                    </div>
                </div>

                {/* Theme Filter */}
                <div className="flex flex-col gap-2">
                    <label className="text-sm font-bold text-text-subtle">테마 (Theme)</label>
                    <div className="flex flex-wrap gap-2">
                        {THEME_RANKINGS.map((theme) => (
                            <button
                                key={theme.name}
                                onClick={() => toggleTheme(theme.name)}
                                className={clsx(
                                    "px-2 py-1 rounded-full text-xs font-medium border transition-colors text-left",
                                    selectedThemes.includes(theme.name)
                                        ? "bg-primary/20 border-primary text-primary"
                                        : "bg-background-dark border-border-dark text-gray-400 hover:border-gray-500"
                                )}
                            >
                                {theme.name}
                            </button>
                        ))}
                    </div>
                </div>
            </aside>

            {/* Results Table (Right) */}
            <main className="flex-1 bg-card-dark border border-border-dark rounded-xl flex flex-col overflow-hidden">
                <div className="p-4 border-b border-border-dark flex items-center justify-between bg-card-dark">
                    <div className="flex items-center gap-2">
                        <span className="text-white font-bold">검색 결과</span>
                        <span className="bg-primary/20 text-primary text-xs font-bold px-2 py-0.5 rounded-full">{MOCK_SCREENER_RESULTS.length}건</span>
                    </div>
                    <div className="flex gap-2">
                        <button className="flex items-center gap-1 text-sm text-text-subtle hover:text-white px-3 py-1.5 border border-border-dark rounded-lg">
                            <span className="material-symbols-outlined text-[18px]">download</span>
                            다운로드
                        </button>
                    </div>
                </div>

                <div className="flex-1 overflow-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="text-text-subtle font-medium bg-background-dark sticky top-0 z-10">
                            <tr>
                                <th className="px-4 py-3 font-bold border-b border-border-dark">종목명 (Ticker)</th>
                                <th className="px-4 py-3 font-bold border-b border-border-dark">시장</th>
                                <th className="px-4 py-3 font-bold border-b border-border-dark">업종</th>
                                <th className="px-4 py-3 font-bold border-b border-border-dark text-right">현재가</th>
                                <th className="px-4 py-3 font-bold border-b border-border-dark text-right">거래일</th>
                                <th className="px-4 py-3 font-bold border-b border-border-dark text-center">신호</th>
                                <th className="px-4 py-3 font-bold border-b border-border-dark text-right">점수</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark/50">
                            {MOCK_SCREENER_RESULTS.map((item, i) => (
                                <tr key={i} className="hover:bg-white/5 transition-colors cursor-pointer text-gray-300">
                                    <td className="px-4 py-3">
                                        <div className="flex flex-col">
                                            <span className="text-white font-bold">{item.name}</span>
                                            <span className="text-text-subtle text-xs">{item.ticker}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3">{item.market}</td>
                                    <td className="px-4 py-3">{item.sector}</td>
                                    <td className="px-4 py-3 text-right font-medium text-white">
                                        {item.price.toLocaleString()}
                                    </td>
                                    <td className="px-4 py-3 text-right text-text-subtle">
                                        {(item.turnover / 100000000).toFixed(1)}억
                                    </td>
                                    <td className="px-4 py-3 text-center">
                                        <span className={clsx(
                                            "px-2 py-1 rounded text-xs font-bold",
                                            item.target === 'BUY' ? "bg-green-500/20 text-green-500" :
                                                item.target === 'SELL' ? "bg-red-500/20 text-red-500" :
                                                    item.target === 'WAIT' ? "bg-yellow-500/20 text-yellow-500" : "bg-gray-700 text-gray-400"
                                        )}>
                                            {item.target || '-'}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-right text-primary font-bold">
                                        {item.score || '-'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </main>
        </div>
    );
}
