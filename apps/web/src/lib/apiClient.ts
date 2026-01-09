import axios from 'axios';

// Simple types for API responses (can be expanded)
export interface ApiResponse<T> {
    data: T;
    message?: string;
    status: number;
}

// We don't export a singleton instance because base URL can change at runtime via Settings.
// Instead, we provide a helper to get a configured instance or just use a hook.
// But for React Query 'queryFn', we might just pass the URL.

export const createApiClient = (baseURL: string) => {
    return axios.create({
        baseURL,
        headers: {
            'Content-Type': 'application/json',
        },
    });
};
