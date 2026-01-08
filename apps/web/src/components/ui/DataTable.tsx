import { cn } from "../../lib/utils";
import { Skeleton } from "./Skeleton";

export type Column<T> = {
  header: string;
  key: string;
  width?: string;
  align?: "left" | "center" | "right";
  render?: (row: T) => React.ReactNode;
};

type DataTableProps<T> = {
  columns: Column<T>[];
  rows: T[];
  loading?: boolean;
  emptyMessage?: string;
  onRowClick?: (row: T) => void;
};

export const DataTable = <T,>({
  columns,
  rows,
  loading,
  emptyMessage = "데이터가 없습니다.",
  onRowClick,
}: DataTableProps<T>) => {
  return (
    <div className="min-w-0 w-full overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
      <table className="w-full table-fixed text-left text-sm">
        <thead className="bg-[var(--surface-muted)] text-xs uppercase text-[var(--muted)]">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={cn(
                  "px-4 py-3 font-semibold",
                  column.align === "center" && "text-center",
                  column.align === "right" && "text-right"
                )}
                style={{ width: column.width }}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading &&
            Array.from({ length: 4 }).map((_, index) => (
              <tr key={`skeleton-${index}`} className="border-t border-[var(--border)]">
                <td colSpan={columns.length} className="px-4 py-4">
                  <Skeleton />
                </td>
              </tr>
            ))}
          {!loading && rows.length === 0 && (
            <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-8 text-center text-sm text-[var(--muted)]"
                >
                {emptyMessage}
              </td>
            </tr>
          )}
          {!loading &&
            rows.map((row, index) => (
              <tr
                key={`row-${index}`}
                className={cn(
                  "border-t border-[var(--border)] transition",
                  onRowClick && "cursor-pointer hover:bg-[var(--surface-muted)]"
                )}
                onClick={() => onRowClick?.(row)}
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={cn(
                      "px-4 py-3 text-sm text-[var(--text)] break-words",
                      column.align === "center" && "text-center",
                      column.align === "right" && "text-right"
                    )}
                  >
                    {column.render ? column.render(row) : (row as any)[column.key]}
                  </td>
                ))}
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
};
