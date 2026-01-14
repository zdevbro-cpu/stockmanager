import { useEffect, useState, useRef } from 'react';
import clsx from 'clsx';
import { useQuery } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useSettings } from '../contexts/SettingsContext';
import { createApiClient } from '../lib/apiClient';
import DocumentManager from '../features/reports/DocumentManager';

type Tab = 'library' | 'builder' | 'preview';

interface ReportMeta {
    id: number;
    company_name: string;
    template: string;
    status: string;
    created_at: string;
}

import {
    ComposedChart,
    Line,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';

function ReportChartLoader({ reportId }: { reportId: number }) {
    const { apiBaseUrl } = useSettings();
    const client = createApiClient(apiBaseUrl);

    const { data: reportMeta } = useQuery({
        queryKey: ['report_meta', reportId],
        queryFn: async () => {
            const resp = await client.get(`/reports/${reportId}`);
            return resp.data;
        },
    });

    const companyId = reportMeta?.company_id;

    const { data: chartData } = useQuery({
        queryKey: ['financials_chart', companyId, 'FIN_IS_ANNUAL_3Y'],
        queryFn: async () => {
            if (!companyId) return null;
            const resp = await client.get(`/financials/${companyId}/chart/FIN_IS_ANNUAL_3Y`);
            return resp.data;
        },
        enabled: !!companyId,
    });

    if (!companyId) return <div className="text-center text-gray-400 text-xs">Loading context...</div>;
    if (!chartData) return <div className="text-center text-gray-400 text-xs">Loading Chart...</div>;

    return (
        <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
                <XAxis dataKey="name" stroke="#666" tick={{ fontSize: 10 }} />
                <YAxis
                    yAxisId="left"
                    orientation="left"
                    stroke="#8884d8"
                    tick={{ fontSize: 10 }}
                    tickFormatter={(val) => `${(val / 100000000).toLocaleString()}`}
                    label={{ value: 'Amount (100M KRW)', angle: -90, position: 'insideLeft', style: { fontSize: '10px' } }}
                />
                <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" tick={{ fontSize: 10 }} tickFormatter={(val) => `${val}%`} />
                <Tooltip
                    contentStyle={{ backgroundColor: '#fff', borderColor: '#ddd', fontSize: '10px', color: '#000' }}
                    formatter={(value: any, name: string) => {
                        if (name.toLowerCase().includes('margin') || name.toUpperCase().includes('ROE')) {
                            return [`${value}%`, name];
                        }
                        return [`${(value / 100000000).toLocaleString()} KRW 100M`, name];
                    }}
                />
                <Legend iconSize={10} wrapperStyle={{ fontSize: '10px' }} />
                <Bar yAxisId="left" dataKey="revenue" fill="#bfdbfe" name="Revenue" barSize={40} radius={[4, 4, 0, 0]} />
                <Line yAxisId="left" type="monotone" dataKey="op_income" stroke="#2563eb" strokeWidth={2} name="Operating Income" dot={{ r: 3 }} />
                <Line yAxisId="left" type="monotone" dataKey="net_income" stroke="#7c3aed" strokeWidth={2} name="Net Income" dot={{ r: 3 }} />
            </ComposedChart>
        </ResponsiveContainer>
    );
}

export default function Reports() {
    const { apiBaseUrl } = useSettings();
    const [activeTab, setActiveTab] = useState<Tab>('builder');
    const [reports, setReports] = useState<ReportMeta[]>([]);
    const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
    const [reportContent, setReportContent] = useState<string>('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [generationStatus, setGenerationStatus] = useState('');

    // Form states for Builder
    const [searchTerm, setSearchTerm] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [targetCompanyId, setTargetCompanyId] = useState('');
    const [selectedCompanyName, setSelectedCompanyName] = useState('');
    const [template, setTemplate] = useState('investment_memo_vc_v1');
    const [isSearching, setIsSearching] = useState(false);

    const searchCompanies = async (val: string) => {
        setSearchTerm(val);
        if (val.length < 1) {
            setSearchResults([]);
            return;
        }
        setIsSearching(true);
        try {
            const client = createApiClient(apiBaseUrl);
            const resp = await client.get(`/companies/search?q=${encodeURIComponent(val)}`);
            setSearchResults(resp.data);
        } catch (error) {
            console.error(error);
        } finally {
            setIsSearching(false);
        }
    };

    const handleSelectCompany = (c: any) => {
        setTargetCompanyId(c.id.toString());
        setSelectedCompanyName(c.name);
        setSearchTerm(c.name);
        setSearchResults([]);
    };

    const fetchReports = async () => {
        try {
            const client = createApiClient(apiBaseUrl);
            const resp = await client.get(`/reports?t=${Date.now()}`);
            setReports(resp.data);
        } catch (error) {
            console.error("Failed to fetch reports", error);
        }
    };

    const fetchReportDetail = async (id: number) => {
        try {
            const client = createApiClient(apiBaseUrl);
            const resp = await client.get(`/reports/${id}`);

            setReportContent(resp.data.content);

            setSelectedReportId(id);
            setActiveTab('preview');
        } catch (error) {
            console.error("Failed to fetch report detail", error);
        }
    };

    const handleCreateReport = async () => {
        if (!targetCompanyId) {
            alert('Delete failed: ' + (error instanceof Error ? error.message : 'Unknown error'));
            return;
        }
        setIsGenerating(true);
        setGenerationStatus('由ы룷???앹꽦 ?붿껌??蹂대궡??以?..');
        try {
            const client = createApiClient(apiBaseUrl);
            const startResp = await client.post('/reports', {
                company_id: parseInt(targetCompanyId),
                template: template
            }, {
                headers: { 'Authorization': 'Bearer dev-token' }
            });

            const newReportId = startResp.data.report_id;
            setGenerationStatus('AI 遺꾩꽍 諛?DART ?곗씠???섏쭛 以?.. (??20~40珥??뚯슂)');

            // Polling for status
            let isDone = false;
            let attempts = 0;
            const maxAttempts = 60; // 2 mins max

            while (!isDone && attempts < maxAttempts) {
                await new Promise(resolve => setTimeout(resolve, 2000)); // Poll every 2s
                attempts++;

                try {
                    const statusResp = await client.get(`/reports/${newReportId}`);
                    if (statusResp.data.status === 'DONE') {
                        isDone = true;
                        setGenerationStatus('遺꾩꽍 ?꾨즺! 由ы룷?몃? 遺덈윭?ㅻ뒗 以?..');
                        await fetchReportDetail(newReportId);
                        fetchReports();
                    } else {
                        // Update status every 2 seconds so user knows it's alive
                        setGenerationStatus(`?ъ링 遺꾩꽍 吏꾪뻾 以?.. (${attempts * 2}珥?寃쎄낵)`);
                    }
                } catch (err) {
                    console.error("Polling error", err);
                    // On error, still update the time to show we're retrying
                    setGenerationStatus(`?ъ떆??以?.. (${attempts * 2}珥?寃쎄낵)`);
                }
            }

            if (!isDone) {
                alert("由ы룷???앹꽦 ?쒓컙???덈Т ?ㅻ옒 嫄몃┰?덈떎. ?쇱씠釉뚮윭由ъ뿉???섏쨷???뺤씤?댁＜?몄슂.");
                setActiveTab('library');
                fetchReports();
            }
        } catch (error) {
            alert("由ы룷???앹꽦 ?붿껌 ?ㅽ뙣");
        } finally {
            setIsGenerating(false);
            setGenerationStatus('');
        }
    };

    const reportRef = useRef<HTMLDivElement>(null);

    const handleDownloadPdf = () => {
        const reportElement = reportRef.current;
        if (!reportElement) return;

        // Create a hidden iframe for clean printing
        const iframe = document.createElement('iframe');
        iframe.style.position = 'fixed';
        iframe.style.right = '0';
        iframe.style.bottom = '0';
        iframe.style.width = '0';
        iframe.style.height = '0';
        iframe.style.border = '0';
        document.body.appendChild(iframe);

        const content = reportElement.innerHTML;

        const doc = iframe.contentWindow?.document;
        if (doc) {
            doc.open();
            doc.write(`
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Investment Memo</title>
                    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap" rel="stylesheet">
                    <style>
                        @page { margin: 15mm; size: A4; }
                        body {
                            font-family: 'Noto Sans KR', sans-serif;
                            font-size: 9pt;
                            line-height: 1.5;
                            color: #000;
                            margin: 0;
                            padding: 0;
                        }
                        h1 {
                            font-size: 10pt;
                            color: #0891b2;
                            border-bottom: 2px solid #0891b2;
                            margin-bottom: 4px;
                            display: inline-block;
                        }
                        h2 {
                            font-size: 18pt;
                            font-weight: 900;
                            margin-top: 5px;
                            margin-bottom: 15px;
                            color: #000;
                            letter-spacing: -0.5px;
                        }
                        /* Numbered Section Headers - Drastically Smaller as requested */
                        h3 {
                            font-size: 8pt !important; /* Smaller than body */
                            font-weight: 800;
                            margin-top: 15px;
                            margin-bottom: 5px;
                            border-bottom: 1px solid #000;
                            padding-bottom: 2px;
                            color: #000;
                        }
                        p { margin-bottom: 8px; text-align: justify; }
                        ul, ol { padding-left: 18px; margin-bottom: 8px; }
                        li { margin-bottom: 3px; }
                        
                        /* High-contrast Table Grid - FORCED */
                        table {
                            width: 100%;
                            border-collapse: collapse !important;
                            margin: 10px 0;
                            font-size: 8pt;
                            border: 1px solid #000 !important;
                        }
                        th, td {
                            border: 1px solid #000 !important; /* Force black grid */
                            padding: 4px 6px;
                            color: #000;
                        }
                        th { 
                            background-color: #eee !important; 
                            font-weight: 700; 
                            text-align: center;
                            -webkit-print-color-adjust: exact; /* Force print background */
                            print-color-adjust: exact;
                        }
                        
                        /* Layout protection */
                        * { box-sizing: border-box; }
                        img { max-width: 100%; }
                        
                        /* Page break controls */
                        h1, h2, h3, tr, li, p {
                            break-inside: avoid;
                            page-break-inside: avoid;
                        }
                    </style>
                </head>
                <body>
                    ${content}
                </body>
                </html>
            `);
            doc.close();

            // Wait for fonts to load then print
            iframe.onload = () => {
                setTimeout(() => {
                    iframe.contentWindow?.focus();
                    iframe.contentWindow?.print();
                    // Cleanup usually happens after print dialog closes, but in JS thread it continues.
                    // We can leave it or remove it after a delay.
                    setTimeout(() => document.body.removeChild(iframe), 1000);
                }, 500);
            };
        }
    };

    const handleDeleteReport = async (id: number) => {
        if (!confirm("??由ы룷?몃? ??젣?섏떆寃좎뒿?덇퉴?")) return;

        // Optimistic UI update: Remove from list immediately
        const previousReports = [...reports];
        setReports(prev => prev.filter(r => r.id !== id));

        try {
            const client = createApiClient(apiBaseUrl);
            await client.delete(`/reports/${id}`, {
                headers: { 'Authorization': 'Bearer dev-token' }
            });

            // Successfully deleted on server, sync once more to be safe
            fetchReports();

            if (selectedReportId === id) {
                setReportContent('');
                setSelectedReportId(null);
            }
        } catch (error) {
            // Rollback if failed
            setReports(previousReports);
            alert("??젣 ?ㅽ뙣: " + (error instanceof Error ? error.message : "?????녿뒗 ?ㅻ쪟"));
        }
    };

    useEffect(() => {
        fetchReports();
    }, [apiBaseUrl]);

    const TABS: { id: Tab; label: string; icon: string }[] = [
        { id: 'builder', label: 'Builder', icon: 'edit_document' },
        { id: 'preview', label: 'Preview', icon: 'visibility' },
        { id: 'library', label: 'Library', icon: 'library_books' },
    ];

    return (
        <div className="flex flex-col gap-6 max-w-7xl mx-auto h-[calc(100vh-100px)]">
            <h1 className="text-2xl font-bold text-white no-print">Reports</h1>

            {/* Tabs */}
            <div className="flex border-b border-border-dark no-print">
                {TABS.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={clsx(
                            "px-6 py-3 flex items-center gap-2 font-bold text-sm border-b-2 transition-colors",
                            activeTab === tab.id
                                ? "border-green-400 text-green-400"
                                : "border-transparent text-text-subtle hover:text-white hover:border-border-dark"
                        )}
                    >
                        <span className="material-symbols-outlined text-[20px]">{tab.icon}</span>
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-hidden bg-card-dark border border-border-dark rounded-xl p-6 relative flex flex-col print-content-wrapper">

                {/* Blocking Overlay for Generation */}
                {isGenerating && (
                    <div className="absolute inset-0 z-[100] bg-background-dark/80 backdrop-blur-sm flex flex-col items-center justify-center text-center p-8">
                        <div className="relative w-24 h-24 mb-6">
                            <div className="absolute inset-0 border-4 border-primary/20 rounded-full"></div>
                            <div className="absolute inset-0 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                            <div className="absolute inset-4 border-4 border-cyan-400/20 rounded-full animate-pulse"></div>
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">Generating report</h3>
                        <p className="text-text-subtle mb-4 max-w-md">
                            Collecting financials, DART filings, and recent news for the report.
                        </p>
                        <div className="bg-primary/10 border border-primary/30 px-6 py-3 rounded-full text-primary font-bold animate-bounce shadow-lg shadow-primary/20">
                            {generationStatus}
                        </div>
                        <p className="mt-8 text-[10px] text-gray-500 italic">
                            * Generation time depends on data availability.
                        </p>
                    </div>
                )}

                {/* Library Tab */}
                {activeTab === 'library' && (
                    <div className="flex flex-col gap-4 h-full overflow-y-auto no-print">
                        <div className="flex justify-between items-center mb-2">
                            <h2 className="text-lg font-bold text-white">Report Library</h2>
                            <button
                                onClick={() => setActiveTab('builder')}
                                className="bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2"
                            >
                                <span className="material-symbols-outlined text-[18px]">add</span>
                                Create report
                            </button>
                        </div>
                        <div className="border border-border-dark rounded-lg overflow-hidden">
                            <table className="w-full text-sm">
                                <thead className="bg-[#151e1d] text-text-subtle">
                                    <tr>
                                        <th className="px-4 py-3 text-left">Company</th>
                                        <th className="px-4 py-3 text-left">Created At</th>
                                        <th className="px-4 py-3 text-left">Status</th>
                                        <th className="px-4 py-3 text-center">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border-dark/50">
                                    {reports.map((r) => (
                                        <tr key={r.id} className="hover:bg-white/5 text-gray-300">
                                            <td className="px-4 py-3">
                                                <div className="flex flex-col">
                                                    <span className="text-white font-bold">{r.company_name}</span>
                                                    <span className="text-xs text-text-subtle">{r.template}</span>
                                                </div>
                                            </td>
                                            <td className="px-4 py-3">{new Date(r.created_at).toLocaleString()}</td>
                                            <td className="px-4 py-3">
                                                <span className={clsx(
                                                    "px-2 py-0.5 rounded text-[10px] font-bold",
                                                    r.status === 'DONE' ? "bg-green-500/20 text-green-500" : "bg-blue-500/20 text-blue-500"
                                                )}>
                                                    {r.status}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3">
                                                <div className="flex items-center justify-center gap-2">
                                                    {/* Download DOCX */}
                                                    <button
                                                        onClick={() => {
                                                            const link = document.createElement('a');
                                                            link.href = `${apiBaseUrl}/reports/${r.id}/download`;
                                                            link.download = `report_${r.id}.docx`;
                                                            link.click();
                                                        }}
                                                        className="text-blue-400 hover:bg-blue-400/10 p-2 rounded-lg transition-colors flex items-center justify-center"
                                                        title="?ㅼ슫濡쒕뱶"
                                                    >
                                                        <span className="material-symbols-outlined text-[20px]">download</span>
                                                    </button>

                                                    {/* View */}
                                                    <button
                                                        onClick={() => fetchReportDetail(r.id)}
                                                        className="text-cyan-300 hover:bg-cyan-300/10 p-2 rounded-lg transition-colors flex items-center justify-center"
                                                        title="由ы룷??蹂닿린"
                                                    >
                                                        <span className="material-symbols-outlined text-[20px]">visibility</span>
                                                    </button>

                                                    {/* Delete */}
                                                    <button
                                                        onClick={() => handleDeleteReport(r.id)}
                                                        className="text-red-500 hover:bg-red-500/10 p-2 rounded-lg transition-colors flex items-center justify-center"
                                                        title="由ы룷????젣"
                                                    >
                                                        <span className="material-symbols-outlined text-[20px]">delete</span>
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                    {reports.length === 0 && (
                                        <tr>
                                            <td colSpan={4} className="px-4 py-8 text-center text-text-subtle">
                                                ?앹꽦??由ы룷?멸? ?놁뒿?덈떎.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Builder Tab */}
                {activeTab === 'builder' && (
                    <div className="flex flex-col h-full overflow-y-auto max-w-2xl mx-auto w-full py-8 no-print">
                        <h2 className="text-xl font-bold text-white mb-6">AI Report Builder</h2>

                        <div className="space-y-6">
                            <div className="flex flex-col gap-2">
                                <label className="text-sm font-bold text-text-subtle">Company Search</label>
                                <div className="relative">
                                    <input
                                        type="text"
                                        placeholder="Search company name or ticker"
                                        value={searchTerm}
                                        onChange={(e) => searchCompanies(e.target.value)}
                                        className="w-full bg-background-dark border border-border-dark rounded-lg px-4 py-3 text-white outline-none focus:border-primary"
                                    />
                                    {isSearching && (
                                        <span className="absolute right-4 top-3.5 w-4 h-4 border-2 border-primary/30 border-t-primary rounded-full animate-spin"></span>
                                    )}
                                    {searchResults.length > 0 && (
                                        <div className="absolute top-full left-0 right-0 z-[100] mt-2 bg-card-dark border border-border-dark rounded-lg shadow-2xl overflow-hidden max-h-60 overflow-y-auto">
                                            {searchResults.map(c => (
                                                <button
                                                    key={c.id}
                                                    onClick={() => handleSelectCompany(c)}
                                                    className="w-full text-left px-4 py-3 hover:bg-white/5 transition-colors border-b border-border-dark/30 last:border-0"
                                                >
                                                    <div className="flex justify-between items-center">
                                                        <span className="text-white font-bold">{c.name}</span>
                                                        <span className="text-xs text-text-subtle bg-background-dark px-2 py-0.5 rounded">{c.market} | {c.ticker}</span>
                                                    </div>
                                                    <div className="text-xs text-gray-500 mt-1">{c.sector}</div>
                                                </button>
                                            ))}
                                        </div>
                                    )}
                                </div>
                                {targetCompanyId && (
                                    <p className="text-xs text-primary font-bold mt-1">Selected: {selectedCompanyName} (ID: {targetCompanyId})</p>
                                )}
                                <div className="mt-4">
                                    <DocumentManager companyId={targetCompanyId} />
                                </div>
                            </div>

                            <div className="flex flex-col gap-2">
                                <label className="text-sm font-bold text-text-subtle">Template</label>
                                <select
                                    value={template}
                                    onChange={(e) => setTemplate(e.target.value)}
                                    className="bg-background-dark border border-border-dark rounded-lg px-4 py-3 text-white outline-none focus:border-primary"
                                >
                                    <optgroup label="Public Companies (DART)">
                                        <option value="investment_memo_vc_v1">VC Investment Memo</option>
                                        <option value="investment_memo_v1">Company Memo</option>
                                    </optgroup>
                                    <optgroup label="Private Companies" disabled>
                                        <option value="startup_brief">Startup Brief</option>
                                    </optgroup>
                                </select>
                            </div>

                            <button
                                onClick={handleCreateReport}
                                disabled={isGenerating || !targetCompanyId}
                                className="w-full bg-primary hover:bg-blue-600 disabled:bg-gray-700 text-white font-bold py-4 rounded-xl shadow-lg shadow-primary/20 flex items-center justify-center gap-2"
                            >
                                {isGenerating ? (
                                    <>
                                        <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                                        Generating report...
                                    </>
                                ) : (
                                    <>
                                        <span className="material-symbols-outlined">auto_awesome</span>
                                        Generate Report
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                )}

                {activeTab === 'preview' && (
                    <div className="h-full flex flex-col gap-4">
                        <div className="flex justify-between items-center border-b border-border-dark pb-4 no-print">
                            <h2 className="text-lg font-bold text-white flex items-center gap-2">
                                <span className="material-symbols-outlined text-primary">description</span>
                                Report Preview
                            </h2>
                            <button
                                onClick={handleDownloadPdf}
                                disabled={!reportContent}
                                className="flex items-center gap-2 text-sm text-cyan-300 hover:text-cyan-100 transition-colors bg-cyan-400/10 px-3 py-1.5 rounded-lg disabled:opacity-50"
                            >
                                <span className="material-symbols-outlined text-[20px]">print</span>
                                Print / PDF (Clean Print)
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto bg-background-dark/50 rounded-lg p-0 border border-border-dark shadow-inner print:overflow-visible print:bg-white print:border-none print:shadow-none">
                            <div
                                ref={reportRef}
                                className="bg-white text-black p-12 min-h-full shadow-2xl mx-auto w-[210mm] report-print-container"
                            >
                                <div className="prose prose-slate max-w-none">
                                    {/* Check if content is HTML (from DOCX) */}
                                    {reportContent.includes('<p>') || reportContent.includes('<table>') ? (
                                        <div dangerouslySetInnerHTML={{ __html: reportContent }} />
                                    ) : (
                                        /* Original markdown rendering for MD files */
                                        reportContent.split(':::chart-financial-annual:::').map((part, idx) => (
                                            <div key={idx}>
                                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                    {part}
                                                </ReactMarkdown>
                                                {/* Render Chart between parts if not the last part */}
                                                {idx < reportContent.split(':::chart-financial-annual:::').length - 1 && selectedReportId && (
                                                    <div className="my-8 h-[300px] w-full border border-gray-200 rounded p-4 break-inside-avoid page-break-inside-avoid">
                                                        <h3 className="text-center mb-4 text-sm font-bold">?щТ?ㅼ쟻(Financial Performance)</h3>
                                                        <ReportChartLoader reportId={selectedReportId} />
                                                    </div>
                                                )}
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <style>{`
                @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');

                .report-print-container { 
                    font-family: 'Noto Sans KR', 'Malgun Gothic', dotum, sans-serif !important;
                    font-size: 0.8rem; /* Restore to original small readable size */
                    line-height: 1.6;
                    color: #222;
                    letter-spacing: -0.01em;
                }
                /* ... keep h1, h2 styles ... */
                .report-print-container h1 { 
                    font-size: 1.1rem; 
                    font-weight: 800; 
                    color: #0ea5e9; 
                    margin-bottom: 0px; 
                    border-bottom: 2.5px solid #0ea5e9; 
                    padding-bottom: 6px;
                    text-align: left;
                    letter-spacing: 0.05em;
                    display: block;
                    width: 100%;
                    text-transform: uppercase;
                }
                .report-print-container h2 { 
                    font-size: 2.4rem; 
                    font-weight: 800; 
                    color: #000; 
                    margin-top: 20px; 
                    margin-bottom: 10px; 
                    text-align: left;
                    line-height: 1.1;
                    letter-spacing: -0.04em;
                    border: none;
                    padding: 0;
                }
                .report-print-container p:first-of-type {
                    margin-top: 0;
                    margin-bottom: 40px;
                    font-size: 1.1rem;
                    color: #111;
                    font-weight: 500;
                }
                
                /* RESTORED STABLE STYLES FOR CONTENT */
                .report-print-container h3,
                .report-print-container .prose h3 {
                    font-size: 1.3rem !important; 
                    font-weight: 800 !important;
                    color: #000;
                    margin-top: 2rem;
                    margin-bottom: 1rem;
                    border-bottom: 2px solid #ddd;
                    padding-bottom: 5px;
                }

                .report-print-container ul, .report-print-container ol { margin-bottom: 0.8rem; padding-left: 1.2rem; }
                .report-print-container li { margin-bottom: 0.3rem; color: #333; }
                
                .report-print-container table {
                    font-size: 0.8rem !important;
                    width: 95%; /* CENTER ALIGN TABLE */
                    margin: 1.5rem auto; 
                    border-collapse: collapse;
                    border-top: 2px solid #444; 
                    border-bottom: 2px solid #444;
                }
                .report-print-container th {
                    background-color: #f3f4f6 !important; 
                    font-weight: 700;
                    text-align: center !important;
                    border: 1px solid #d1d5db; 
                    padding: 8px 6px;
                    color: #111;
                }
                .report-print-container td {
                    border: 1px solid #d1d5db; 
                    padding: 6px 8px;
                    color: #333;
                }
                .report-print-container td:first-child {
                    text-align: left;
                    font-weight: 600;
                    background-color: #fcfcfc;
                }
            `}</style>
        </div>
    );
}

