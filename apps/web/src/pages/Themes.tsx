import { useState } from 'react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { useAllThemes } from '../hooks/useStockData';

export default function Themes() {
    const { data: themes, isLoading } = useAllThemes();

    return (
        <div className="max-w-7xl mx-auto flex flex-col gap-6">
            <div className="flex items-center justify-between mb-2">
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    <Link to="/" className="text-text-subtle hover:text-white material-symbols-outlined">
                        arrow_back
                    </Link>
                    테마별 시세
                </h2>
                <span className="text-sm text-text-subtle">전체 테마 목록</span>
            </div>

            <div className="bg-card-dark border border-border-dark rounded-xl p-6">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="text-text-subtle border-b border-border-dark">
                                <th className="text-left py-4 font-bold">테마명</th>
                                <th className="text-center py-4 font-bold">전일대비</th>
                                <th className="text-center py-4 font-bold">최근3일 등락률(평균)</th>
                                <th className="text-center py-4 font-bold">전일대비 등락현황</th>
                                <th className="text-left py-4 font-bold pl-8">주도주</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark/50">
                            {isLoading ? (
                                <tr><td colSpan={5} className="py-8 text-center text-text-subtle">Loading...</td></tr>
                            ) : themes?.map((theme: any, i: number) => (
                                <tr key={i} className="hover:bg-white/5 transition-colors">
                                    <td className="py-4 text-white font-bold text-base">{theme.name}</td>
                                    <td className={clsx("py-4 text-center font-bold", theme.changePercent.includes('+') ? "text-red-500" : "text-blue-500")}>
                                        {theme.changePercent}
                                    </td>
                                    <td className={clsx("py-4 text-center", theme.change3d?.includes('+') ? "text-red-400" : "text-blue-400")}>
                                        {theme.change3d || '-'}
                                    </td>
                                    <td className="py-4 text-center">
                                        {/* Mock Data for visual structure */}
                                        <div className="flex items-center justify-center gap-4 text-xs">
                                            <span className="text-text-subtle">상승 <b className="text-red-500">34</b></span>
                                            <span className="text-text-subtle">보합 <b>2</b></span>
                                            <span className="text-text-subtle">하락 <b className="text-blue-500">5</b></span>
                                        </div>
                                    </td>
                                    <td className="py-4 pl-8">
                                        <div className="flex flex-col gap-1">
                                            <div className="flex items-center gap-2">
                                                <span className="text-red-500 text-[10px]">▲</span>
                                                <span className="text-white hover:underline cursor-pointer">{theme.leadingStock}</span>
                                                <span className="text-red-500 text-xs">+5.4%</span>
                                            </div>
                                            {/* Second leading stock mock */}
                                            <div className="flex items-center gap-2">
                                                <span className="text-red-500 text-[10px]">▲</span>
                                                <span className="text-white hover:underline cursor-pointer text-text-subtle">2등주식</span>
                                                <span className="text-red-500 text-xs">+2.1%</span>
                                            </div>
                                        </div>
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
