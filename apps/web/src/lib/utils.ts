import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));

export const formatNumber = (value: number | null | undefined) => {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat("ko-KR").format(value);
};

export const formatPercent = (value: number | null | undefined) => {
  if (value === null || value === undefined) return "-";
  return `${(value * 100).toFixed(1)}%`;
};

export const formatDateLabel = (iso: string) => {
  if (!iso) return "-";
  return iso.replaceAll("-", ".");
};

export const todayLocal = () => {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  const local = new Date(now.getTime() - offset);
  return local.toISOString().slice(0, 10);
};
