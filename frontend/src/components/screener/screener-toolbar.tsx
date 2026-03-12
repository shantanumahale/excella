"use client";

import { Badge } from "@/components/ui/badge";
import { Pagination } from "@/components/shared/pagination";
import { ColumnEditor } from "./column-editor";
import { Loader2 } from "lucide-react";

interface ScreenerToolbarProps {
  total: number;
  offset: number;
  limit: number;
  onOffsetChange: (offset: number) => void;
  selectedColumns: string[];
  onColumnsChange: (columns: string[]) => void;
  isFetching: boolean;
}

export function ScreenerToolbar({
  total,
  offset,
  limit,
  onOffsetChange,
  selectedColumns,
  onColumnsChange,
  isFetching,
}: ScreenerToolbarProps) {
  return (
    <div className="space-y-3">
      {/* Top row: result count + column editor */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-foreground">Screener</h1>
          <Badge variant="secondary" className="text-xs">
            {total.toLocaleString()} {total === 1 ? "company" : "companies"}
          </Badge>
          {isFetching && (
            <Loader2 className="h-4 w-4 text-muted-foreground animate-spin" />
          )}
        </div>
        <ColumnEditor
          selectedColumns={selectedColumns}
          onColumnsChange={onColumnsChange}
        />
      </div>

      {/* Pagination (only when there are results) */}
      {total > 0 && (
        <Pagination
          total={total}
          offset={offset}
          limit={limit}
          onChange={onOffsetChange}
        />
      )}
    </div>
  );
}
