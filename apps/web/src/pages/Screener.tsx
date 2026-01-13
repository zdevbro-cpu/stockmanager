import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { RECOMENDATIONS } from '../lib/mockData';
import clsx from 'clsx';
import { useAllIndustries, useAllThemes, useIndustryNodes, useUniverse } from '../hooks/useStockData';
import { createApiClient } from '../lib/apiClient';
import { useSettings } from '../contexts/SettingsContext';

// Mock large list for the table
const MOCK_SCREENER_RESULTS = [
    ...RECOMENDATIONS.map(r => ({ ...r, market: 'KOSPI', price: 72000, turnover: 500000000, sector: '반도체' })),
    { rank: 6, ticker: '005490', name: 'POSCO홀딩스', market: 'KOSPI', price: 450000, turnover: 300000000, sector: '철강', target: 'WAIT', score: 60, weight: '0%' },
    { rank: 7, ticker: '035720', name: '카카오', market: 'KOSPI', price: 54300, turnover: 150000000, sector: '서비스', target: 'HOLD', score: 55, weight: '0%' },
    { rank: 8, ticker: '247540', name: '에코프로비엠', market: 'KOSDAQ', price: 280000, turnover: 800000000, sector: '2차전지', target: 'BUY', score: 82, weight: '0%' },
    { rank: 9, ticker: '068270', name: '셀트리온', market: 'KOSPI', price: 180000, turnover: 120000000, sector: '의약품', target: 'WAIT', score: 58, weight: '0%' },
    // Duplicate for scroll
    { rank: 10, ticker: '000270', name: '기아', market: 'KOSPI', price: 95000, turnover: 220000000, sector: '자동차', target: 'BUY', score: 75, weight: '0%' },
];

const FILTER_STORAGE_KEY = 'stockmanager_screener_filters';
const CUSTOM_THEMES_KEY = 'stockmanager_screener_custom_themes';
const HIDDEN_THEMES_KEY = 'stockmanager_screener_hidden_themes';
const turnoverLabel = '\uac70\ub798\ub300\uae08';

