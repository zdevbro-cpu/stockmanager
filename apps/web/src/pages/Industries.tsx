import { useState } from 'react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { useAllIndustries } from '../hooks/useStockData';

export default function Industries() {
    const { data: industries, isLoading } = useAllIndustries();

    return (
        <div className="max-w-7xl mx-auto flex flex-col gap-6">
            <div className="flex items-center justify-between mb-2">
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    <Link to="/" className="text-text-subtle hover:text-white material-symbols-outlined">
                        arrow_back
                    </Link>
                    업종별 시세
                </h2>
                <span className="text-sm text-text-subtle">전체 업종 목록</span>
            </div>

            <div className="bg-card-dark border border-border-dark rounded-xl p-6">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm table-fixed">
                        <thead>
                            <tr className="text-text-subtle border-b border-border-dark">
                                <th className="text-left py-4 font-bold w-56">업종명</th>
                                <th className="text-center py-4 font-bold w-28">전일대비</th>
                                <th className="text-center py-4 font-bold w-36">최근3일 등락률(평균)</th>
                                <th className="text-center py-4 font-bold w-44">전일대비 등락현황</th>
                                <th className="text-left py-4 font-bold w-52 pl-4">주도주</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark/50">
                            {isLoading ? (
                                <tr><td colSpan={5} className="py-8 text-center text-text-subtle">Loading...</td></tr>
                            ) : industries?.map((ind: any, i: number) => {
                                const change3d = ind.change3d || ind.change || '-';
                                return (
                                    <tr key={i} className="hover:bg-white/5 transition-colors">
                                        <td className="py-4 text-white font-bold text-base">{ind.name}</td>
                                        <td className={clsx('py-4 text-center font-bold', ind.change?.includes('+') ? 'text-red-500' : 'text-blue-500')}>
                                            {ind.change}
                                        </td>
                                        <td className={clsx("py-4 text-center", change3d?.includes('+') ? "text-red-400" : "text-blue-400")}>
                                            {change3d}
                                        </td>
                                        <td className="py-4 text-center">
                                            <div className="flex items-center justify-center gap-4 text-xs">
                                                <span className="text-text-subtle">상승 <b className="text-red-500">{ind.up ?? '-'}</b></span>
                                                <span className="text-text-subtle">보합 <b>{ind.flat ?? '-'}</b></span>
                                                <span className="text-text-subtle">하락 <b className="text-blue-500">{ind.down ?? '-'}</b></span>
                                            </div>
                                        </td>
                                        <td className="py-4 pl-4">
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-red-500 text-[10px]">▲</span>
                                                    <span className="text-white hover:underline cursor-pointer break-words">{ind.leadingStock ?? '-'}</span>
                                                    <span className="text-text-subtle text-xs">{ind.leadingStockChange ?? '-'}</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-red-500 text-[10px]">▲</span>
                                                    <span className="text-white hover:underline cursor-pointer text-text-subtle">2등주식</span>
                                                    <span className="text-text-subtle text-xs">-</span>
                                                </div>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
