import { useQuery } from '@tanstack/react-query';
import { useSettings } from '../contexts/SettingsContext';
import { createApiClient } from '../lib/apiClient';
import { TOP_INDICES, INVESTOR_TRENDS, POPULAR_SEARCHES, THEME_RANKINGS, INDUSTRY_RANKINGS, RECOMENDATIONS, SIGNALS } from '../lib/mockData';

// Types (should ideally be in a shared type file or generated)
export interface IndexData {
    name: string;
    value: string;
    change: string;
    changePercent: string;
    up: boolean;
}

// Hooks

export const useTopIndices = () => {
    const { isDemoMode, apiBaseUrl } = useSettings();
    return useQuery({
        queryKey: ['indices'],
        queryFn: async () => {
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/indices');
            return data;
        },
        staleTime: 60000,
        refetchInterval: 900000,
    });
};

export const useInvestorTrends = () => {
    const { isDemoMode, apiBaseUrl } = useSettings();
    return useQuery({
        queryKey: ['investorTrends'],
        queryFn: async () => {
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/investor-trends'); // Endpoint assumed
            return data;
        },
    });
};

export const usePopularSearches = () => {
    const { isDemoMode, apiBaseUrl } = useSettings();
    return useQuery({
        queryKey: ['popularSearches'],
        queryFn: async () => {
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/popular-searches');
            return data;
        },
    });
};

export const useAllPopularSearches = () => {
    const { isDemoMode, apiBaseUrl } = useSettings();
    return useQuery({
        queryKey: ['allPopularSearches'],
        queryFn: async () => {
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/popular-searches/all');
            return data;
        },
    });
};

export const useThemeRankings = () => {
    const { isDemoMode, apiBaseUrl } = useSettings();
    return useQuery({
        queryKey: ['themeRankings'],
        queryFn: async () => {
            // Force API call to avoid stale mock data
            // if (isDemoMode) return THEME_RANKINGS; 
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/themes/rankings');
            return data;
        },
    });
};

export const useIndustryRankings = () => {
    const { isDemoMode, apiBaseUrl } = useSettings();
    return useQuery({
        queryKey: ['industryRankings'],
        queryFn: async () => {
            // Force API call
            // if (isDemoMode) return INDUSTRY_RANKINGS;
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/industries/rankings');
            return data;
        },
    });
};

export const useAllThemes = () => {
    const { isDemoMode, apiBaseUrl } = useSettings();
    return useQuery({
        queryKey: ['allThemes'],
        queryFn: async () => {
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/themes/all');
            return data;
        },
    });
};

export const useAllIndustries = () => {
    const { isDemoMode, apiBaseUrl } = useSettings();
    return useQuery({
        queryKey: ['allIndustries'],
        queryFn: async () => {
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/industries/all');
            return data;
        },
    });
};

export const useIndustryNodes = () => {
    const { apiBaseUrl } = useSettings();
    return useQuery({
        queryKey: ['industryNodes'],
        queryFn: async () => {
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/classifications/nodes', {
                params: {
                    taxonomy_id: 'KIS_INDUSTRY',
                },
            });
            return data?.items ?? [];
        },
        staleTime: 60000,
    });
};

export const useIndexChart = (market: string) => {
    const { apiBaseUrl } = useSettings();
    return useQuery({
        queryKey: ['indexChart', market],
        queryFn: async () => {
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/indices/chart', {
                params: {
                    market,
                    days: 30,
                    interval: '1d',
                },
            });
            return data;
        },
        staleTime: 60000,
    });
};

export const useUniverse = (params: Record<string, unknown>) => {
    const { apiBaseUrl } = useSettings();
    return useQuery({
        queryKey: ['universe', params],
        queryFn: async () => {
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/universe', { params });
            return data;
        },
        staleTime: 60000,
    });
};

export const useRecommendations = (params?: {
    as_of_date?: string;
    strategy_id?: string;
    strategy_version?: string;
}) => {
    const { isDemoMode, apiBaseUrl } = useSettings();
    return useQuery({
        queryKey: ['recommendations', params],
        queryFn: async () => {
            if (isDemoMode) return RECOMENDATIONS;
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/recommendations', { params });
            if (Array.isArray(data)) return data;
            return data?.items ?? [];
        },
        retry: false,
    });
};

export const useStrategies = () => {
    const { apiBaseUrl } = useSettings();
    return useQuery({
        queryKey: ['strategies'],
        queryFn: async () => {
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/strategies');
            if (Array.isArray(data)) return data;
            return data?.items ?? [];
        },
        staleTime: 60000,
        retry: false,
    });
};

export const useRecommendationRunStatus = () => {
    const { apiBaseUrl } = useSettings();
    return useQuery({
        queryKey: ['recommendations-run-status'],
        queryFn: async () => {
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/recommendations/run-status');
            return data;
        },
        staleTime: 10000,
        retry: false,
    });
};

const buildSignalReason = (row: any) => {
    if (Array.isArray(row?.risk_flags) && row.risk_flags.length > 0) {
        if (row.risk_flags.includes('NO_PRICE_DATA')) {
            return '데이터 부족: price_daily 데이터 없음';
        }
        if (row.risk_flags.includes('INSUFFICIENT_HISTORY')) {
            return '데이터 부족: 최근 가격 이력 부족';
        }
        return row.risk_flags.join(', ');
    }
    if (Array.isArray(row?.triggers) && row.triggers.length > 0) {
        return row.triggers.join(', ');
    }
    if (row?.confidence !== null && row?.confidence !== undefined) {
        return `Confidence ${Number(row.confidence).toFixed(2)}`;
    }
    return '-';
};

export const useSignals = (params?: { horizon?: string; ticker?: string; tickers?: string[] }) => {
    const { isDemoMode, apiBaseUrl } = useSettings();
    return useQuery({
        queryKey: ['signals', params],
        queryFn: async () => {
            if (isDemoMode) return SIGNALS;
            const client = createApiClient(apiBaseUrl);
            const requestParams = {
                ...params,
                tickers: params?.tickers?.join(','),
            };
            const { data } = await client.get('/signals', { params: requestParams });
            const items = Array.isArray(data) ? data : data?.items ?? [];
            return items.map((row: any) => ({
                date: row.ts ? String(row.ts).slice(0, 10) : row.date,
                name: row.name ?? row.ticker ?? '-',
                ticker: row.ticker ?? '-',
                type: row.signal ?? row.type ?? 'WAIT',
                price: row.price ?? '-',
                reason: row.reason ?? buildSignalReason(row),
                horizon: row.horizon ?? params?.horizon ?? '-',
                target_price_low: row.target_price_low ?? null,
                target_price_high: row.target_price_high ?? null,
                target_price_basis: row.target_price_basis ?? null,
            }));
        },
    });
};

