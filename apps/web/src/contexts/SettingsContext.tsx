import { createContext, useContext, useState, ReactNode } from 'react';

interface SettingsContextType {
    apiBaseUrl: string;
    setApiBaseUrl: (url: string) => void;
    isDemoMode: boolean;
    setDemoMode: (isDemo: boolean) => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const SettingsProvider = ({ children }: { children: ReactNode }) => {
    // Initialize from localStorage or defaults
    const [apiBaseUrl, setApiBaseUrlState] = useState(() => {
        return localStorage.getItem('stockmanager_api_url') || 'http://localhost:8000';
    });
    const [isDemoMode, setDemoModeState] = useState(() => {
        const stored = localStorage.getItem('stockmanager_demo_mode');
        return stored === null ? true : stored === 'true'; // Default to True
    });

    const setApiBaseUrl = (url: string) => {
        setApiBaseUrlState(url);
        localStorage.setItem('stockmanager_api_url', url);
    };

    const setDemoMode = (isDemo: boolean) => {
        setDemoModeState(isDemo);
        localStorage.setItem('stockmanager_demo_mode', String(isDemo));
    };

    return (
        <SettingsContext.Provider value={{ apiBaseUrl, setApiBaseUrl, isDemoMode, setDemoMode }}>
            {children}
        </SettingsContext.Provider>
    );
};

export const useSettings = () => {
    const context = useContext(SettingsContext);
    if (context === undefined) {
        throw new Error('useSettings must be used within a SettingsProvider');
    }
    return context;
};
