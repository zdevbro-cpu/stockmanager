import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useTopIndices, useInvestorTrends, usePopularSearches, useThemeRankings, useIndustryRankings, useIndexChart, useFxRate, useMarketBreadth } from '../hooks/useStockData';

export default function Dashboard() {
    const { data: indices } = useTopIndices();
    const { data: fxRate } = useFxRate();
    const { data: breadth } = useMarketBreadth();
    const { data: trends } = useInvestorTrends();
    const [deferSections, setDeferSections] = useState(false);
    const { data: popular } = usePopularSearches({
        enabled: deferSections,
        staleTime: 3600000,
        refetchInterval: 3600000,
        refetchOnWindowFocus: false,
    });
    const { data: themes } = useThemeRankings({
        enabled: deferSections,
        staleTime: 300000,
        refetchInterval: 300000,
        refetchOnWindowFocus: false,
    });
    const { data: industries } = useIndustryRankings({
        enabled: deferSections,
        staleTime: 300000,
        refetchInterval: 300000,
        refetchOnWindowFocus: false,
    });

    const [selectedMarket, setSelectedMarket] = useState('KOSPI');
    useEffect(() => {
        const timer = setTimeout(() => setDeferSections(true), 0);
        return () => clearTimeout(timer);
    }, []);

    const { data: indexChart } = useIndexChart(selectedMarket);
    const chartData = Array.isArray(indexChart)
        ? indexChart.map((item: any) => ({
            time: item.date,
            value: item.value,
        }))
        : [];
    const chartDataWithFallback = chartData.length === 1
        ? [
            { time: `${chartData[0].time} 09:00`, value: chartData[0].value },
            { time: `${chartData[0].time} 15:30`, value: chartData[0].value },
        ]
        : chartData;
    const formatChartTick = (value: string) => {
        if (!value) return value;
        if (value.includes(' ')) {
            const parts = value.split(' ');
            return parts[parts.length - 1];
        }
        return value;
    };

    return (
        <div className="flex flex-col gap-6 max-w-7xl mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                <div className="lg:col-span-3 flex flex-col gap-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {indices?.map((idx: any) => (
                            <div
                                key={idx.name}
                                onClick={() => setSelectedMarket(idx.name)}
                                className={clsx(
                                    'bg-card-dark border p-4 rounded-xl flex flex-col items-center justify-center cursor-pointer transition-all hover:bg-white/5',
                                    selectedMarket === idx.name ? 'border-primary ring-1 ring-primary' : 'border-border-dark'
                                )}
                            >
                                <span className="text-text-subtle font-bold text-sm tracking-wide mb-1">{idx.name}</span>
                                <span className={clsx('text-2xl font-bold', idx.up ? 'text-red-500' : 'text-blue-500')}>{idx.value}</span>
                                <div className="flex items-center gap-1 text-sm font-medium mt-1">
                                    <span className={clsx('material-symbols-outlined text-[16px]', idx.up ? 'text-red-500' : 'text-blue-500')}>
                                        {idx.up ? 'arrow_upward' : 'arrow_downward'}
                                    </span>
                                    <span className={idx.up ? 'text-red-500' : 'text-blue-500'}>{idx.change} ({idx.changePercent})</span>
                                </div>
                            </div>
                        ))}
                        <div className="bg-card-dark border border-border-dark p-4 rounded-xl flex flex-col items-center justify-center">
                            <span className="text-text-subtle font-bold text-sm tracking-wide mb-1">USD/KRW</span>
                            <span className="text-2xl font-bold text-white">
                                {fxRate?.value ? Number(fxRate.value).toLocaleString('en-US') : '-'}
                            </span>
                            <div className="flex items-center gap-1 text-xs text-text-subtle mt-1">
                                <span>{fxRate?.date ?? '-'}</span>
                            </div>
                        </div>
                    </div>

                    <div className="bg-card-dark border border-border-dark rounded-xl p-5 min-h-[480px] flex flex-col relative">
                        <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-6 gap-4">
                            <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                시장 종합 ({selectedMarket})
                                <span className={clsx('text-sm font-medium', indices?.find((i: any) => i.name === selectedMarket)?.up ? 'text-red-500' : 'text-blue-500')}>
                                    {indices?.find((i: any) => i.name === selectedMarket)?.value}
                                    <span className="ml-1 text-xs">{indices?.find((i: any) => i.name === selectedMarket)?.changePercent}</span>
                                </span>
                            </h3>
                            <div className="flex gap-4 text-xs sm:text-sm font-medium bg-background-dark/30 p-2 rounded-lg border border-border-dark/50">
                                {trends?.map((t: any, idx: number) => {
                                    const dotColors = ['bg-green-500', 'bg-orange-500', 'bg-blue-500'];
                                    return (
                                        <div key={`${t.type}-${idx}`} className="flex items-center gap-1.5">
                                            <div className={clsx('w-2 h-2 rounded-sm', dotColors[idx % dotColors.length])}></div>
                                            <span className="text-text-subtle">{t.type}</span>
                                            <span className={t.up ? 'text-red-400 font-bold' : 'text-blue-400 font-bold'}>{t.value}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        <div className="flex-1 w-full min-h-[250px] relative">
                            {chartDataWithFallback.length === 0 ? (
                                <div className="h-full flex items-center justify-center text-sm text-text-subtle">
                                    차트 데이터가 없습니다.
                                </div>
                            ) : (
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={chartDataWithFallback}>
                                        <defs>
                                            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor={selectedMarket === 'KOSPI' ? '#EF4444' : '#3B82F6'} stopOpacity={0.1} />
                                                <stop offset="95%" stopColor={selectedMarket === 'KOSPI' ? '#EF4444' : '#3B82F6'} stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                        <XAxis
                                            dataKey="time"
                                            stroke="#666"
                                            fontSize={11}
                                            tickLine={false}
                                            axisLine={false}
                                            tickFormatter={formatChartTick}
                                        />
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
                            )}
                        </div>

                        <div className="mt-4 grid grid-cols-4 gap-0 border-t border-border-dark divide-x divide-border-dark bg-background-dark/30 rounded-b-lg overflow-hidden text-xs sm:text-sm">
                            <div className="p-3 flex flex-col items-center justify-center gap-1">
                                <span className="text-text-subtle font-medium">등락 종목</span>
                                <div className="flex items-center gap-2">
                                    <span className="text-red-500 font-bold flex items-center gap-0.5">상승 {breadth?.up ?? '-'}</span>
                                    <span className="text-text-subtle">/</span>
                                    <span className="text-blue-500 font-bold flex items-center gap-0.5">하락 {breadth?.down ?? '-'}</span>
                                </div>
                            </div>
                            <div className="p-3 flex flex-col items-center justify-center gap-1">
                                <span className="text-text-subtle font-medium">프로그램</span>
                                <span className="text-text-subtle font-bold">{breadth?.program_net_krw ?? '-'}</span>
                            </div>
                            <div className="p-3 flex flex-col items-center justify-center gap-1">
                                <span className="text-text-subtle font-medium">차익</span>
                                <span className="text-text-subtle font-bold">{breadth?.arbitrage_net_krw ?? '-'}</span>
                            </div>
                            <div className="p-3 flex flex-col items-center justify-center gap-1">
                                <span className="text-text-subtle font-medium">비차익</span>
                                <span className="text-text-subtle font-bold">{breadth?.non_arbitrage_net_krw ?? '-'}</span>
                            </div>
                        </div>
                    </div>
                </div>

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
                                <div className={clsx('text-sm font-bold', item.up ? 'text-red-500' : 'text-blue-500')}>
                                    {item.price}
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-card-dark border border-border-dark rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4 border-l-4 border-primary pl-3">
                        <h3 className="text-lg font-bold text-white">테마별 시세</h3>
                        <Link to="/themes" className="text-xs text-text-subtle hover:text-white flex items-center gap-1">
                            더보기<span className="material-symbols-outlined text-[14px]">chevron_right</span>
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

                <div className="bg-card-dark border border-border-dark rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4 border-l-4 border-primary pl-3">
                        <h3 className="text-lg font-bold text-white">업종별 시세</h3>
                        <Link to="/industries" className="text-xs text-text-subtle hover:text-white flex items-center gap-1">
                            더보기<span className="material-symbols-outlined text-[14px]">chevron_right</span>
                        </Link>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="text-text-subtle border-b border-border-dark">
                                    <th className="text-left py-2 font-medium">업종명</th>
                                    <th className="text-right py-2 font-medium">전일대비</th>
                                    <th className="text-center py-2 font-medium">상승/보합/하락</th>
                                    <th className="text-right py-2 font-medium">주도주</th>
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
                                        <td className="py-3 text-right text-text-subtle">
                                            {ind.leadingStock ?? '-'}
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
