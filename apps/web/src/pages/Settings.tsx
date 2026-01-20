import { useEffect, useState } from 'react';
import clsx from 'clsx';
import { useSettings } from '../contexts/SettingsContext';
import { createApiClient } from '../lib/apiClient';

interface ETLJob {
    id: string;
    name: string;
    source: string;
    lastRun: string;
    lastUpdatedRaw?: string | null;
    processedCount?: number | null;
    totalCount?: number | null;
    progressUnit?: string;
    status: string;
    lastResultStatus?: string;
    isRunning?: boolean;
    message?: string | null;
    duration: string;
    rowCount: number;
}

interface SignalHorizonRules {
    short: number;
    long: number;
    mom: number;
    slope_lb: number;
    vol_n: number;
    vol_mult: number;
    atr_n: number;
    vol_q_window: number;
    vol_q: number;
    confirm: number;
}

interface SignalConfig {
    engine: string;
    horizons: Record<string, SignalHorizonRules>;
    weights: Record<string, number>;
}

const JOB_TEMPLATES: Record<string, any> = {
    krx: { name: 'KRX 종목 기준정보 (Master Data)', source: 'Korea Exchange', progressUnit: '종목' },
    mapping: { name: '종목 매핑 (Standard)', source: 'Internal Mapping', progressUnit: '종목' },
    dart: { name: 'DART 공시/재무', source: 'FSS DART Open API', progressUnit: '공시' },
    dart_financials: { name: 'DART 재무제표 (Numerical)', source: 'FSS DART Open API', progressUnit: '회사' },
    ecos: { name: 'ECOS 거시경제', source: 'Bank of Korea', progressUnit: '지표' },
};

