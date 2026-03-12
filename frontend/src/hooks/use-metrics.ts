"use client";

import { useQuery } from "@tanstack/react-query";
import { getMetrics } from "@/lib/api";

interface UseMetricsParams {
  ticker: string;
  period_type?: string;
  limit?: number;
}

export function useMetrics({ ticker, period_type, limit }: UseMetricsParams) {
  const query = useQuery({
    queryKey: ["metrics", ticker, period_type, limit],
    queryFn: () => getMetrics(ticker, { period_type, limit }),
    enabled: !!ticker,
    staleTime: 5 * 60 * 1000,
  });

  return {
    data: query.data,
    isLoading: query.isLoading,
  };
}
