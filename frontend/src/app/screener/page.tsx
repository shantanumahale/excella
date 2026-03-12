"use client";

import { useState, useEffect, useCallback } from "react";
import { useScreener } from "@/hooks/use-screener";
import { FilterPanel } from "@/components/screener/filter-panel";
import { ScreenerToolbar } from "@/components/screener/screener-toolbar";
import { ScreenerTable } from "@/components/screener/screener-table";
import { loadSavedColumns } from "@/components/screener/column-editor";
import { DEFAULT_SCREENER_COLUMNS } from "@/lib/constants";
import { cn } from "@/lib/utils";

export default function ScreenerPage() {
  const {
    data,
    isLoading,
    isFetching,
    filters,
    addFilter,
    removeFilter,
    updateFilter,
    clearFilters,
    sortBy,
    setSortBy,
    sortOrder,
    setSortOrder,
    offset,
    setOffset,
    limit,
  } = useScreener();

  const [filterCollapsed, setFilterCollapsed] = useState(false);
  const [selectedColumns, setSelectedColumns] = useState<string[]>(DEFAULT_SCREENER_COLUMNS);

  // Load saved columns from localStorage on mount
  useEffect(() => {
    setSelectedColumns(loadSavedColumns(DEFAULT_SCREENER_COLUMNS));
  }, []);

  const handleSort = useCallback(
    (column: string) => {
      if (sortBy === column) {
        setSortOrder(sortOrder === "asc" ? "desc" : "asc");
      } else {
        setSortBy(column);
        setSortOrder("desc");
      }
      setOffset(0);
    },
    [sortBy, sortOrder, setSortBy, setSortOrder, setOffset],
  );

  const results = data?.data ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="flex gap-0 -mx-4 sm:-mx-6 lg:-mx-8 min-h-[calc(100vh-8rem)]">
      {/* Filter sidebar */}
      <aside
        className={cn(
          "shrink-0 border-r border-border bg-card/50 transition-all duration-200",
          filterCollapsed ? "w-12" : "w-80",
        )}
      >
        <div className="sticky top-0 h-[calc(100vh-8rem)] overflow-hidden">
          <FilterPanel
            filters={filters}
            onAdd={addFilter}
            onUpdate={updateFilter}
            onRemove={removeFilter}
            onClear={clearFilters}
            isCollapsed={filterCollapsed}
            onToggleCollapse={() => setFilterCollapsed(!filterCollapsed)}
          />
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 min-w-0 px-4 sm:px-6 lg:px-8 py-2 space-y-4">
        <ScreenerToolbar
          total={total}
          offset={offset}
          limit={limit}
          onOffsetChange={setOffset}
          selectedColumns={selectedColumns}
          onColumnsChange={setSelectedColumns}
          isFetching={isFetching}
        />

        <ScreenerTable
          data={results}
          isLoading={isLoading}
          selectedColumns={selectedColumns}
          sortBy={sortBy}
          sortOrder={sortOrder}
          onSort={handleSort}
        />

        {/* Bottom pagination for long tables */}
        {total > limit && (
          <div className="pt-2">
            <ScreenerToolbar
              total={total}
              offset={offset}
              limit={limit}
              onOffsetChange={setOffset}
              selectedColumns={selectedColumns}
              onColumnsChange={setSelectedColumns}
              isFetching={isFetching}
            />
          </div>
        )}
      </div>
    </div>
  );
}
