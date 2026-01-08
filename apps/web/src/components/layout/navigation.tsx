import {
  LayoutDashboard,
  Filter,
  Sparkles,
  Radar,
  Star,
  FileText,
  Settings,
} from "lucide-react";

export const navItems = [
  { path: "/", label: "홈", icon: LayoutDashboard },
  { path: "/screener", label: "스크리너", icon: Filter },
  { path: "/recommendations", label: "추천", icon: Sparkles },
  { path: "/signals", label: "시그널", icon: Radar },
  { path: "/watchlist", label: "관심", icon: Star },
  { path: "/reports", label: "리포트", icon: FileText },
  { path: "/settings", label: "설정", icon: Settings },
];
