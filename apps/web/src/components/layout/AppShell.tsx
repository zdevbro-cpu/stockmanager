import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { BottomTabs } from "./BottomTabs";

export const AppShell = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="flex min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col overflow-x-hidden">
        <TopBar />
        <main className="min-w-0 flex-1 overflow-x-hidden px-4 pb-20 pt-6 lg:px-8">
          <div className="mx-auto w-full max-w-[1200px] animate-rise">
            {children}
          </div>
        </main>
      </div>
      <BottomTabs />
    </div>
  );
};
