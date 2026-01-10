import { useEffect, useState } from 'react';
import clsx from 'clsx';
import { useSettings } from '../contexts/SettingsContext';
import { createApiClient } from '../lib/apiClient';

interface ETLJob {
    id: string;
    name: string;
    source: string;
    lastRun: string;
    status: string;
    duration: string;
    rowCount: number;
}

const JOB_TEMPLATES: Record<string, any> = {
    krx: { name: 'KRX 종목 기준정보 (Master Data)', source: 'Korea Exchange' },
    mapping: { name: '종목 매핑 (Standard)', source: 'Internal Mapping' },
    dart: { name: 'DART 공시/재무', source: 'FSS DART Open API' },
    dart_financials: { name: 'DART 재무제표 (Numerical)', source: 'FSS DART Open API' },
    ecos: { name: 'ECOS 거시경제', source: 'Bank of Korea' },
};

export default function Settings() {
    const { apiBaseUrl, isDemoMode, setDemoMode } = useSettings();
    const [jobs, setJobs] = useState<ETLJob[]>([]);
    const [loadingMap, setLoadingMap] = useState<Record<string, boolean>>({});

    const fetchStatus = async () => {
        try {
            const client = createApiClient(apiBaseUrl);
            const resp = await client.get('/ingest/status');
            const data = resp.data.jobs.map((j: any) => ({
                id: j.id,
                ...JOB_TEMPLATES[j.id],
                lastRun: j.last_updated ? new Date(j.last_updated).toLocaleString() : '-',
                status: j.status, // Use backend real status
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

    useEffect(() => {
        if (!isDemoMode) {
            fetchStatus();
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

    return (
        <div className="flex flex-col gap-8 max-w-5xl mx-auto">
            <h1 className="text-2xl font-bold text-white">설정 및 데이터 관리</h1>

            {/* General Settings Section */}
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

            {/* ETL Management Section */}
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
                                                job.status === 'SUCCESS' ? "bg-green-500/20 text-green-500" :
                                                    job.status === 'RUNNING' ? "bg-blue-500/20 text-blue-500" :
                                                        job.status === 'FAILED' ? "bg-red-500/20 text-red-500" :
                                                            "bg-gray-700 text-gray-400"
                                            )}>
                                                {job.status}
                                            </span>
                                            {job.rowCount > 0 && (
                                                <span className="text-[10px] text-text-subtle">
                                                    적재 데이터: {job.rowCount.toLocaleString()}건
                                                </span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-4 py-4 text-right">
                                        <button
                                            onClick={() => handleRunJob(job.id)}
                                            disabled={loadingMap[job.id]}
                                            className={clsx(
                                                "px-4 py-2 rounded-lg font-bold text-xs transition-all flex items-center gap-2 ml-auto",
                                                loadingMap[job.id]
                                                    ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                                                    : "bg-primary hover:bg-blue-600 text-white shadow-lg shadow-primary/20"
                                            )}
                                        >
                                            {loadingMap[job.id] ? (
                                                <>
                                                    <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                                                    Running...
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
        </div>
    );
}
