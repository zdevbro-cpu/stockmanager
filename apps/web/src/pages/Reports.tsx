import { useEffect, useState, useRef } from 'react';
import clsx from 'clsx';
import { useSettings } from '../contexts/SettingsContext';
import { createApiClient } from '../lib/apiClient';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type Tab = 'library' | 'builder' | 'preview';

interface ReportMeta {
    id: number;
    company_name: string;
    template: string;
    status: string;
    created_at: string;
}

export default function Reports() {
    const { apiBaseUrl } = useSettings();
    const [activeTab, setActiveTab] = useState<Tab>('builder');
    const [reports, setReports] = useState<ReportMeta[]>([]);
    const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
    const [reportContent, setReportContent] = useState<string>('');
    const [isGenerating, setIsGenerating] = useState(false);

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
            const resp = await client.get(`/search/company?q=${encodeURIComponent(val)}`);
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
            const resp = await client.get('/reports');
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
            alert("기업을 먼저 선택해주세요.");
            return;
        }
        setIsGenerating(true);
        try {
            const client = createApiClient(apiBaseUrl);
            await client.post('/reports', {
                company_id: parseInt(targetCompanyId),
                template: template
            }, {
                headers: { 'Authorization': 'Bearer dev-token' }
            });
            alert("리포트 생성이 백그라운드에서 시작되었습니다.");
            setActiveTab('library');
            fetchReports();
        } catch (error) {
            alert("리포트 생성 요청 실패");
        } finally {
            setIsGenerating(false);
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
        if (!confirm("이 리포트를 삭제하시겠습니까?")) return;
        try {
            const client = createApiClient(apiBaseUrl);
            await client.delete(`/reports/${id}`);
            fetchReports();
            if (selectedReportId === id) {
                setReportContent('');
                setSelectedReportId(null);
            }
        } catch (error) {
            alert("삭제 실패");
        }
    };

    useEffect(() => {
        fetchReports();
    }, [apiBaseUrl]);

    const TABS: { id: Tab; label: string; icon: string }[] = [
        { id: 'builder', label: '작성기 (Builder)', icon: 'edit_document' },
        { id: 'preview', label: '미리보기 (Preview)', icon: 'visibility' },
        { id: 'library', label: '라이브러리 (Library)', icon: 'library_books' },
    ];

    return (
        <div className="flex flex-col gap-6 max-w-7xl mx-auto h-[calc(100vh-100px)]">
            <h1 className="text-2xl font-bold text-white no-print">리포트 (Reports)</h1>

            {/* Tabs */}
            <div className="flex border-b border-border-dark no-print">
                {TABS.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={clsx(
                            "px-6 py-3 flex items-center gap-2 font-bold text-sm border-b-2 transition-colors",
                            activeTab === tab.id
                                ? "border-primary text-primary"
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

                {/* Library Tab */}
                {activeTab === 'library' && (
                    <div className="flex flex-col gap-4 h-full overflow-y-auto no-print">
                        <div className="flex justify-between items-center mb-2">
                            <h2 className="text-lg font-bold text-white">생성된 리포트 목록</h2>
                            <button
                                onClick={() => setActiveTab('builder')}
                                className="bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2"
                            >
                                <span className="material-symbols-outlined text-[18px]">add</span>
                                새 리포트 작성
                            </button>
                        </div>
                        <div className="border border-border-dark rounded-lg overflow-hidden">
                            <table className="w-full text-sm">
                                <thead className="bg-[#151e1d] text-text-subtle">
                                    <tr>
                                        <th className="px-4 py-3 text-left">제목/기업</th>
                                        <th className="px-4 py-3 text-left">생성일</th>
                                        <th className="px-4 py-3 text-left">상태</th>
                                        <th className="px-4 py-3 text-right">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border-dark/50">
                                    {reports.map((r) => (
                                        <tr key={r.id} className="hover:bg-white/5 text-gray-300">
                                            <td className="px-4 py-3">
                                                <div className="flex flex-col">
                                                    <span className="text-white font-bold">{r.company_name} 투자 분석</span>
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
                                            <td className="px-4 py-3 text-right">
                                                <div className="flex items-center justify-end gap-2">
                                                    <button
                                                        onClick={() => fetchReportDetail(r.id)}
                                                        className="text-cyan-300 hover:bg-cyan-300/10 p-2 rounded-lg transition-colors flex items-center justify-center"
                                                        title="리포트 보기"
                                                    >
                                                        <span className="material-symbols-outlined text-[20px]">visibility</span>
                                                    </button>
                                                    <button
                                                        onClick={() => handleDeleteReport(r.id)}
                                                        className="text-red-500 hover:bg-red-500/10 p-2 rounded-lg transition-colors flex items-center justify-center"
                                                        title="리포트 삭제"
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
                                                생성된 리포트가 없습니다.
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
                        <h2 className="text-xl font-bold text-white mb-6">AI 리포트 생성기</h2>

                        <div className="space-y-6">
                            <div className="flex flex-col gap-2 relative">
                                <label className="text-sm font-bold text-text-subtle">기업 검색 (이름 또는 종목코드)</label>
                                <div className="relative">
                                    <input
                                        type="text"
                                        placeholder="예: 금호석유, 005930"
                                        value={searchTerm}
                                        onChange={(e) => searchCompanies(e.target.value)}
                                        className="w-full bg-background-dark border border-border-dark rounded-lg px-4 py-3 text-white outline-none focus:border-primary"
                                    />
                                    {isSearching && (
                                        <span className="absolute right-4 top-3.5 w-4 h-4 border-2 border-primary/30 border-t-primary rounded-full animate-spin"></span>
                                    )}
                                </div>
                                {searchResults.length > 0 && (
                                    <div className="absolute top-full left-0 right-0 z-10 mt-2 bg-card-dark border border-border-dark rounded-lg shadow-2xl overflow-hidden max-h-60 overflow-y-auto">
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
                                {targetCompanyId && (
                                    <p className="text-xs text-primary font-bold mt-1">✓ 선택됨: {selectedCompanyName} (ID: {targetCompanyId})</p>
                                )}
                            </div>

                            <div className="flex flex-col gap-2">
                                <label className="text-sm font-bold text-text-subtle">리포트 템플릿</label>
                                <select
                                    value={template}
                                    onChange={(e) => setTemplate(e.target.value)}
                                    className="bg-background-dark border border-border-dark rounded-lg px-4 py-3 text-white outline-none focus:border-primary"
                                >
                                    <optgroup label="상장사 전용 (DART 연동)">
                                        <option value="investment_memo_vc_v1">투자 결정 검토서 (VC Style)</option>
                                        <option value="investment_memo_v1">기업 분석 미팅 메모</option>
                                    </optgroup>
                                    <optgroup label="비상장사 전용 (DeepSearch - 연동 예정)" disabled>
                                        <option value="startup_brief">스타트업 투자 요약</option>
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
                                        AI 분석 중... 자산/공시 데이터 로딩 중
                                    </>
                                ) : (
                                    <>
                                        <span className="material-symbols-outlined">auto_awesome</span>
                                        분석 보고서 생성 (Generate)
                                    </>
                                )}
                            </button>

                            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 mt-8">
                                <h4 className="text-blue-400 font-bold text-sm flex items-center gap-2 mb-2">
                                    <span className="material-symbols-outlined text-[18px]">info</span>
                                    비상장사 데이터 안내
                                </h4>
                                <p className="text-xs text-blue-300 leading-relaxed">
                                    현재 상장사 리포트 기능이 우선 구현되었습니다. 비상장사 분석은 <b>DeepSearch</b> 및 <b>혁신의숲 API</b> 연동을 통해 곧 지원될 예정입니다.
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Preview Tab */}
                {activeTab === 'preview' && (
                    <div className="h-full flex flex-col gap-4">
                        <div className="flex justify-between items-center border-b border-border-dark pb-4 no-print">
                            <h2 className="text-lg font-bold text-white flex items-center gap-2">
                                <span className="material-symbols-outlined text-primary">description</span>
                                리포트 미리보기
                            </h2>
                            <button
                                onClick={handleDownloadPdf}
                                disabled={!reportContent}
                                className="flex items-center gap-2 text-sm text-cyan-300 hover:text-cyan-100 transition-colors bg-cyan-400/10 px-3 py-1.5 rounded-lg disabled:opacity-50"
                            >
                                <span className="material-symbols-outlined text-[20px]">print</span>
                                PDF 인쇄/저장 (Clean Print)
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto bg-background-dark/50 rounded-lg p-0 border border-border-dark shadow-inner print:overflow-visible print:bg-white print:border-none print:shadow-none">
                            <div
                                ref={reportRef}
                                className="bg-white text-black p-12 min-h-full shadow-2xl mx-auto w-[210mm] report-print-container"
                            >
                                <div className="prose prose-slate max-w-none">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {reportContent || "_리포트 내용을 선택해주세요._"}
                                    </ReactMarkdown>
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
                    font-size: 0.78rem; 
                    line-height: 1.5;
                    color: #222;
                    letter-spacing: -0.025em;
                }
                /* ... keep h1, h2 styles ... */
                .report-print-container h1 { 
                    font-size: 0.85rem; 
                    font-weight: 500; 
                    color: #0891b2; 
                    margin-bottom: 0.2rem; 
                    border-bottom: 2px solid #0891b2; 
                    padding-bottom: 0.2rem;
                    text-align: left;
                    letter-spacing: 0.05em;
                    display: inline-block;
                }
                .report-print-container h2 { 
                    font-size: 1.8rem; 
                    font-weight: 900; 
                    color: #111; 
                    margin-top: 0.5rem; 
                    margin-bottom: 2rem; 
                    text-align: left;
                    line-height: 1.1;
                    letter-spacing: -0.03em;
                }
                /* Combined targeting for section titles */
                .report-print-container h3, 
                .report-print-container ol > li::marker,
                .report-print-container ol > li > strong:first-child,
                .report-print-container .prose h3 {
                    font-size: 0.8rem !important;
                    font-weight: 700 !important;
                    color: #000;
                }
                .report-print-container h3 {
                    margin-top: 1.6rem;
                    margin-bottom: 0.5rem;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 0.2rem;
                }
                .report-print-container ul, .report-print-container ol { margin-bottom: 0.8rem; padding-left: 1.2rem; }
                .report-print-container li { margin-bottom: 0.3rem; color: #333; }
            `}</style>
        </div>
    );
}
