import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { useAllPopularSearches } from '../hooks/useStockData';

export default function Popular() {
    const { data: popular, isLoading } = useAllPopularSearches();

    return (
        <div className="max-w-7xl mx-auto flex flex-col gap-6">
            <div className="flex items-center justify-between mb-2">
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    <Link to="/" className="text-text-subtle hover:text-white material-symbols-outlined">
                        arrow_back
                    </Link>
                    인기 검색 종목
                </h2>
                <span className="text-sm text-text-subtle">검색 상위 50 종목</span>
            </div>

            <div className="bg-card-dark border border-border-dark rounded-xl p-6">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="text-text-subtle border-b border-border-dark">
                                <th className="text-center py-4 font-bold w-16">순위</th>
                                <th className="text-left py-4 font-bold">종목명</th>
                                <th className="text-right py-4 font-bold">현재가</th>
                                <th className="text-right py-4 font-bold">전일대비</th>
                                <th className="text-right py-4 font-bold">거래량</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark/50">
                            {isLoading ? (
                                <tr><td colSpan={5} className="py-8 text-center text-text-subtle">Loading...</td></tr>
                            ) : popular?.map((item: any, i: number) => (
                                <tr key={item.rank} className="hover:bg-white/5 transition-colors">
                                    <td className="py-4 text-center font-bold text-primary">{item.rank}</td>
                                    <td className="py-4 text-white font-bold text-base">{item.name}</td>
                                    <td className={clsx("py-4 text-right font-bold", item.up ? "text-red-500" : "text-blue-500")}>
                                        {item.price}
                                    </td>
                                    <td className={clsx("py-4 text-right font-bold", item.up ? "text-red-500" : "text-blue-500")}>
                                        {item.changePercent}
                                    </td>
                                    <td className="py-4 text-right text-text-subtle">
                                        {item.volume}
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
