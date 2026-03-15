"use client";

import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { runScreener } from "@/lib/api";
import type { ScreenerFilter } from "@/lib/types";

export interface ScreenerFilterState {
  metric: string;
  category: string;
  operator: string;
  value: number | null;
  valueTo: number | null;
}

export function useScreener() {
  const [filters, setFilters] = useState<ScreenerFilterState[]>([]);
  const [sortBy, setSortBy] = useState<string>("market_cap");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [offset, setOffset] = useState(0);
  const [limit] = useState(50);

  // Build the API-ready filters (drop incomplete ones)
  const apiFilters: ScreenerFilter[] = filters
    .filter((f) => {
      if (f.operator === "not_null") return true;
      if (f.operator === "between") return f.value !== null && f.valueTo !== null;
      return f.value !== null;
    })
    .map((f) => {
      const metricPath = `${f.category}.${f.metric}`;
      if (f.operator === "between") {
        return { metric: metricPath, operator: f.operator, value: [f.value!, f.valueTo!] };
      }
      return {
        metric: metricPath,
        operator: f.operator,
        value: f.operator === "not_null" ? 0 : f.value!,
      };
    });

  const query = useQuery({
    queryKey: ["screener", apiFilters, sortBy, sortOrder, offset, limit],
    queryFn: () =>
      runScreener({
        filters: apiFilters,
        sort_by: sortBy,
        sort_order: sortOrder,
        offset,
        limit,
      }),
    placeholderData: (prev) => prev,
  });

  const addFilter = useCallback(
    (category: string, metric: string) => {
      setFilters((prev) => [
        ...prev,
        { metric, category, operator: "gt", value: null, valueTo: null },
      ]);
    },
    [],
  );

  const removeFilter = useCallback((index: number) => {
    setFilters((prev) => prev.filter((_, i) => i !== index));
    setOffset(0);
  }, []);

  const updateFilter = useCallback(
    (index: number, patch: Partial<ScreenerFilterState>) => {
      setFilters((prev) =>
        prev.map((f, i) => (i === index ? { ...f, ...patch } : f)),
      );
      setOffset(0);
    },
    [],
  );

  const clearFilters = useCallback(() => {
    setFilters([]);
    setOffset(0);
  }, []);

  return {
    data: query.data,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    error: query.error,
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
  };
}
