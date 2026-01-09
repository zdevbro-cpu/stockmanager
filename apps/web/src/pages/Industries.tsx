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
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="text-text-subtle border-b border-border-dark">
                                <th className="text-left py-4 font-bold w-1/4">업종명</th>
                                <th className="text-center py-4 font-bold w-1/6">전일대비</th>
                                <th className="text-center py-4 font-bold w-1/3">
                                    <div className="flex flex-col">
                                        <span>전일대비 등락현황</span>
                                        <div className="grid grid-cols-4 text-xs font-normal mt-1 text-text-subtle border-t border-border-dark/50 pt-1">
                                            <span>전체</span>
                                            <span>상승</span>
                                            <span>보합</span>
                                            <span>하락</span>
                                        </div>
                                    </div>
                                </th>
                                <th className="text-right py-4 font-bold">등락그래프</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark/50">
                            {isLoading ? (
                                <tr><td colSpan={4} className="py-8 text-center text-text-subtle">Loading...</td></tr>
                            ) : industries?.map((ind: any, i: number) => (
                                <tr key={i} className="hover:bg-white/5 transition-colors">
                                    <td className="py-4 text-white font-bold text-base">{ind.name}</td>
                                    <td className={clsx("py-4 text-center font-bold", ind.change?.includes('+') ? "text-red-500" : "text-blue-500")}>
                                        {ind.change}
                                    </td>
                                    <td className="py-4">
                                        <div className="grid grid-cols-4 text-center text-sm">
                                            <span className="text-white font-medium">{ind.up + ind.flat + ind.down}</span>
                                            <span className="text-red-500">{ind.up}</span>
                                            <span className="text-text-subtle">{ind.flat}</span>
                                            <span className="text-blue-500">{ind.down}</span>
                                        </div>
                                    </td>
                                    <td className="py-4 text-right">
                                        <div className="h-2 w-32 bg-border-dark rounded-full ml-auto overflow-hidden">
                                            <div
                                                className={clsx("h-full", ind.change?.includes('+') ? "bg-red-500" : "bg-blue-500")}
                                                style={{ width: `${Math.random() * 60 + 20}%` }}
                                            ></div>
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
