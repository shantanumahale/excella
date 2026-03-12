"use client";

import { useMemo } from "react";
import Link from "next/link";
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  type ColumnDef,
} from "@tanstack/react-table";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { TableSkeleton } from "@/components/shared/loading-skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { METRIC_MAP } from "@/lib/metric-metadata";
import { formatMetricValue } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { ArrowUp, ArrowDown, ArrowUpDown, Search } from "lucide-react";
import type { ScreenerResult } from "@/lib/types";

interface ScreenerTableProps {
  data: ScreenerResult[];
  isLoading: boolean;
  selectedColumns: string[];
  sortBy: string;
  sortOrder: "asc" | "desc";
  onSort: (column: string) => void;
}

export function ScreenerTable({
  data,
  isLoading,
  selectedColumns,
  sortBy,
  sortOrder,
  onSort,
}: ScreenerTableProps) {
  // Build columns from selection, filtering out the fixed ones
  const metricColumns = useMemo(() => {
    const fixed = new Set(["ticker", "name", "sector", "industry"]);
    return selectedColumns.filter((col) => !fixed.has(col));
  }, [selectedColumns]);

  const columns = useMemo<ColumnDef<ScreenerResult, unknown>[]>(() => {
    const cols: ColumnDef<ScreenerResult, unknown>[] = [
      // Ticker — always first, frozen-style
      {
        id: "ticker",
        accessorKey: "ticker",
        header: () => (
          <SortableHeader
            label="Ticker"
            column="ticker"
            sortBy={sortBy}
            sortOrder={sortOrder}
            onSort={onSort}
          />
        ),
        cell: ({ row }) => (
          <Link
            href={`/company/${row.original.ticker}`}
            className="font-semibold text-primary hover:underline"
          >
            {row.original.ticker}
          </Link>
        ),
        size: 90,
      },
      // Name
      {
        id: "name",
        accessorKey: "name",
        header: () => (
          <SortableHeader
            label="Name"
            column="name"
            sortBy={sortBy}
            sortOrder={sortOrder}
            onSort={onSort}
          />
        ),
        cell: ({ row }) => (
          <span className="text-foreground max-w-[200px] truncate block">
            {row.original.name}
          </span>
        ),
        size: 200,
      },
      // Sector
      {
        id: "sector",
        accessorKey: "sector",
        header: () => (
          <SortableHeader
            label="Sector"
            column="sector"
            sortBy={sortBy}
            sortOrder={sortOrder}
            onSort={onSort}
          />
        ),
        cell: ({ row }) =>
          row.original.sector ? (
            <Badge variant="outline" className="text-xs font-normal whitespace-nowrap">
              {row.original.sector}
            </Badge>
          ) : (
            <span className="text-muted-foreground">--</span>
          ),
        size: 150,
      },
    ];

    // Dynamic metric columns
    for (const metricKey of metricColumns) {
      const meta = METRIC_MAP[metricKey];
      const label = meta?.label ?? metricKey;
      const format = meta?.format ?? "number";

      cols.push({
        id: metricKey,
        header: () => (
          <SortableHeader
            label={label}
            column={metricKey}
            sortBy={sortBy}
            sortOrder={sortOrder}
            onSort={onSort}
          />
        ),
        cell: ({ row }) => {
          const val = row.original.metrics?.[metricKey] ?? null;
          return (
            <span className="text-sm tabular-nums text-right block">
              {formatMetricValue(val, format)}
            </span>
          );
        },
        size: 120,
      });
    }

    return cols;
  }, [metricColumns, sortBy, sortOrder, onSort]);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (isLoading && data.length === 0) {
    return <TableSkeleton rows={12} columns={Math.min(metricColumns.length + 3, 8)} />;
  }

  if (!isLoading && data.length === 0) {
    return (
      <EmptyState
        icon={Search}
        title="No companies found"
        description="Try adjusting your filters or removing some criteria to see more results."
      />
    );
  }

  return (
    <div className="relative rounded-lg border border-border overflow-hidden">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id} className="bg-muted/30 hover:bg-muted/30">
                {headerGroup.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    className="whitespace-nowrap"
                    style={{ width: header.getSize() }}
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id} className="whitespace-nowrap">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sortable header helper
// ---------------------------------------------------------------------------

function SortableHeader({
  label,
  column,
  sortBy,
  sortOrder,
  onSort,
}: {
  label: string;
  column: string;
  sortBy: string;
  sortOrder: "asc" | "desc";
  onSort: (column: string) => void;
}) {
  const isActive = sortBy === column;

  return (
    <button
      className={cn(
        "flex items-center gap-1 text-xs font-medium transition-colors hover:text-foreground",
        isActive ? "text-foreground" : "text-muted-foreground",
      )}
      onClick={() => onSort(column)}
    >
      {label}
      {isActive ? (
        sortOrder === "asc" ? (
          <ArrowUp className="h-3 w-3" />
        ) : (
          <ArrowDown className="h-3 w-3" />
        )
      ) : (
        <ArrowUpDown className="h-3 w-3 opacity-40" />
      )}
    </button>
  );
}
