import { useEffect, useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useRecommendations, useRecommendationRunStatus, useStrategies } from '../hooks/useStockData';
import ExplainDrawer from '../components/ExplainDrawer';
import clsx from 'clsx';
import { createApiClient } from '../lib/apiClient';
import { useSettings } from '../contexts/SettingsContext';

export default function Recommendations() {
    const { apiBaseUrl, isDemoMode } = useSettings();
    const queryClient = useQueryClient();
    const today = new Date().toISOString().slice(0, 10);
    const [asOfDate, setAsOfDate] = useState(today);
    const [strategyId, setStrategyId] = useState('prod_v1');
    const [strategyVersion, setStrategyVersion] = useState('1.0');
    const [topN, setTopN] = useState(5);
    const [paramOverrides, setParamOverrides] = useState<Record<string, number | string>>({});
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [createForm, setCreateForm] = useState({
        strategy_id: '',
        strategy_version: '1.0',
        name: '',
        summary: '',
        params: {
            top_n_default: 10,
            min_price_krw: 1000,
            min_avg_turnover_krw_20d: 20000000000,
            max_weight_per_name: 0.1,
            max_weight_per_sector: 0.3,
            sector_taxonomy: 'KIS_INDUSTRY',
        },
    });
    const [createOverwrite, setCreateOverwrite] = useState(false);
    const [createError, setCreateError] = useState<string | null>(null);
    const [isRunning, setIsRunning] = useState(false);
    const [runError, setRunError] = useState<string | null>(null);

    const {
        data: strategies,
        isError: isStrategiesError,
        error: strategiesError,
        isFetching: isStrategiesFetching,
    } = useStrategies();

    const {
        data: recommendations,
        isError: isRecommendationsError,
        error: recommendationsError,
        isFetching: isRecommendationsFetching,
    } = useRecommendations({
        as_of_date: asOfDate,
        strategy_id: strategyId,
        strategy_version: strategyVersion,
    });
    const [selectedItem, setSelectedItem] = useState<any>(null);
    const rows = useMemo(() => recommendations ?? [], [recommendations]);
    const maxScore = useMemo(() => {
        if (!rows.length) return null;
        const scores = rows.map((item: any) => Number(item.score)).filter((v: number) => !Number.isNaN(v));
        if (!scores.length) return null;
        return Math.max(...scores);
    }, [rows]);

    const { data: runStatus } = useRecommendationRunStatus();

    const strategySummary = useMemo(() => ({
        prod_v1: 'Momentum (20d/5d) with volatility penalty, liquidity/price filters, weight caps.',
    }), []);

    useEffect(() => {
        if (!strategies || strategies.length === 0) return;
        const current = strategies.find((s: any) => s.strategy_id === strategyId && s.strategy_version === strategyVersion);
        if (current) return;
        const first = strategies[0];
        setStrategyId(first.strategy_id);
        setStrategyVersion(first.strategy_version);
        if (typeof first.params?.top_n_default === 'number') {
            setTopN(first.params.top_n_default);
        }
        setParamOverrides({});
    }, [strategies, strategyId, strategyVersion]);

    const selectedStrategy = useMemo(() => {
        if (!strategies) return null;
        return strategies.find((s: any) => s.strategy_id === strategyId && s.strategy_version === strategyVersion) || null;
    }, [strategies, strategyId, strategyVersion]);

    useEffect(() => {
        setParamOverrides({});
    }, [strategyId, strategyVersion]);

    const getErrorMessage = (err: any, fallback: string) => {
        const detail = err?.response?.data?.detail;
        if (detail) return String(detail);
        if (err?.message) return String(err.message);
        return fallback;
    };

    const formatNumber = (value: number | string | undefined) => {
        if (value === undefined || value === null || value === '') return '';
        const num = typeof value === 'number' ? value : Number(String(value).replace(/,/g, ''));
        if (Number.isNaN(num)) return '';
        return num.toLocaleString('en-US');
    };

    const parseNumber = (value: string) => {
        const cleaned = value.replace(/,/g, '');
        const parsed = Number(cleaned);
        return Number.isNaN(parsed) ? 0 : parsed;
    };

    const handleRun = async () => {
        if (isDemoMode) {
            setRunError('Demo mode is enabled.');
            return;
        }
        setRunError(null);
        setIsRunning(true);
        try {
            const client = createApiClient(apiBaseUrl);
            await client.post('/recommendations/trigger', {
                as_of_date: asOfDate,
                strategy_id: strategyId,
                strategy_version: strategyVersion,
                top_n: topN,
                params_override: Object.keys(paramOverrides).length ? paramOverrides : undefined,
            });
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['recommendations'] });
            }, 1500);
        } catch (err: any) {
            setRunError(getErrorMessage(err, 'Failed to run recommendation job.'));
        } finally {
            setIsRunning(false);
        }
    };

    const handleCreateStrategy = async () => {
        setCreateError(null);
        try {
            const client = createApiClient(apiBaseUrl);
            await client.post('/strategies', createForm, { params: { overwrite: createOverwrite } });
            queryClient.invalidateQueries({ queryKey: ['strategies'] });
            setIsCreateOpen(false);
        } catch (err: any) {
            setCreateError(getErrorMessage(err, 'Failed to create strategy.'));
        }
    };

    const formatWeight = (value: number | string | null | undefined) => {
        if (value === null || value === undefined) return '-';
        if (typeof value === 'number') {
            if (value <= 1) return `${(value * 100).toFixed(1)}%`;
            return `${value.toFixed(1)}%`;
        }
        return value;
    };

    const getSignal = (item: any) => {
        if (item.target) return item.target;
        if (item.signal) return item.signal;
        if (item.rationale?.signal) return item.rationale.signal;
        const weight = Number(item.target_weight ?? item.weight ?? 0);
        return weight > 0 ? 'BUY' : 'WAIT';
    };
    const formatScore = (value: number | null | undefined) => {
        if (value === null || value === undefined) return '-';
        return Number(value).toFixed(3);
    };
    const formatScore100 = (value: number | null | undefined) => {
        if (value === null || value === undefined || maxScore === null || maxScore === 0) return '-';
        return ((Number(value) / maxScore) * 100).toFixed(3);
    };
    const formatPriceRange = (low?: number | null, high?: number | null) => {
        if (low === null || low === undefined || high === null || high === undefined) return '-';
        return `${formatNumber(low)} ~ ${formatNumber(high)}`;
    };

    return (
        <div className="flex flex-col gap-6 max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white">Recommendation Algorithm</h1>
                    <p className="text-text-subtle text-sm mt-1">
                        Strategy: {strategyId} (v{strategyVersion}) - As of: {asOfDate}
                    </p>
                    <p className="text-xs text-text-subtle mt-2">
                        {selectedStrategy?.summary ?? strategySummary[strategyId] ?? 'No strategy summary available.'}
                    </p>
                    {maxScore !== null && (
                        <p className="text-xs text-text-subtle mt-1">Max Score: {formatScore(maxScore)}</p>
                    )}
                    {selectedStrategy?.name && (
                        <p className="text-xs text-text-subtle mt-1">Name: {selectedStrategy.name}</p>
                    )}
                </div>
                <div className="flex flex-wrap gap-2 items-center">
                    <input
                        type="date"
                        value={asOfDate}
                        onChange={(e) => setAsOfDate(e.target.value)}
                        className="bg-card-dark border border-border-dark text-white text-sm rounded-lg px-3 py-2 outline-none focus:border-primary"
                    />
                    <select
                        value={`${strategyId}:${strategyVersion}`}
                        onChange={(e) => {
                            const [nextId, nextVersion] = e.target.value.split(':');
                            setStrategyId(nextId);
                            setStrategyVersion(nextVersion);
                            const match = strategies?.find((s: any) => s.strategy_id === nextId && s.strategy_version === nextVersion);
                            if (typeof match?.params?.top_n_default === 'number') {
                                setTopN(match.params.top_n_default);
                            }
                            setParamOverrides({});
                        }}
                        className="bg-card-dark border border-border-dark text-white text-sm rounded-lg px-3 py-2 outline-none focus:border-primary"
                    >
                        {strategies?.length ? strategies.map((s: any) => (
                            <option key={`${s.strategy_id}:${s.strategy_version}`} value={`${s.strategy_id}:${s.strategy_version}`}>
                                {s.name} ({s.strategy_id} v{s.strategy_version})
                            </option>
                        )) : (
                            <option value={`${strategyId}:${strategyVersion}`}>
                                {isStrategiesFetching ? 'Loading strategies...' : 'No strategies found'}
                            </option>
                        )}
                    </select>
                    <input
                        type="number"
                        min={1}
                        max={50}
                        value={topN}
                        onChange={(e) => setTopN(Number(e.target.value))}
                        className="bg-card-dark border border-border-dark text-white text-sm rounded-lg px-3 py-2 outline-none focus:border-primary w-20"
                    />
                    <button
                        onClick={handleRun}
                        disabled={isRunning}
                        className={clsx(
                            "px-4 py-2 rounded-lg text-sm font-bold transition-colors",
                            isRunning ? "bg-gray-700 text-gray-400 cursor-not-allowed" : "bg-primary text-white hover:bg-primary/80"
                        )}
                    >
                        {isRunning ? 'Running...' : 'Run Recommendations'}
                    </button>
                    <button className="bg-card-dark float-right border border-border-dark hover:bg-white/5 text-white p-2 rounded-lg">
                        <span className="material-symbols-outlined">download</span>
                    </button>
                </div>
            </div>
            {runError && (
                <div className="text-sm text-red-400">{runError}</div>
            )}
            {isRecommendationsError && (
                <div className="text-sm text-red-400">
                    {getErrorMessage(recommendationsError, 'Failed to load recommendations.')}
                </div>
            )}
            {isStrategiesError && (
                <div className="text-sm text-red-400">
                    {getErrorMessage(strategiesError, 'Failed to load strategies.')}
                </div>
            )}
            {selectedStrategy?.params && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-text-subtle">
                    <label className="flex flex-col gap-1">
                        <span>min_price_krw</span>
                        <input
                            type="text"
                            inputMode="numeric"
                            value={formatNumber(paramOverrides.min_price_krw ?? selectedStrategy.params.min_price_krw)}
                            onChange={(e) => setParamOverrides(prev => ({ ...prev, min_price_krw: parseNumber(e.target.value) }))}
                            className="bg-background-dark border border-border-dark rounded px-2 py-1 text-white"
                        />
                    </label>
                    <label className="flex flex-col gap-1">
                        <span>min_avg_turnover_krw_20d</span>
                        <input
                            type="text"
                            inputMode="numeric"
                            value={formatNumber(paramOverrides.min_avg_turnover_krw_20d ?? selectedStrategy.params.min_avg_turnover_krw_20d)}
                            onChange={(e) => setParamOverrides(prev => ({ ...prev, min_avg_turnover_krw_20d: parseNumber(e.target.value) }))}
                            className="bg-background-dark border border-border-dark rounded px-2 py-1 text-white"
                        />
                    </label>
                    <label className="flex flex-col gap-1">
                        <span>max_weight_per_name</span>
                        <input
                            type="text"
                            inputMode="decimal"
                            value={paramOverrides.max_weight_per_name ?? selectedStrategy.params.max_weight_per_name ?? ''}
                            onChange={(e) => setParamOverrides(prev => ({ ...prev, max_weight_per_name: Number(e.target.value) }))}
                            className="bg-background-dark border border-border-dark rounded px-2 py-1 text-white"
                        />
                    </label>
                    <label className="flex flex-col gap-1">
                        <span>max_weight_per_sector</span>
                        <input
                            type="text"
                            inputMode="decimal"
                            value={paramOverrides.max_weight_per_sector ?? selectedStrategy.params.max_weight_per_sector ?? ''}
                            onChange={(e) => setParamOverrides(prev => ({ ...prev, max_weight_per_sector: Number(e.target.value) }))}
                            className="bg-background-dark border border-border-dark rounded px-2 py-1 text-white"
                        />
                    </label>
                </div>
            )}
            <div className="flex flex-col gap-1 text-xs text-text-subtle">
                <span>추천 결과: {rows.length}건</span>
                {runStatus?.status && (
                    <span>
                        필터 통과: 전체 {runStatus.universe_total ?? '-'} →
                        가격 {runStatus.after_min_price ?? '-'} →
                        거래대금 {runStatus.after_min_turnover ?? '-'} →
                        지표 {runStatus.after_indicators ?? '-'} →
                        최종 {runStatus.final_top_n ?? '-'}
                    </span>
                )}
                <button
                    onClick={() => setIsCreateOpen(!isCreateOpen)}
                    className="text-primary hover:text-white transition-colors"
                >
                    {isCreateOpen ? '전략 추가 닫기' : '전략 추가'}
                </button>
            </div>
            {isCreateOpen && (
                <div className="bg-card-dark border border-border-dark rounded-lg p-4 text-xs text-text-subtle grid grid-cols-1 md:grid-cols-2 gap-3">
                    <label className="flex flex-col gap-1">
                        <span>strategy_id</span>
                        <input
                            type="text"
                            value={createForm.strategy_id}
                            onChange={(e) => setCreateForm(prev => ({ ...prev, strategy_id: e.target.value }))}
                            className="bg-background-dark border border-border-dark rounded px-2 py-1 text-white"
                        />
                    </label>
                    <label className="flex flex-col gap-1">
                        <span>strategy_version</span>
                        <input
                            type="text"
                            value={createForm.strategy_version}
                            onChange={(e) => setCreateForm(prev => ({ ...prev, strategy_version: e.target.value }))}
                            className="bg-background-dark border border-border-dark rounded px-2 py-1 text-white"
                        />
                    </label>
                    <label className="flex flex-col gap-1">
                        <span>name</span>
                        <input
                            type="text"
                            value={createForm.name}
                            onChange={(e) => setCreateForm(prev => ({ ...prev, name: e.target.value }))}
                            className="bg-background-dark border border-border-dark rounded px-2 py-1 text-white"
                        />
                    </label>
                    <label className="flex flex-col gap-1">
                        <span>summary</span>
                        <input
                            type="text"
                            value={createForm.summary}
                            onChange={(e) => setCreateForm(prev => ({ ...prev, summary: e.target.value }))}
                            className="bg-background-dark border border-border-dark rounded px-2 py-1 text-white"
                        />
                    </label>
                    <label className="flex flex-col gap-1">
                        <span>top_n_default</span>
                        <input
                            type="number"
                            value={createForm.params.top_n_default}
                            onChange={(e) => setCreateForm(prev => ({ ...prev, params: { ...prev.params, top_n_default: Number(e.target.value) } }))}
                            className="bg-background-dark border border-border-dark rounded px-2 py-1 text-white"
                        />
                    </label>
                    <label className="flex flex-col gap-1">
                        <span>min_price_krw</span>
                        <input
                            type="text"
                            inputMode="numeric"
                            value={formatNumber(createForm.params.min_price_krw)}
                            onChange={(e) => setCreateForm(prev => ({ ...prev, params: { ...prev.params, min_price_krw: parseNumber(e.target.value) } }))}
                            className="bg-background-dark border border-border-dark rounded px-2 py-1 text-white"
                        />
                    </label>
                    <label className="flex flex-col gap-1">
                        <span>min_avg_turnover_krw_20d</span>
                        <input
                            type="text"
                            inputMode="numeric"
                            value={formatNumber(createForm.params.min_avg_turnover_krw_20d)}
                            onChange={(e) => setCreateForm(prev => ({ ...prev, params: { ...prev.params, min_avg_turnover_krw_20d: parseNumber(e.target.value) } }))}
                            className="bg-background-dark border border-border-dark rounded px-2 py-1 text-white"
                        />
                    </label>
                    <label className="flex flex-col gap-1">
                        <span>max_weight_per_name</span>
                        <input
                            type="number"
                            step="0.01"
                            value={createForm.params.max_weight_per_name}
                            onChange={(e) => setCreateForm(prev => ({ ...prev, params: { ...prev.params, max_weight_per_name: Number(e.target.value) } }))}
                            className="bg-background-dark border border-border-dark rounded px-2 py-1 text-white"
                        />
                    </label>
                    <label className="flex flex-col gap-1">
                        <span>max_weight_per_sector</span>
                        <input
                            type="number"
                            step="0.01"
                            value={createForm.params.max_weight_per_sector}
                            onChange={(e) => setCreateForm(prev => ({ ...prev, params: { ...prev.params, max_weight_per_sector: Number(e.target.value) } }))}
                            className="bg-background-dark border border-border-dark rounded px-2 py-1 text-white"
                        />
                    </label>
                    <label className="flex flex-col gap-1">
                        <span>sector_taxonomy</span>
                        <input
                            type="text"
                            value={createForm.params.sector_taxonomy}
                            onChange={(e) => setCreateForm(prev => ({ ...prev, params: { ...prev.params, sector_taxonomy: e.target.value } }))}
                            className="bg-background-dark border border-border-dark rounded px-2 py-1 text-white"
                        />
                    </label>
                    <label className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            checked={createOverwrite}
                            onChange={(e) => setCreateOverwrite(e.target.checked)}
                        />
                        <span>overwrite</span>
                    </label>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleCreateStrategy}
                            className="px-3 py-2 rounded bg-primary text-white text-xs font-bold"
                        >
                            전략 저장
                        </button>
                        {createError && <span className="text-red-400">{createError}</span>}
                    </div>
                </div>
            )}

            {/* Table Card */}
            <div className="bg-card-dark border border-border-dark rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-[#151e1d] text-text-subtle border-b border-border-dark">
                            <tr>
                                <th className="px-6 py-4 text-left font-bold w-16">Rank</th>
                                <th className="px-6 py-4 text-left font-bold">종목 (Ticker)</th>
                                <th className="px-6 py-4 text-center font-bold">Signal</th>
                                <th
                                    className="px-6 py-4 text-right font-bold"
                                    title="추천 포트폴리오 내 목표 비중 (target weight)"
                                >
                                    Weight
                                </th>
                                <th
                                    className="px-6 py-4 text-right font-bold"
                                    title="score = 0.6*z(ret_20) + 0.4*z(ret_5) - 0.2*z(vol_20); 표시는 0-100 정규화"
                                >
                                    Score
                                </th>
                                <th className="px-6 py-4 text-right font-bold">Target Range</th>
                                <th className="px-6 py-4 text-right font-bold">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark">
                            {rows.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="px-6 py-8 text-center text-text-subtle">
                                        {isRecommendationsFetching
                                            ? 'Loading recommendations...'
                                            : 'No recommendations yet. Run recommendations to generate results.'}
                                    </td>
                                </tr>
                            ) : rows.map((item: any) => (
                                <tr key={item.ticker} className="group hover:bg-white/5 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/30 text-white font-bold text-sm">
                                            {item.rank}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex flex-col">
                                            <span className="text-white font-bold">{item.name ?? item.name_ko ?? '-'}</span>
                                            <span className="text-xs text-text-subtle font-mono">{item.ticker}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        <span className={clsx(
                                            "px-2 py-1 rounded text-xs font-bold uppercase",
                                            getSignal(item) === 'BUY' ? "text-green-500 bg-green-500/10 border border-green-500/20" :
                                                getSignal(item) === 'SELL' ? "text-red-500 bg-red-500/10 border border-red-500/20" :
                                                    "text-yellow-500 bg-yellow-500/10 border border-yellow-500/20"
                                        )}>
                                            {getSignal(item)}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right text-lg font-display font-bold text-white">{formatWeight(item.weight ?? item.target_weight)}</td>
                                    <td
                                        className="px-6 py-4 text-right font-bold text-white"
                                        title={`raw: ${formatScore(item.score)} / max: ${formatScore(maxScore ?? undefined)}`}
                                    >
                                        {formatScore100(item.score)}
                                    </td>
                                    <td className="px-6 py-4 text-right text-sm text-white">
                                        {formatPriceRange(item.target_price_low, item.target_price_high)}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button
                                            onClick={() => setSelectedItem(item)}
                                            className="px-4 py-2 bg-primary hover:bg-primary/80 text-white rounded-lg text-xs font-bold transition-colors"
                                        >
                                            추천근거
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