export default function Settings() {
    const { apiBaseUrl, isDemoMode, setDemoMode } = useSettings();
    const [jobs, setJobs] = useState<ETLJob[]>([]);
    const [loadingMap, setLoadingMap] = useState<Record<string, boolean>>({});
    const [activeTab, setActiveTab] = useState<'signals' | 'etl'>('etl');
    const [signalConfig, setSignalConfig] = useState<SignalConfig | null>(null);
    const [signalDefaults, setSignalDefaults] = useState<SignalConfig | null>(null);
    const [signalMode, setSignalMode] = useState<'default' | 'custom'>('default');
    const [signalSaving, setSignalSaving] = useState(false);
    const [signalError, setSignalError] = useState<string | null>(null);
    const [testTickers, setTestTickers] = useState('005930,000660');
    const [testHorizon, setTestHorizon] = useState('1D');
    const [testResults, setTestResults] = useState<any[]>([]);
    const [testLoading, setTestLoading] = useState(false);

    const fetchStatus = async () => {
        try {
            const client = createApiClient(apiBaseUrl);
            const resp = await client.get('/ingest/status');
            const data = resp.data.jobs.map((j: any) => ({
                id: j.id,
                ...JOB_TEMPLATES[j.id],
                lastRun: j.last_updated ? new Date(j.last_updated).toLocaleString() : '-',
                lastUpdatedRaw: j.last_updated,
                processedCount: j.processed_count ?? null,
                totalCount: j.total_count ?? null,
                status: j.status, // backend status (RUNNING or last result)
                lastResultStatus: j.last_result_status,
                isRunning: j.is_running,
                message: j.message,
                duration: '-',
                rowCount: j.row_count
            }));

            // Sort order: ECOS -> KRX -> Mapping -> DART -> DART Financials
            const order = ['ecos', 'krx', 'mapping', 'dart', 'dart_financials'];
            data.sort((a: any, b: any) => order.indexOf(a.id) - order.indexOf(b.id));

            setJobs(data);
        } catch (error) {
            console.error("Failed to fetch initial status", error);
        }
    };

    const fetchSignalConfig = async () => {
        try {
            const client = createApiClient(apiBaseUrl);
            const resp = await client.get('/signals/config');
            setSignalConfig(resp.data.config);
            setSignalDefaults(resp.data.defaults);
            setSignalMode(resp.data.mode);
            setSignalError(null);
        } catch (error) {
            console.error("Failed to fetch signal config", error);
            setSignalError('Failed to load signal config');
        }
    };

    useEffect(() => {
        if (!isDemoMode) {
            fetchStatus();
            fetchSignalConfig();
        }
    }, [apiBaseUrl, isDemoMode]);

    const handleRunJob = async (id: string) => {
        if (isDemoMode) {
            alert("데모 모드에서는 실제 적재를 실행할 수 없습니다.");
            return;
        }

        setLoadingMap(prev => ({ ...prev, [id]: true }));
        try {
            const client = createApiClient(apiBaseUrl);
            await client.post(`/ingest/trigger/${id}`);

            // Update status to indicate it has been accepted and is running in background
            setLoadingMap(prev => ({ ...prev, [id]: false }));
            setJobs(prevJobs => prevJobs.map(job => {
                if (job.id === id) {
                    return { ...job, lastRun: new Date().toLocaleString(), status: 'RUNNING', duration: 'Async' };
                }
                return job;
            }));

            // Auto refresh status after 5 seconds to show first results
            setTimeout(fetchStatus, 5000);

        } catch (error) {
            console.error("Ingest failed", error);
            setLoadingMap(prev => ({ ...prev, [id]: false }));
            setJobs(prevJobs => prevJobs.map(job => {
                if (job.id === id) {
                    return { ...job, status: 'FAILED' };
                }
                return job;
            }));
            alert("적재 요청 실패. 백엔드 로그를 확인하세요.");
        }
    };

    // Periodic polling when a job is RUNNING
    useEffect(() => {
        let interval: any;
        if (jobs.some(j => j.status === 'RUNNING')) {
            interval = setInterval(fetchStatus, 3000);
        }
        return () => clearInterval(interval);
    }, [jobs]);

    const formatProgress = (job: ETLJob) => {
        const processed = job.processedCount ?? 0;
        const total = job.totalCount ?? 0;
        const unit = job.progressUnit ? ` ${job.progressUnit}` : '';
        if (total > 0) {
            return `${processed.toLocaleString()}/${total.toLocaleString()}${unit}`;
        }
        return `${processed.toLocaleString()}/--${unit}`;
    };

    const updateHorizonRule = (horizon: string, key: keyof SignalHorizonRules, value: number) => {
        if (!signalConfig) return;
        setSignalConfig({
            ...signalConfig,
            horizons: {
                ...signalConfig.horizons,
                [horizon]: {
                    ...signalConfig.horizons[horizon],
                    [key]: value
                }
            }
        });
    };

    const updateWeight = (key: string, value: number) => {
        if (!signalConfig) return;
        setSignalConfig({
            ...signalConfig,
            weights: {
                ...signalConfig.weights,
                [key]: value
            }
        });
    };

    const saveSignalConfig = async (mode: 'default' | 'custom') => {
        if (isDemoMode) return;
        setSignalSaving(true);
        try {
            const client = createApiClient(apiBaseUrl);
            const payload = mode === 'default'
                ? { mode: 'default' }
                : { mode: 'custom', config: signalConfig };
            const resp = await client.put('/signals/config', payload);
            setSignalConfig(resp.data.config);
            setSignalDefaults(resp.data.defaults);
            setSignalMode(resp.data.mode);
            setSignalError(null);
        } catch (error) {
            console.error("Failed to save signal config", error);
            setSignalError('Failed to save signal config');
        } finally {
            setSignalSaving(false);
        }
    };

    const resetSignalLocal = () => {
        if (!signalDefaults) return;
        setSignalConfig(signalDefaults);
    };

    const runSignalTest = async () => {
        if (isDemoMode) return;
        setTestLoading(true);
        try {
            const client = createApiClient(apiBaseUrl);
            const resp = await client.get('/signals', {
                params: {
                    tickers: testTickers,
                    horizon: testHorizon
                }
            });
            setTestResults(resp.data.items || []);
        } catch (error) {
            console.error("Signal test failed", error);
            setTestResults([]);
        } finally {
            setTestLoading(false);
        }
    };

    return (
        <div className="flex flex-col gap-8 max-w-5xl mx-auto">
            <h1 className="text-2xl font-bold text-white">설정 및 데이터 관리</h1>

            <div className="flex gap-2">
                <button
                    onClick={() => setActiveTab('etl')}
                    className={clsx(
                        "px-4 py-2 rounded-lg text-sm font-bold transition-all",
                        activeTab === 'etl'
                            ? "bg-primary text-white shadow-lg shadow-primary/20"
                            : "bg-gray-800 text-gray-300 hover:text-white"
                    )}
                >
                    ETL Management
                </button>
                <button
                    onClick={() => setActiveTab('signals')}
                    className={clsx(
                        "px-4 py-2 rounded-lg text-sm font-bold transition-all",
                        activeTab === 'signals'
                            ? "bg-primary text-white shadow-lg shadow-primary/20"
                            : "bg-gray-800 text-gray-300 hover:text-white"
                    )}
                >
                    Signal Settings
                </button>
            </div>

            {activeTab === 'signals' && (
            <>
            <section className="bg-card-dark border border-border-dark rounded-xl p-6">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-primary">tune</span>
            Signal Tuning (Admin)
            </h2>
            {isDemoMode ? (
            <div className="text-sm text-text-subtle">Demo mode is ON. Disable demo mode to edit signal settings.</div>
            ) : (
            <>
            <div className="flex flex-wrap items-center gap-3 mb-4">
            <button
            onClick={() => saveSignalConfig('custom')}
            disabled={signalSaving || !signalConfig}
            className={clsx(
            "px-4 py-2 rounded-lg font-bold text-xs transition-all",
            (signalSaving || !signalConfig)
            ? "bg-gray-700 text-gray-400 cursor-not-allowed"
            : "bg-primary hover:bg-blue-600 text-white shadow-lg shadow-primary/20"
            )}
            >
            Save Config
            </button>
            <button
            onClick={() => resetSignalLocal()}
            disabled={!signalDefaults || signalSaving}
            className={clsx(
            "px-4 py-2 rounded-lg font-bold text-xs transition-all",
            (!signalDefaults || signalSaving)
            ? "bg-gray-700 text-gray-400 cursor-not-allowed"
            : "bg-gray-800 hover:bg-gray-700 text-white"
            )}
            >
            Reset Local to Defaults
            </button>
            <button
            onClick={() => saveSignalConfig('default')}
            disabled={signalSaving}
            className={clsx(
            "px-4 py-2 rounded-lg font-bold text-xs transition-all",
            signalSaving
            ? "bg-gray-700 text-gray-400 cursor-not-allowed"
            : "bg-gray-800 hover:bg-gray-700 text-white"
            )}
            >
            Use Defaults Now
            </button>
            <span className="text-xs text-text-subtle">Current mode: {signalMode}</span>
            {signalError && <span className="text-xs text-red-400">{signalError}</span>}
            </div>
            
            {signalConfig && (
            <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {['1D', '3D', '1W'].map((horizon) => (
            <div key={horizon} className="border border-border-dark rounded-lg p-4">
            <div className="text-sm font-bold text-white mb-3">{horizon} Rules</div>
            <div className="grid grid-cols-2 gap-3 text-sm">
            {([
            ['short', 'MA Short', 1],
            ['long', 'MA Long', 1],
            ['mom', 'Momentum Days', 1],
            ['slope_lb', 'Slope Lookback', 1],
            ['vol_n', 'Volume MA', 1],
            ['vol_mult', 'Volume Mult', 0.01],
            ['atr_n', 'ATR N', 1],
            ['vol_q_window', 'ATR Quant Window', 1],
            ['vol_q', 'ATR Quantile', 0.01],
            ['confirm', 'Confirm Bars', 1],
            ] as const).map(([key, label, step]) => (
            <label key={`${horizon}-${key}`} className="flex flex-col gap-1">
            <span className="text-xs text-text-subtle">{label}</span>
            <input
            type="number"
            step={step}
            value={signalConfig.horizons[horizon][key]}
            onChange={(e) => updateHorizonRule(horizon, key, Number(e.target.value))}
            className="bg-background-dark border border-border-dark rounded-lg px-3 py-2 text-white outline-none"
            />
            </label>
            ))}
            </div>
            </div>
            ))}
            </div>
            
            <div className="mt-6 border border-border-dark rounded-lg p-4">
            <div className="text-sm font-bold text-white mb-3">Confidence Weights</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            {([
            ['ma_gap', 'MA Gap', 0.01],
            ['trend_strength', 'Trend Strength', 0.01],
            ['vol_strength', 'Volume Strength', 0.01],
            ['vol_penalty', 'Volatility Penalty', 0.01],
            ] as const).map(([key, label, step]) => (
            <label key={key} className="flex flex-col gap-1">
            <span className="text-xs text-text-subtle">{label}</span>
            <input
            type="number"
            step={step}
            value={signalConfig.weights[key]}
            onChange={(e) => updateWeight(key, Number(e.target.value))}
            className="bg-background-dark border border-border-dark rounded-lg px-3 py-2 text-white outline-none"
            />
            </label>
            ))}
            </div>
            </div>
            
            <div className="mt-6 border border-border-dark rounded-lg p-4">
            <div className="text-sm font-bold text-white mb-3">Quick Signal Test</div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
            <label className="flex flex-col gap-1 md:col-span-2">
            <span className="text-xs text-text-subtle">Tickers (comma-separated)</span>
            <input
            type="text"
            value={testTickers}
            onChange={(e) => setTestTickers(e.target.value)}
            className="bg-background-dark border border-border-dark rounded-lg px-3 py-2 text-white outline-none"
            />
            </label>
            <label className="flex flex-col gap-1">
            <span className="text-xs text-text-subtle">Horizon</span>
            <select
            value={testHorizon}
            onChange={(e) => setTestHorizon(e.target.value)}
            className="bg-background-dark border border-border-dark rounded-lg px-3 py-2 text-white outline-none"
            >
            <option value="1D">1D</option>
            <option value="3D">3D</option>
            <option value="1W">1W</option>
            </select>
            </label>
            </div>
            <button
            onClick={runSignalTest}
            disabled={testLoading}
            className={clsx(
            "mt-3 px-4 py-2 rounded-lg font-bold text-xs transition-all",
            testLoading
            ? "bg-gray-700 text-gray-400 cursor-not-allowed"
            : "bg-gray-800 hover:bg-gray-700 text-white"
            )}
            >
            {testLoading ? 'Running...' : 'Run Test'}
            </button>
            {testResults.length > 0 && (
            <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm text-left">
            <thead className="bg-[#151e1d] text-text-subtle border-b border-border-dark">
            <tr>
            <th className="px-4 py-2 font-bold">Ticker</th>
            <th className="px-4 py-2 font-bold">Signal</th>
            <th className="px-4 py-2 font-bold">Confidence</th>
            <th className="px-4 py-2 font-bold">Triggers</th>
            </tr>
            </thead>
            <tbody className="divide-y divide-border-dark/50">
            {testResults.map((row) => (
            <tr key={`${row.ticker}-${row.horizon}`}>
            <td className="px-4 py-2 text-white">{row.ticker}</td>
            <td className="px-4 py-2 text-white">{row.signal}</td>
            <td className="px-4 py-2 text-white">{row.confidence}</td>
            <td className="px-4 py-2 text-gray-300">{(row.triggers || []).join(', ')}</td>
            </tr>
            ))}
            </tbody>
            </table>
            </div>
            )}
            </div>
            </>
            )}
            </>
            )}
            </section>
            </>
            )}

            {activeTab === 'etl' && (
            <>
            <section className="bg-card-dark border border-border-dark rounded-xl p-6">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-primary">tune</span>
            시스템 설정 (System)
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex flex-col gap-2">
            <label className="text-sm font-bold text-text-subtle">API Base URL</label>
            <input
            type="text"
            value={apiBaseUrl}
            onChange={() => { }}
            className="bg-background-dark border border-border-dark rounded-lg px-4 py-2 text-white outline-none opacity-50 cursor-not-allowed"
            readOnly
            />
            </div>
            <div className="flex flex-col gap-2">
            <label className="text-sm font-bold text-text-subtle">데모 모드 (Demo Mode)</label>
            <div
            className="flex items-center gap-3 cursor-pointer"
            onClick={() => setDemoMode(!isDemoMode)}
            >
            <div className={clsx("w-12 h-6 rounded-full relative transition-colors", isDemoMode ? "bg-primary" : "bg-gray-600")}>
            <div className={clsx("absolute top-1 w-4 h-4 bg-white rounded-full transition-all", isDemoMode ? "right-1" : "left-1")}></div>
            </div>
            <span className="text-sm text-white">
            {isDemoMode ? "ON (백엔드 미연결 시 Mock 사용)" : "OFF (실제 API 사용)"}
            </span>
            </div>
            </div>
            </div>
            </section>

            <section className="bg-card-dark border border-border-dark rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="material-symbols-outlined text-green-500">database</span>
            데이터 수동 적재 (ETL Management)
            </h2>
            <button className="text-sm text-text-subtle hover:text-white flex items-center gap-1">
            <span className="material-symbols-outlined text-[18px]">history</span>
            전체 로그 보기
            </button>
            </div>
            
            <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
            <thead className="bg-[#151e1d] text-text-subtle border-b border-border-dark">
            <tr>
            <th className="px-4 py-3 font-bold">작업명 (Job Name)</th>
            <th className="px-4 py-3 font-bold">출처 (Source)</th>
            <th className="px-4 py-3 font-bold">최근 실행</th>
            <th className="px-4 py-3 font-bold">상태 (Status)</th>
            <th className="px-4 py-3 font-bold text-right">실행 (Action)</th>
            </tr>
            </thead>
            <tbody className="divide-y divide-border-dark/50">
            {jobs.map((job) => (
            <tr key={job.id} className="hover:bg-white/5 transition-colors">
            <td className="px-4 py-4">
            <div className="flex flex-col">
            <span className="text-white font-bold">{job.name}</span>
            <span className="text-xs text-text-subtle">ID: {job.id}</span>
            </div>
            </td>
            <td className="px-4 py-4 text-gray-300">{job.source}</td>
            <td className="px-4 py-4 text-gray-300">
            {job.lastRun}
            <div className="text-[10px] text-text-subtle">소요시간: {job.duration}</div>
            </td>
            <td className="px-4 py-4">
            <div className="flex flex-col gap-1">
            <span className={clsx(
            "px-2 py-1 rounded text-xs font-bold w-fit",
            (job.lastResultStatus ?? job.status) === 'SUCCESS' ? "bg-green-500/20 text-green-500" :
            (job.lastResultStatus ?? job.status) === 'FAILED' ? "bg-red-500/20 text-red-500" :
            (job.lastResultStatus ?? job.status) === 'ERROR' ? "bg-red-500/20 text-red-500" :
            "bg-gray-700 text-gray-400"
            )}>
            {job.lastResultStatus ?? job.status}
            </span>
            {job.rowCount > 0 && (
            <span className="text-[10px] text-text-subtle">
                                                    누적 적재: {job.rowCount.toLocaleString()}건
            </span>
            )}
            </div>
            </td>
            <td className="px-4 py-4 text-right">
            <button
            onClick={() => handleRunJob(job.id)}
            disabled={loadingMap[job.id] || job.isRunning}
            className={clsx(
            "px-4 py-2 rounded-lg font-bold text-xs transition-all flex items-center gap-2 ml-auto",
            (loadingMap[job.id] || job.isRunning)
            ? "bg-gray-700 text-gray-400 cursor-not-allowed"
            : "bg-primary hover:bg-blue-600 text-white shadow-lg shadow-primary/20"
            )}
            >
                                            {(loadingMap[job.id] || job.isRunning) ? (
                                                <>
                                                    <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                                                    {formatProgress(job)}
                                                </>
                                            ) : (
            <>
            <span className="material-symbols-outlined text-[16px]">play_arrow</span>
            적재 실행
            </>
            )}
            </button>
            </td>
            </tr>
            ))}
            </tbody>
            </table>
            </div>
            
            <div className="mt-4 p-4 rounded-lg bg-blue-500/10 border border-blue-500/20 flex gap-3 text-sm text-blue-300">
            <span className="material-symbols-outlined">info</span>
            <div>
            <p className="font-bold mb-1">참고 (Note)</p>
            <p>수동 적재 실행 시 백엔드 워커(Worker)에 작업이 큐잉됩니다. 대량 데이터(DART, ECOS)의 경우 수분이 소요될 수 있습니다.</p>
            </div>
            </div>
            </section>
            </>
            )}

        </div>
    );
}
