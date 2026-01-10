import { useState } from 'react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useTopIndices, useInvestorTrends, usePopularSearches, useThemeRankings, useIndustryRankings, useRecommendations } from '../hooks/useStockData';

export default function Dashboard() {
    const { data: indices } = useTopIndices();
    const { data: trends } = useInvestorTrends();
    const { data: popular } = usePopularSearches();
    const { data: themes } = useThemeRankings();
    const { data: industries } = useIndustryRankings();

    // Add state for selected market
    const [selectedMarket, setSelectedMarket] = useState('KOSPI');

    // Mock Chart Data Sets (to be replaced with API later)
    const chartDataMap: Record<string, any[]> = {
        'KOSPI': [
            { time: '09:00', value: 2540 }, { time: '09:30', value: 2542 },
            { time: '10:00', value: 2530 }, { time: '10:30', value: 2535 },
            { time: '11:00', value: 2538 }, { time: '11:30', value: 2542 },
            { time: '12:00', value: 2540 }, { time: '12:30', value: 2545 },
            { time: '13:00', value: 2548 }, { time: '13:30', value: 2550 },
            { time: '14:00', value: 2548 }, { time: '14:30', value: 2555 },
            { time: '15:00', value: 2560 }, { time: '15:30', value: 2562 }
        ],
        'KOSDAQ': [
            { time: '09:00', value: 860 }, { time: '09:30', value: 858 },
            { time: '10:00', value: 855 }, { time: '10:30', value: 850 },
            { time: '11:00', value: 852 }, { time: '11:30', value: 855 },
            { time: '12:00', value: 858 }, { time: '12:30', value: 860 },
            { time: '13:00', value: 862 }, { time: '13:30', value: 861 },
            { time: '14:00', value: 863 }, { time: '14:30', value: 865 },
            { time: '15:00', value: 868 }, { time: '15:30', value: 870 }
        ],
        'KOSPI200': [
            { time: '09:00', value: 338 }, { time: '09:30', value: 339 },
            { time: '10:00', value: 337 }, { time: '10:30', value: 338 },
            { time: '11:00', value: 339 }, { time: '11:30', value: 340 },
            { time: '12:00', value: 340 }, { time: '12:30', value: 341 },
            { time: '13:00', value: 342 }, { time: '13:30', value: 342 },
            { time: '14:00', value: 343 }, { time: '14:30', value: 344 },
            { time: '15:00', value: 345 }, { time: '15:30', value: 346 }
        ]
    };

    return (
        <div className="flex flex-col gap-6 max-w-7xl mx-auto">
            {/* Top Section: Indices & popular search */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Left: Indices + Chart (Takes 3 cols on desktop) */}
                <div className="lg:col-span-3 flex flex-col gap-4">
                    {/* Indices Cards */}
                    <div className="grid grid-cols-3 gap-4">
                        {indices?.map((idx: any) => (
                            <div
                                key={idx.name}
                                onClick={() => setSelectedMarket(idx.name)}
                                className={clsx(
                                    "bg-card-dark border p-4 rounded-xl flex flex-col items-center justify-center cursor-pointer transition-all hover:bg-white/5",
                                    selectedMarket === idx.name ? "border-primary ring-1 ring-primary" : "border-border-dark"
                                )}
                            >
                                <span className="text-text-subtle font-bold text-sm tracking-wide mb-1">{idx.name}</span>
                                <span className={clsx("text-2xl font-bold", idx.up ? "text-red-500" : "text-blue-500")}>{idx.value}</span>
                                <div className="flex items-center gap-1 text-sm font-medium mt-1">
                                    <span className={clsx("material-symbols-outlined text-[16px]", idx.up ? "text-red-500" : "text-blue-500")}>
                                        {idx.up ? 'arrow_upward' : 'arrow_downward'}
                                    </span>
                                    <span className={idx.up ? "text-red-500" : "text-blue-500"}>{idx.change} ({idx.changePercent})</span>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Chart & Market Summary Section */}
                    {/* Size adjusted to match visual requirements */}
                    <div className="bg-card-dark border border-border-dark rounded-xl p-5 min-h-[480px] flex flex-col relative">
                        {/* Header: Title & Investor Trends */}
                        <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-6 gap-4">
                            <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                시장 종합 ({selectedMarket})
                                <span className={clsx("text-sm font-medium", indices?.find((i: any) => i.name === selectedMarket)?.up ? "text-red-500" : "text-blue-500")}>
                                    {indices?.find((i: any) => i.name === selectedMarket)?.value}
                                    <span className="ml-1 text-xs">{indices?.find((i: any) => i.name === selectedMarket)?.changePercent}</span>
                                </span>
                            </h3>

                            {/* Investor Legend */}
                            <div className="flex gap-4 text-xs sm:text-sm font-medium bg-background-dark/30 p-2 rounded-lg border border-border-dark/50">
                                {trends?.map((t: any) => (
                                    <div key={t.type} className="flex items-center gap-1.5">
                                        <div className={clsx("w-2 h-2 rounded-sm",
                                            t.type === '개인' ? 'bg-green-500' :
                                                t.type === '외국인' ? 'bg-orange-500' : 'bg-blue-500'
                                        )}></div>
                                        <span className="text-text-subtle">{t.type}</span>
                                        <span className={t.up ? "text-red-400 font-bold" : "text-blue-400 font-bold"}>{t.value}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Chart Area */}
                        <div className="flex-1 w-full min-h-[250px] relative">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={chartDataMap[selectedMarket] || chartDataMap['KOSPI']}>
                                    <defs>
                                        <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor={selectedMarket === 'KOSPI' ? '#EF4444' : '#3B82F6'} stopOpacity={0.1} />
                                            <stop offset="95%" stopColor={selectedMarket === 'KOSPI' ? '#EF4444' : '#3B82F6'} stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                    <XAxis dataKey="time" stroke="#666" fontSize={11} tickLine={false} axisLine={false} />
                                    <YAxis domain={['auto', 'auto']} stroke="#666" fontSize={11} tickLine={false} axisLine={false} orientation="right" />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1E1E1E', borderColor: '#333' }}
                                        itemStyle={{ color: '#fff' }}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="value"
                                        stroke={selectedMarket === 'KOSPI' ? '#EF4444' : '#3B82F6'}
                                        fillOpacity={1}
                                        fill="url(#colorValue)"
                                        strokeWidth={2}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Bottom Stats Grid (Mimicking Naver Finance) */}
                        <div className="mt-4 grid grid-cols-4 gap-0 border-t border-border-dark divide-x divide-border-dark bg-background-dark/30 rounded-b-lg overflow-hidden text-xs sm:text-sm">
                            {/* Up/Down Counts */}
                            <div className="p-3 flex flex-col items-center justify-center gap-1">
                                <span className="text-text-subtle font-medium">등락 종목</span>
                                <div className="flex items-center gap-2">
                                    <span className="text-red-500 font-bold flex items-center gap-0.5">↑ 450</span>
                                    <span className="text-text-subtle">/</span>
                                    <span className="text-blue-500 font-bold flex items-center gap-0.5">↓ 320</span>
                                </div>
                            </div>
                            {/* Program Trading */}
                            <div className="p-3 flex flex-col items-center justify-center gap-1">
                                <span className="text-text-subtle font-medium">프로그램</span>
                                <span className="text-red-400 font-bold">+1,240억</span>
                            </div>
                            {/* Net Trading */}
                            <div className="p-3 flex flex-col items-center justify-center gap-1">
                                <span className="text-text-subtle font-medium">차익</span>
                                <span className="text-blue-400 font-bold">-450억</span>
                            </div>
                            {/* Non-Net Trading */}
                            <div className="p-3 flex flex-col items-center justify-center gap-1">
                                <span className="text-text-subtle font-medium">비차익</span>
                                <span className="text-red-400 font-bold">+890억</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right: Popular Searches */}
                <div className="bg-card-dark border border-border-dark rounded-xl p-4 flex flex-col min-h-[480px]">
                    <div className="flex items-center justify-between mb-4 pb-2 border-b border-border-dark">
                        <h3 className="text-white font-bold">인기 검색 종목</h3>
                        <Link to="/popular" className="text-xs text-text-subtle hover:text-white">더보기</Link>
                    </div>
                    <ul className="flex flex-col gap-2 overflow-y-auto">
                        {popular?.map((item: any) => (
                            <li key={item.rank} className="flex items-center justify-between py-1.5 hover:bg-white/5 px-2 rounded cursor-pointer transition-colors">
                                <div className="flex items-center gap-3">
                                    <span className="w-5 text-center text-sm font-bold text-primary">{item.rank}</span>
                                    <span className="text-white text-sm font-medium">{item.name}</span>
                                </div>
                                <div className={clsx("text-sm font-bold", item.up ? "text-red-500" : "text-blue-500")}>
                                    {item.price}
                                    <span className="text-[10px] ml-1">{item.up ? '▲' : '▼'}</span>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>
            </div>

            {/* Middle Section: Themes & Industries */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Themes */}
                <div className="bg-card-dark border border-border-dark rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4 border-l-4 border-primary pl-3">
                        <h3 className="text-lg font-bold text-white">테마별 시세</h3>
                        <Link to="/themes" className="text-xs text-text-subtle hover:text-white flex items-center gap-1">
                            더보기 <span className="material-symbols-outlined text-[14px]">chevron_right</span>
                        </Link>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="text-text-subtle border-b border-border-dark">
                                    <th className="text-left py-2 font-medium">테마명</th>
                                    <th className="text-right py-2 font-medium">전일대비</th>
                                    <th className="text-right py-2 font-medium">최근3일</th>
                                    <th className="text-right py-2 font-medium">주도주</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border-dark/50">
                                {themes?.map((theme: any, i: number) => (
                                    <tr key={i} className="hover:bg-white/5 transition-colors">
                                        <td className="py-3 text-white font-medium">{theme.name}</td>
                                        <td className="py-3 text-right text-red-500 font-bold">{theme.changePercent}</td>
                                        <td className="py-3 text-right text-text-subtle">{theme.change3d}</td>
                                        <td className="py-3 text-right text-white">{theme.leadingStock}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Industries */}
                <div className="bg-card-dark border border-border-dark rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4 border-l-4 border-primary pl-3">
                        <h3 className="text-lg font-bold text-white">업종별 시세</h3>
                        <Link to="/industries" className="text-xs text-text-subtle hover:text-white flex items-center gap-1">
                            더보기 <span className="material-symbols-outlined text-[14px]">chevron_right</span>
                        </Link>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="text-text-subtle border-b border-border-dark">
                                    <th className="text-left py-2 font-medium">업종명</th>
                                    <th className="text-right py-2 font-medium">전일대비</th>
                                    <th className="text-center py-2 font-medium">상승/보합/하락</th>
                                    <th className="text-right py-2 font-medium">그래프</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border-dark/50">
                                {industries?.map((ind: any, i: number) => (
                                    <tr key={i} className="hover:bg-white/5 transition-colors">
                                        <td className="py-3 text-white font-medium">{ind.name}</td>
                                        <td className="py-3 text-right text-red-500 font-bold">{ind.change}</td>
                                        <td className="py-3 text-center text-text-subtle text-xs">
                                            <span className="text-red-400">{ind.up}</span> / <span>{ind.flat}</span> / <span className="text-blue-400">{ind.down}</span>
                                        </td>
                                        <td className="py-3 text-right">
                                            <div className="h-1.5 w-16 bg-border-dark rounded-full ml-auto overflow-hidden">
                                                <div className="h-full bg-red-500" style={{ width: '70%' }}></div>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
