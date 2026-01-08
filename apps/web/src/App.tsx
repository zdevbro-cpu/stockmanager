import { Routes, Route, Navigate } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import HomePage from "./pages/Home";
import ScreenerPage from "./pages/Screener";
import RecommendationsPage from "./pages/Recommendations";
import SignalsPage from "./pages/Signals";
import WatchlistPage from "./pages/Watchlist";
import ReportsPage from "./pages/Reports";
import SettingsPage from "./pages/Settings";

const App = () => {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/screener" element={<ScreenerPage />} />
        <Route path="/recommendations" element={<RecommendationsPage />} />
        <Route path="/signals" element={<SignalsPage />} />
        <Route path="/watchlist" element={<WatchlistPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
};

export default App;
