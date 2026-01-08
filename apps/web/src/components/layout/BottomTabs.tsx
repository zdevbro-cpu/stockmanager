import { NavLink } from "react-router-dom";
import { navItems } from "./navigation";
import { cn } from "../../lib/utils";

export const BottomTabs = () => {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-30 flex items-center justify-around border-t border-[var(--border)] bg-[var(--surface)] px-2 py-2 backdrop-blur lg:hidden">
      {navItems.slice(0, 5).map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          className={({ isActive }) =>
            cn(
              "flex flex-col items-center gap-1 rounded-md px-3 py-2 text-[10px] font-semibold",
              isActive ? "text-[var(--accent)]" : "text-[var(--muted)]"
            )
          }
        >
          <item.icon size={16} />
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
};
