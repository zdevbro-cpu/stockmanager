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

export const useRecommendations = () => {
    const { isDemoMode, apiBaseUrl } = useSettings();
    return useQuery({
        queryKey: ['recommendations'],
        queryFn: async () => {
            if (isDemoMode) return RECOMENDATIONS;
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/recommendations');
            return data;
        },
    });
};

export const useSignals = () => {
    const { isDemoMode, apiBaseUrl } = useSettings();
    return useQuery({
        queryKey: ['signals'],
        queryFn: async () => {
            if (isDemoMode) return SIGNALS;
            const client = createApiClient(apiBaseUrl);
            const { data } = await client.get('/signals');
            return data;
        },
    });
};

