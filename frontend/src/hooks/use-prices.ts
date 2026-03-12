"use client";

import { useQuery } from "@tanstack/react-query";
import { getPrices } from "@/lib/api";

interface UsePricesParams {
  ticker: string;
  start?: string;
  end?: string;
  offset?: number;
  limit?: number;
}

export function usePrices({ ticker, start, end, offset, limit }: UsePricesParams) {
  const query = useQuery({
    queryKey: ["prices", ticker, start, end, offset, limit],
    queryFn: () => getPrices(ticker, { start, end, offset, limit }),
    enabled: !!ticker,
    staleTime: 5 * 60 * 1000,
  });

  return {
    data: query.data,
    isLoading: query.isLoading,
    error: query.error,
  };
}
