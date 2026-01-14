import { Outlet, Link, useLocation } from 'react-router-dom';
import clsx from 'clsx';

const NAV_ITEMS = [
    { path: '/', label: 'Market Information', icon: 'home' },
    { path: '/screener', label: 'Screener', icon: 'filter_alt' },
    { path: '/recommendations', label: 'Recommendation', icon: 'recommend' },
    { path: '/watchlist', label: 'Watchlist', icon: 'visibility' },
    { path: '/signals', label: 'Signals', icon: 'sensors' },
    { path: '/reports', label: 'Reports', icon: 'description' },
    { path: '/settings', label: 'Settings', icon: 'settings' },
];

export default function Layout() {
    const location = useLocation();

    return (
        <div className="flex min-h-screen bg-background-light dark:bg-background-dark text-slate-900 dark:text-white font-display">
            {/* Desktop Sidebar */}
            <aside className="hidden lg:flex flex-col w-64 border-r border-border-dark bg-background-dark fixed inset-y-0 z-50">
                <div className="flex items-center gap-2 h-16 px-6 border-b border-border-dark">
                    <span className="material-symbols-outlined text-primary text-3xl">finance_chip</span>
                    <span className="text-xl font-bold text-white tracking-tight">StockManager</span>
                </div>

                <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
                    {NAV_ITEMS.map((item) => (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={clsx(
                                "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors",
                                location.pathname === item.path
                                    ? "bg-primary text-white shadow-lg shadow-primary/20"
                                    : "text-text-subtle hover:bg-white/5 hover:text-white"
                            )}
                        >
                            <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                            {item.label}
                        </Link>
                    ))}
                </nav>

                <div className="p-4 border-t border-border-dark">
                    <div className="flex items-center gap-3 px-2">
                        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
                            U
                        </div>
                        <div className="flex flex-col">
                            <span className="text-sm font-bold text-white">User</span>
                            <span className="text-xs text-text-subtle">Free Plan</span>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col lg:ml-64 min-w-0">
                {/* Top Header */}
                <header className="sticky top-0 z-40 bg-background-light/95 dark:bg-background-dark/95 backdrop-blur-md border-b border-border-dark px-4 lg:px-6 h-16 flex items-center justify-between">
                    <div className="lg:hidden flex items-center gap-2">
                        <span className="material-symbols-outlined text-primary text-2xl">finance_chip</span>
                        <span className="font-bold text-lg dark:text-white">StockManager</span>
                    </div>

                    {/* Desktop: Breadcrumbs or Title (Hidden on mobile if needed, or simple) */}
                    <div className="hidden lg:block text-sm font-medium text-text-subtle">
                        {NAV_ITEMS.find(n => n.path === location.pathname)?.label}
                    </div>

                    {/* Right Actions */}
                    <div className="flex items-center gap-3">
                        <div className="hidden md:flex relative">
                            <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-text-subtle text-[18px]">search</span>
                            <input
                                type="text"
                                placeholder="Search ticker..."
                                className="h-9 w-64 bg-card-dark border border-border-dark rounded-lg pl-9 pr-4 text-sm text-white focus:outline-none focus:border-primary placeholder:text-text-subtle/50"
                            />
                        </div>
                        <button className="relative p-2 rounded-lg hover:bg-white/5 transition-colors">
                            <span className="material-symbols-outlined text-text-subtle text-[22px]">notifications</span>
                            <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-red-500 ring-2 ring-background-dark"></span>
                        </button>
                    </div>
                </header>

                {/* Content */}
                <main className="flex-1 p-4 lg:p-6 pb-20 lg:pb-6 overflow-x-hidden">
                    <Outlet />
                </main>
            </div>

            {/* Mobile Bottom Nav */}
            <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#151e1d]/90 backdrop-blur-lg border-t border-white/5 pb-[env(safe-area-inset-bottom)]">
                <div className="flex items-center justify-around h-16 px-2">
                    {(
                        [NAV_ITEMS[0], NAV_ITEMS[1], { ...NAV_ITEMS[2], isFab: true }, NAV_ITEMS[3], NAV_ITEMS[4]] as Array<typeof NAV_ITEMS[0] & { isFab?: boolean }>
                    ).map((item) => {
                        if (item.isFab) {
                            return (
                                <Link key={item.path} to={item.path} className="flex items-center justify-center w-12 h-12 -mt-6 rounded-full bg-primary shadow-lg shadow-primary/30 text-white">
                                    <span className="material-symbols-outlined text-[28px]">{item.icon}</span>
                                </Link>
                            )
                        }
                        const isActive = location.pathname === item.path;
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={clsx(
                                    "flex flex-col items-center justify-center gap-1 w-16 h-full transition-colors",
                                    isActive ? "text-primary" : "text-gray-500 hover:text-gray-300"
                                )}
                            >
                                <span className={clsx("material-symbols-outlined", isActive && "filled")}>
                                    {item.icon}
                                </span>
                                <span className="text-[10px] font-medium truncate w-full text-center">{item.label.split('(')[0]}</span>
                            </Link>
                        )
                    })}
                </div>
            </nav>
        </div>
    );
}
