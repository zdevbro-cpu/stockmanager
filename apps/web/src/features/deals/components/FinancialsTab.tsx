import { useQuery } from '@tanstack/react-query';
import { createApiClient } from '../../../lib/apiClient';
import { useSettings } from '../../../contexts/SettingsContext';
import { ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts';
import clsx from 'clsx';

interface FinancialsProps {
    companyId: number;
}

export default function FinancialsTab({ companyId }: FinancialsProps) {
    const { apiBaseUrl } = useSettings();
    const client = createApiClient(apiBaseUrl);

    // 1. Fetch Main Data (Summary, Ratios, Risks)
    const { data: finData, isLoading } = useQuery({
        queryKey: ['financials', companyId],
        queryFn: async () => {
            const resp = await client.get(`/financials/${companyId}`);
            return resp.data;
        }
    });

    // 2. Fetch Charts (Lazy/Client-side assembly example)
    const { data: chartData } = useQuery({
        queryKey: ['financials_chart', companyId, 'FIN_IS_ANNUAL_3Y'],
        queryFn: async () => {
            const resp = await client.get(`/financials/${companyId}/chart/FIN_IS_ANNUAL_3Y`);
            return resp.data;
        },
        enabled: !!companyId
    });

    if (isLoading) return <div className="p-8 text-center text-gray-500">Loading Financial Analysis...</div>;
    if (!finData) return <div className="p-8 text-center text-gray-500">No Data Available</div>;

    const { summary_3y, ratios_3y, market_actions } = finData;

    return (
        <div className="flex flex-col gap-8 text-white">
            {/* Top Risk Warning Banner (KIND) */}
            {market_actions?.length > 0 && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-start gap-4">
                    <span className="material-symbols-outlined text-red-500 mt-1">warning</span>
                    <div>
                        <h4 className="font-bold text-red-400 mb-2">투자 유의 / 시장 조치 (KIND)</h4>
                        <ul className="list-disc pl-4 space-y-1 text-sm text-gray-300">
                            {market_actions.map((action: any, i: number) => (
                                <li key={i}>
                                    <span className="font-bold text-white">{action.action_type}</span>: {action.reason}
                                    <span className="text-xs text-gray-500 ml-2">({action.start_date}~)</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            )}

            {/* 1. 3-Year Summary & Chart */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-card-dark border border-border-dark rounded-xl p-6">
                    <h3 className="font-bold mb-4 flex items-center gap-2">
                        <span className="material-symbols-outlined text-sm">bar_chart</span>
                        손익 추이 (3개년)
                    </h3>
                    <div className="h-[250px] w-full text-xs">
                        {chartData ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <ComposedChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                    <XAxis dataKey="name" stroke="#9ca3af" tick={{ fontSize: 12 }} />
                                    <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} tickFormatter={(val) => `${(val / 100000000).toLocaleString()}억`} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1a2232', borderColor: '#333', color: '#fff' }}
                                        formatter={(value: any) => [`${(value / 100000000).toLocaleString()}억원`, ""]}
                                    />
                                    <Legend />
                                    <Bar dataKey="매출액" fill="#3b82f6" name="매출액" barSize={40} />
                                    <Line type="monotone" dataKey="영업이익" stroke="#10b981" strokeWidth={2} name="영업이익" dot={{ r: 4 }} />
                                    <Line type="monotone" dataKey="순이익" stroke="#8b5cf6" strokeWidth={2} name="순이익" dot={{ r: 4 }} />
                                </ComposedChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex h-full items-center justify-center text-gray-600">No Chart Data</div>
                        )}
                    </div>
                </div>

                <div className="bg-card-dark border border-border-dark rounded-xl p-6">
                    <h3 className="font-bold mb-4">재무상태 요약 (단위: 억원)</h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-right">
                            <thead className="text-gray-400 border-b border-gray-700">
                                <tr>
                                    <th className="py-2 text-left bg-gray-800/50 pl-2">구분</th>
                                    {summary_3y.map((row: any) => (
                                        <th key={row.fiscal_year} className="py-2 px-2">{row.fiscal_year}년</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-800">
                                <tr>
                                    <td className="py-3 text-left font-bold text-gray-300 pl-2">자산</td>
                                    {summary_3y.map((row: any) => (
                                        <td key={row.fiscal_year} className="py-3 px-2">{(row.assets / 100000000).toLocaleString()}</td>
                                    ))}
                                </tr>
                                <tr>
                                    <td className="py-3 text-left font-bold text-gray-300 pl-2">부채</td>
                                    {summary_3y.map((row: any) => (
                                        <td key={row.fiscal_year} className="py-3 px-2">{(row.liabilities / 100000000).toLocaleString()}</td>
                                    ))}
                                </tr>
                                <tr className="bg-blue-500/5">
                                    <td className="py-3 text-left font-bold text-blue-300 pl-2">자본</td>
                                    {summary_3y.map((row: any) => (
                                        <td key={row.fiscal_year} className="py-3 px-2 font-bold text-blue-400">{(row.equity / 100000000).toLocaleString()}</td>
                                    ))}
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* 2. Key Ratios */}
            <div className="bg-card-dark border border-border-dark rounded-xl p-6">
                <h3 className="font-bold mb-4 flex items-center gap-2">
                    <span className="material-symbols-outlined text-sm">percent</span>
                    핵심 투자 지표 (Ratios)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {ratios_3y.map((row: any) => (
                        <div key={row.fiscal_year} className="bg-white/5 rounded-lg p-4">
                            <div className="text-center font-bold text-lg mb-2 text-gray-300">{row.fiscal_year}</div>
                            <div className="space-y-3">
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-400">영업이익률 (OPM)</span>
                                    <span className={clsx("font-bold", row.op_margin > 0 ? "text-green-400" : "text-red-400")}>
                                        {row.op_margin}%
                                    </span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-400">ROE</span>
                                    <span className="font-bold text-blue-400">{row.roe}%</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-gray-400">부채비율</span>
                                    <span className={clsx("font-bold", row.debt_ratio > 200 ? "text-red-400" : "text-gray-200")}>
                                        {row.debt_ratio}%
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