export default function Screener() {
    const { apiBaseUrl } = useSettings();
    const { data: themeData } = useAllThemes();
    const { data: industryNodes } = useIndustryNodes();
    const { data: industryData } = useAllIndustries();

    const [priceMin, setPriceMin] = useState<string>('');
    const [industryQuery, setIndustryQuery] = useState<string>('');
    const [themeQuery, setThemeQuery] = useState<string>('');
    const [customThemeInput, setCustomThemeInput] = useState<string>('');
    const [selectedIndustries, setSelectedIndustries] = useState<string[]>([]);
    const [selectedThemes, setSelectedThemes] = useState<string[]>([]);
    const [customThemes, setCustomThemes] = useState<string[]>([]);
    const [hiddenThemes, setHiddenThemes] = useState<string[]>([]);
    const [pageSize, setPageSize] = useState<number>(50);
    const [pageIndex, setPageIndex] = useState<number>(1);

    useEffect(() => {
        const stored = localStorage.getItem(FILTER_STORAGE_KEY);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                setPriceMin(parsed.priceMin || '');
                if (Array.isArray(parsed.selectedIndustries)) {
                    const normalized = parsed.selectedIndustries.map((value: string) => (
                        value.includes(':') ? value : `name:${value}`
                    ));
                    setSelectedIndustries(normalized);
                } else {
                    setSelectedIndustries([]);
                }
                setSelectedThemes(Array.isArray(parsed.selectedThemes) ? parsed.selectedThemes : []);
            } catch {
                // Ignore malformed storage
            }
        }

        const storedCustom = localStorage.getItem(CUSTOM_THEMES_KEY);
        if (storedCustom) {
            try {
                const parsed = JSON.parse(storedCustom);
                setCustomThemes(Array.isArray(parsed) ? parsed : []);
            } catch {
                // Ignore malformed storage
            }
        }

        const storedHidden = localStorage.getItem(HIDDEN_THEMES_KEY);
        if (storedHidden) {
            try {
                const parsed = JSON.parse(storedHidden);
                setHiddenThemes(Array.isArray(parsed) ? parsed : []);
            } catch {
                // Ignore malformed storage
            }
        }
    }, []);

    useEffect(() => {
        localStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify({
            priceMin,
            selectedIndustries,
            selectedThemes,
        }));
    }, [priceMin, selectedIndustries, selectedThemes]);

    useEffect(() => {
        localStorage.setItem(CUSTOM_THEMES_KEY, JSON.stringify(customThemes));
    }, [customThemes]);

    useEffect(() => {
        localStorage.setItem(HIDDEN_THEMES_KEY, JSON.stringify(hiddenThemes));
    }, [hiddenThemes]);

    useEffect(() => {
        setPageIndex(1);
    }, [priceMin, selectedIndustries, selectedThemes, industryQuery, themeQuery]);

    const minPrice = priceMin.trim() ? Number(priceMin) : undefined;
    const selectedIndustryCodes = selectedIndustries
        .filter((key) => key.startsWith('code:'))
        .map((key) => key.replace(/^code:/, ''));
    const selectedIndustryNames = selectedIndustries
        .filter((key) => key.startsWith('name:'))
        .map((key) => key.replace(/^name:/, ''));

    const { data: industryMembers } = useQuery({
        queryKey: ['industryMembers', selectedIndustryNames],
        queryFn: async () => {
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/industries/members', {
                params: { names: selectedIndustryNames.join(',') },
            });
            return Array.isArray(data?.items) ? data.items : [];
        },
        enabled: selectedIndustryNames.length > 0,
        staleTime: 60000,
    });
    const industryMemberSet = useMemo(() => new Set(industryMembers ?? []), [industryMembers]);
    const { data: themeMembers } = useQuery({
        queryKey: ['themeMembers', selectedThemes],
        queryFn: async () => {
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/themes/members', {
                params: { names: selectedThemes.join(',') },
            });
            return Array.isArray(data?.items) ? data.items : [];
        },
        enabled: selectedThemes.length > 0,
        staleTime: 60000,
    });
    const themeMemberSet = useMemo(() => new Set(themeMembers ?? []), [themeMembers]);
    const { data: universeData } = useUniverse({
        min_price_krw: Number.isFinite(minPrice) ? minPrice : undefined,
        include_industry_codes: selectedIndustryCodes.length > 0 ? selectedIndustryCodes.join(',') : undefined,
        include_industry_names: selectedIndustryNames.length > 0 ? selectedIndustryNames.join(',') : undefined,
    });

    const universeItems = useMemo(() => (
        Array.isArray(universeData?.items) ? universeData.items : []
    ), [universeData]);

    const industryOptions = useMemo(() => {
        if (Array.isArray(industryNodes) && industryNodes.length > 0) {
            return industryNodes
                .filter((item: any) => item?.code && item?.name)
                .map((item: any) => ({ key: `code:${item.code}`, name: item.name }))
                .sort((a, b) => a.name.localeCompare(b.name));
        }

        if (universeItems.length > 0) {
            const names = new Set<string>();
            universeItems.forEach((item: any) => {
                if (item.sector_name) {
                    names.add(item.sector_name);
                }
            });
            if (names.size > 0) {
                return Array.from(names)
                    .map((name) => ({ key: `name:${name}`, name }))
                    .sort((a, b) => a.name.localeCompare(b.name));
            }
        }

        if (Array.isArray(industryData) && industryData.length > 0) {
            return industryData
                .filter((item: any) => item?.name)
                .map((item: any) => ({ key: `name:${item.name}`, name: item.name }))
                .sort((a, b) => a.name.localeCompare(b.name));
        }

        return [];
    }, [industryNodes, industryData, universeItems]);

    const industryNameByKey = useMemo(() => {
        const map = new Map<string, string>();
        industryOptions.forEach((item) => map.set(item.key, item.name));
        return map;
    }, [industryOptions]);

    const themeNames = useMemo(() => {
        const scraped = Array.isArray(themeData) ? themeData.map((item: any) => item.name) : [];
        const merged = new Set<string>([...scraped, ...customThemes]);
        return Array.from(merged).filter((name) => !hiddenThemes.includes(name)).sort((a, b) => a.localeCompare(b));
    }, [themeData, customThemes, hiddenThemes]);

    const filteredIndustries = useMemo(() => {
        if (!industryQuery.trim()) return industryOptions;
        const q = industryQuery.toLowerCase();
        return industryOptions.filter((item) => item.name.toLowerCase().includes(q));
    }, [industryOptions, industryQuery]);

    const filteredThemes = useMemo(() => {
        if (!themeQuery.trim()) return themeNames;
        const q = themeQuery.toLowerCase();
        return themeNames.filter((name) => name.toLowerCase().includes(q));
    }, [themeNames, themeQuery]);

    const tableItems = useMemo(() => {
        const items = universeItems;
        if (items.length === 0) {
            return [];
        }

        let filtered = items;
        if (selectedIndustries.length > 0) {
            const hasSectorData = filtered.some((item: any) => item.sector_code || item.sector_name);
            if (hasSectorData) {
                filtered = filtered.filter((item: any) => {
                    const sectorCode = item.sector_code ? `code:${item.sector_code}` : null;
                    const sectorName = item.sector_name ? `name:${item.sector_name}` : null;
                    return selectedIndustries.some((key) => key === sectorCode || key === sectorName);
                });
            }
            if (selectedIndustryNames.length > 0 && industryMemberSet.size > 0) {
                filtered = filtered.filter((item: any) => industryMemberSet.has(item.ticker));
            }
        }

        if (selectedThemes.length > 0 && Array.isArray(themeMembers)) {
            filtered = filtered.filter((item: any) => themeMemberSet.has(item.ticker));
        }

        const turnoverValues = filtered
            .map((item: any) => Number(item.avg_turnover_krw_20d))
            .filter((value: number) => Number.isFinite(value) && value > 0)
            .sort((a, b) => a - b);
        const rankByValue = new Map<number, number>();
        turnoverValues.forEach((value, idx) => {
            rankByValue.set(value, idx);
        });
        const denom = turnoverValues.length > 1 ? turnoverValues.length - 1 : 1;

        return filtered.map((item: any, index: number) => {
            const turnoverValue = Number(item.avg_turnover_krw_20d);
            const score = turnoverValues.length > 0 && Number.isFinite(turnoverValue) && turnoverValue > 0
                ? Math.max(1, Math.round(((rankByValue.get(turnoverValue) ?? 0) / denom) * 100))
                : '-';
            return {
            rank: index + 1,
            ticker: item.ticker,
            name: item.name_ko,
            market: item.market,
            sector: item.sector_name || '-',
            sector_code: item.sector_code || null,
            price: item.last_price_krw ?? null,
            turnover: item.avg_turnover_krw_20d ?? null,
            target: item.signal ?? '-',
            score,
        };
        });
    }, [universeItems, selectedIndustries, selectedThemes, selectedIndustryNames, industryMemberSet, themeMemberSet, themeMembers]);

    const totalPages = useMemo(() => (
        Math.max(1, Math.ceil(tableItems.length / pageSize))
    ), [tableItems.length, pageSize]);

    const pagedItems = useMemo(() => {
        const start = (pageIndex - 1) * pageSize;
        return tableItems.slice(start, start + pageSize);
    }, [tableItems, pageIndex, pageSize]);

    const toggleIndustry = (key: string) => {
        if (selectedIndustries.includes(key)) {
            setSelectedIndustries(selectedIndustries.filter(i => i !== key));
        } else {
            setSelectedIndustries([...selectedIndustries, key]);
        }
    };

    const toggleTheme = (name: string) => {
        if (selectedThemes.includes(name)) {
            setSelectedThemes(selectedThemes.filter(t => t !== name));
        } else {
            setSelectedThemes([...selectedThemes, name]);
        }
    };

    const resetFilters = () => {
        setPriceMin('');
        setSelectedIndustries([]);
        setSelectedThemes([]);
        setIndustryQuery('');
        setThemeQuery('');
    };

    const prevSelectedIndustries = useRef<number>(0);
    useEffect(() => {
        if (prevSelectedIndustries.current > 0 && selectedIndustries.length === 0) {
            setIndustryQuery('');
        }
        prevSelectedIndustries.current = selectedIndustries.length;
    }, [selectedIndustries]);

    const prevSelectedThemes = useRef<number>(0);
    useEffect(() => {
        if (prevSelectedThemes.current > 0 && selectedThemes.length === 0) {
            setThemeQuery('');
        }
        prevSelectedThemes.current = selectedThemes.length;
    }, [selectedThemes]);

    const addCustomTheme = () => {
        const value = customThemeInput.trim();
        if (!value) return;
        if (!themeNames.includes(value)) {
            setCustomThemes((prev) => [...prev, value]);
        }
        setHiddenThemes((prev) => prev.filter((name) => name !== value));
        setCustomThemeInput('');
    };

    const hideTheme = (name: string) => {
        setHiddenThemes((prev) => (prev.includes(name) ? prev : [...prev, name]));
        setSelectedThemes((prev) => prev.filter((item) => item !== name));
        setCustomThemes((prev) => prev.filter((item) => item !== name));
    };

    const restoreTheme = (name: string) => {
        setHiddenThemes((prev) => prev.filter((item) => item !== name));
    };

    return (
        <div className="flex flex-col gap-6 max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white">발굴 (Screener)</h1>
                    <p className="text-text-subtle text-sm mt-1">
                        업종/테마 필터를 조합해 관심 종목을 빠르게 추립니다.
                    </p>
                </div>
                <button
                    onClick={resetFilters}
                    className="text-xs text-primary font-bold hover:underline"
                >
                    필터 초기화
                </button>
            </div>

            <section className="bg-card-dark border border-border-dark rounded-xl p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="flex flex-col gap-4">
                    <div className="flex flex-col gap-2">
                        <label className="text-sm font-bold text-text-subtle">최소 주가 (KRW)</label>
                        <input
                            type="number"
                            placeholder="예: 10000"
                            value={priceMin}
                            onChange={(e) => setPriceMin(e.target.value)}
                            className="bg-background-dark border border-border-dark rounded-lg px-3 py-2 text-white focus:border-primary outline-none"
                        />
                    </div>
                    <div className="flex flex-col gap-2">
                        <label className="text-sm font-bold text-text-subtle">선택된 업종</label>
                        <div className="flex flex-wrap gap-2 min-h-[36px]">
                            {selectedIndustries.length === 0 ? (
                                <span className="text-xs text-text-subtle">선택 없음</span>
                            ) : (
                                selectedIndustries.map((key) => (
                                    <span key={key} className="px-2 py-1 rounded-full text-xs bg-primary/15 text-primary border border-primary/30">
                                        {industryNameByKey.get(key) || key.replace(/^name:|^code:/, '')}
                                    </span>
                                ))
                            )}
                        </div>
                    </div>
                    <div className="flex flex-col gap-2">
                        <label className="text-sm font-bold text-text-subtle">선택된 테마</label>
                        <div className="flex flex-wrap gap-2 min-h-[36px]">
                            {selectedThemes.length === 0 ? (
                                <span className="text-xs text-text-subtle">선택 없음</span>
                            ) : (
                                selectedThemes.map((name) => (
                                    <span key={name} className="px-2 py-1 rounded-full text-xs bg-primary/15 text-primary border border-primary/30">
                                        {name}
                                    </span>
                                ))
                            )}
                        </div>
                    </div>
                </div>

                <div className="flex flex-col gap-3">
                    <div className="flex items-center justify-between">
                        <label className="text-sm font-bold text-text-subtle">업종 필터</label>
                        <span className="text-xs text-text-subtle">{industryOptions.length}개</span>
                    </div>
                    <input
                        type="text"
                        placeholder="업종 검색"
                        value={industryQuery}
                        onChange={(e) => setIndustryQuery(e.target.value)}
                        className="bg-background-dark border border-border-dark rounded-lg px-3 py-2 text-white focus:border-primary outline-none"
                    />
                    <div className="flex flex-col gap-1 max-h-56 overflow-y-auto pr-1">
                        {filteredIndustries.map((item) => (
                            <label key={item.key} className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer hover:text-white">
                                <input
                                    type="checkbox"
                                    className="rounded border-border-dark bg-background-dark text-primary focus:ring-primary"
                                    checked={selectedIndustries.includes(item.key)}
                                    onChange={() => toggleIndustry(item.key)}
                                />
                                {item.name}
                            </label>
                        ))}
                        {filteredIndustries.length === 0 && (
                            <span className="text-xs text-text-subtle">검색 결과 없음</span>
                        )}
                    </div>
                </div>

                <div className="flex flex-col gap-3">
                    <div className="flex items-center justify-between">
                        <label className="text-sm font-bold text-text-subtle">테마 필터</label>
                        <span className="text-xs text-text-subtle">{themeNames.length}개</span>
                    </div>
                    <input
                        type="text"
                        placeholder="테마 검색"
                        value={themeQuery}
                        onChange={(e) => setThemeQuery(e.target.value)}
                        className="bg-background-dark border border-border-dark rounded-lg px-3 py-2 text-white focus:border-primary outline-none"
                    />
                    <div className="flex flex-wrap gap-2 max-h-44 overflow-y-auto pr-1">
                        {filteredThemes.map((name) => (
                            <div key={name} className="flex items-center gap-1">
                                <button
                                    onClick={() => toggleTheme(name)}
                                    className={clsx(
                                        "px-2 py-1 rounded-full text-xs font-medium border transition-colors text-left",
                                        selectedThemes.includes(name)
                                            ? "bg-primary/20 border-primary text-primary"
                                            : "bg-background-dark border-border-dark text-gray-400 hover:border-gray-500"
                                    )}
                                >
                                    {name}
                                </button>
                                <button
                                    onClick={() => hideTheme(name)}
                                    className="text-xs text-text-subtle hover:text-white"
                                    title="Hide theme"
                                >
                                    Hide
                                </button>
                            </div>
                        ))}
                        {filteredThemes.length === 0 && (
                            <span className="text-xs text-text-subtle">검색 결과 없음</span>
                        )}
                    </div>
                    <div className="flex flex-col gap-2 border-t border-border-dark pt-3">
                        <label className="text-xs font-semibold text-text-subtle">테마 추가</label>
                        <div className="flex gap-2">
                            <input
                                type="text"
                                placeholder="새 테마 이름"
                                value={customThemeInput}
                                onChange={(e) => setCustomThemeInput(e.target.value)}
                                className="flex-1 bg-background-dark border border-border-dark rounded-lg px-3 py-2 text-white focus:border-primary outline-none"
                            />
                            <button
                                onClick={addCustomTheme}
                                className="px-3 py-2 bg-primary text-white rounded-lg text-xs font-bold hover:bg-primary/90"
                            >
                                추가
                            </button>
                        </div>
                    </div>
                    {hiddenThemes.length > 0 && (
                        <div className="flex flex-col gap-2 border-t border-border-dark pt-3">
                            <label className="text-xs font-semibold text-text-subtle">숨김된 테마</label>
                            <div className="flex flex-wrap gap-2">
                                {hiddenThemes.map((name) => (
                                    <button
                                        key={name}
                                        onClick={() => restoreTheme(name)}
                                        className="px-2 py-1 rounded-full text-xs border border-border-dark text-text-subtle hover:text-white hover:border-primary"
                                    >
                                        {name} 복구
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </section>

            <section className="bg-card-dark border border-border-dark rounded-xl overflow-hidden">
                <div className="p-4 border-b border-border-dark flex items-center justify-between bg-card-dark">
                    <div className="flex items-center gap-2">
                        <span className="text-white font-bold">Results</span>
                        <span className="bg-primary/20 text-primary text-xs font-bold px-2 py-0.5 rounded-full">{tableItems.length} items</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2 text-xs text-text-subtle">
                            <span>Rows</span>
                            <select
                                value={pageSize}
                                onChange={(e) => {
                                    setPageSize(Number(e.target.value));
                                    setPageIndex(1);
                                }}
                                className="bg-background-dark border border-border-dark rounded-md px-2 py-1 text-white text-xs"
                            >
                                {[50, 100, 200].map((size) => (
                                    <option key={size} value={size}>{size}</option>
                                ))}
                            </select>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-text-subtle">
                            <button
                                onClick={() => setPageIndex(1)}
                                disabled={pageIndex === 1}
                                className="px-2 py-1 border border-border-dark rounded-md disabled:opacity-40"
                            >
                                First
                            </button>
                            <button
                                onClick={() => setPageIndex((prev) => Math.max(1, prev - 1))}
                                disabled={pageIndex === 1}
                                className="px-2 py-1 border border-border-dark rounded-md disabled:opacity-40"
                            >
                                Prev
                            </button>
                            <span>{pageIndex} / {totalPages}</span>
                            <button
                                onClick={() => setPageIndex((prev) => Math.min(totalPages, prev + 1))}
                                disabled={pageIndex === totalPages}
                                className="px-2 py-1 border border-border-dark rounded-md disabled:opacity-40"
                            >
                                Next
                            </button>
                            <button
                                onClick={() => setPageIndex(totalPages)}
                                disabled={pageIndex === totalPages}
                                className="px-2 py-1 border border-border-dark rounded-md disabled:opacity-40"
                            >
                                Last
                            </button>
                        </div>
                        <div className="flex gap-2">
                            <button className="flex items-center gap-1 text-sm text-text-subtle hover:text-white px-3 py-1.5 border border-border-dark rounded-lg">
                                <span className="material-symbols-outlined text-[18px]">download</span>
                                Download
                            </button>
                        </div>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="text-text-subtle font-medium bg-background-dark">
                            <tr>
                                <th className="px-4 py-3 font-bold border-b border-border-dark">종목명 (Ticker)</th>
                                <th className="px-4 py-3 font-bold border-b border-border-dark">시장</th>
                                <th className="px-4 py-3 font-bold border-b border-border-dark">업종</th>
                                <th className="px-4 py-3 font-bold border-b border-border-dark text-right">현재가</th>
                                <th className="px-4 py-3 font-bold border-b border-border-dark text-right">{turnoverLabel}</th>
                                <th className="px-4 py-3 font-bold border-b border-border-dark text-center">신호</th>
                                <th className="px-4 py-3 font-bold border-b border-border-dark text-right">점수</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-dark/50">
                            {pagedItems.length === 0 && (
                                <tr>
                                    <td className="px-4 py-6 text-center text-sm text-text-subtle" colSpan={7}>
                                        조건에 맞는 결과가 없습니다.
                                    </td>
                                </tr>
                            )}
                            {pagedItems.map((item: any, i: number) => (
                                <tr key={i} className="hover:bg-white/5 transition-colors cursor-pointer text-gray-300">
                                    <td className="px-4 py-3">
                                        <div className="flex flex-col">
                                            <span className="text-white font-bold">{item.name}</span>
                                            <span className="text-text-subtle text-xs">{item.ticker}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3">
                                        {item.market === 'KRX_KOSPI'
                                            ? 'KOSPI'
                                            : item.market === 'KRX_KOSDAQ'
                                                ? 'KOSDAQ'
                                                : item.market || '-'}
                                    </td>
                                    <td className="px-4 py-3">{item.sector}</td>
                                    <td className="px-4 py-3 text-right font-medium text-white">
                                        {item.price === null || item.price === undefined
                                            ? '-'
                                            : Number(item.price).toLocaleString()}
                                    </td>
                                    <td className="px-4 py-3 text-right text-text-subtle">
                                        {item.turnover === null || item.turnover === undefined
                                            ? '-'
                                            : `${(Number(item.turnover) / 100000000).toFixed(1)}100M`}
                                    </td>
                                    <td className="px-4 py-3 text-center">
                                        <span className={clsx(
                                            "px-2 py-1 rounded text-xs font-bold",
                                            item.target === 'BUY' ? "bg-green-500/20 text-green-500" :
                                                item.target === 'SELL' ? "bg-red-500/20 text-red-500" :
                                                    item.target === 'WAIT' ? "bg-yellow-500/20 text-yellow-500" : "bg-gray-700 text-gray-400"
                                        )}>
                                            {item.target || '-'}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-right text-primary font-bold">
                                        {item.score === '-' || item.score === null || item.score === undefined
                                            ? '-'
                                            : item.score}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
    );
}