import { NavLink } from "react-router-dom";
import { navItems } from "./navigation";
import { cn } from "../../lib/utils";

export const Sidebar = () => {
  return (
    <aside className="hidden h-screen w-60 flex-col border-r border-[var(--border)] bg-[var(--surface)] px-4 py-6 lg:flex">
      <div className="mb-6 text-lg font-semibold text-[var(--text)]">
        StockManager
        <div className="mt-1 text-xs font-medium text-[var(--muted)]">
          인사이트 허브
        </div>
      </div>
      <nav className="flex flex-1 flex-col gap-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition",
                isActive
                  ? "bg-[var(--accent)] text-white shadow-soft"
                  : "text-[var(--muted)] hover:bg-[var(--surface-muted)] hover:text-[var(--text)]"
              )
            }
          >
            <item.icon size={16} />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-muted)] p-3 text-xs text-[var(--muted)]">
        데이터는 참고용입니다. 실제 매매 판단은 별도 검토가 필요합니다.
      </div>
    </aside>
  );
};
