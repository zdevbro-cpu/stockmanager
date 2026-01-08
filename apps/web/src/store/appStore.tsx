import { createContext, useContext, useMemo, useState } from "react";
import { loadJson, saveJson } from "../lib/storage";
import { todayLocal } from "../lib/utils";

type AppSettings = {
  asOfDate: string;
  setAsOfDate: (value: string) => void;
  apiBaseUrl: string;
  setApiBaseUrl: (value: string) => void;
  demoMode: boolean;
  setDemoMode: (value: boolean) => void;
  searchQuery: string;
  setSearchQuery: (value: string) => void;
};

const AppSettingsContext = createContext<AppSettings | null>(null);

const STORAGE_KEY = "stockmanager.settings";

type StoredSettings = {
  apiBaseUrl: string;
  demoMode: boolean;
};

const defaultSettings: StoredSettings = {
  apiBaseUrl: "http://localhost:8000",
  demoMode: true,
};

export const AppProvider = ({ children }: { children: React.ReactNode }) => {
  const stored = loadJson<StoredSettings>(STORAGE_KEY, defaultSettings);
  const [asOfDate, setAsOfDate] = useState(todayLocal());
  const [apiBaseUrl, setApiBaseUrlState] = useState(stored.apiBaseUrl);
  const [demoMode, setDemoModeState] = useState(stored.demoMode);
  const [searchQuery, setSearchQuery] = useState("");

  const setApiBaseUrl = (value: string) => {
    setApiBaseUrlState(value);
    saveJson(STORAGE_KEY, { apiBaseUrl: value, demoMode });
  };

  const setDemoMode = (value: boolean) => {
    setDemoModeState(value);
    saveJson(STORAGE_KEY, { apiBaseUrl, demoMode: value });
  };

  const value = useMemo(
    () => ({
      asOfDate,
      setAsOfDate,
      apiBaseUrl,
      setApiBaseUrl,
      demoMode,
      setDemoMode,
      searchQuery,
      setSearchQuery,
    }),
    [asOfDate, apiBaseUrl, demoMode, searchQuery]
  );

  return (
    <AppSettingsContext.Provider value={value}>
      {children}
    </AppSettingsContext.Provider>
  );
};

export const useAppSettings = () => {
  const context = useContext(AppSettingsContext);
  if (!context) {
    throw new Error("AppSettingsProvider가 필요합니다.");
  }
  return context;
};
