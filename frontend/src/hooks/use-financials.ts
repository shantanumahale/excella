"use client";

import { useQuery } from "@tanstack/react-query";
import { getFinancials } from "@/lib/api";

interface UseFinancialsParams {
  ticker: string;
  statement_type?: string;
  period_type?: string;
  limit?: number;
}

export function useFinancials({
  ticker,
  statement_type,
  period_type,
  limit,
}: UseFinancialsParams) {
  const query = useQuery({
    queryKey: ["financials", ticker, statement_type, period_type, limit],
    queryFn: () => getFinancials(ticker, { statement_type, period_type, limit }),
    enabled: !!ticker,
    staleTime: 5 * 60 * 1000,
  });

  return {
    data: query.data,
    isLoading: query.isLoading,
  };
}
