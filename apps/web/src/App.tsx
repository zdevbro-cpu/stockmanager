import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Screener from './pages/Screener'
import Recommendations from './pages/Recommendations'
import Signals from './pages/Signals'
import Watchlist from './pages/Watchlist'
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import Themes from './pages/Themes';
import Industries from './pages/Industries';
import Layout from './Layout'
import { SettingsProvider } from './contexts/SettingsContext'

const queryClient = new QueryClient()

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <SettingsProvider>
                <BrowserRouter>
                    <Routes>
                        <Route element={<Layout />}>
                            <Route path="/" element={<Dashboard />} />
                            <Route path="/screener" element={<Screener />} />
                            <Route path="/recommendations" element={<Recommendations />} />
                            <Route path="/signals" element={<Signals />} />
                            <Route path="/watchlist" element={<Watchlist />} />
                            <Route path="/reports" element={<Reports />} />
                            <Route path="/settings" element={<Settings />} />
                            <Route path="/themes" element={<Themes />} />
                            <Route path="/industries" element={<Industries />} />
                        </Route>
                    </Routes>
                </BrowserRouter>
            </SettingsProvider>
        </QueryClientProvider>
    )
}

export default App
