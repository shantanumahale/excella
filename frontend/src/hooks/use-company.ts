"use client";

import { useQuery } from "@tanstack/react-query";
import { getCompany } from "@/lib/api";

export function useCompany(ticker: string) {
  const query = useQuery({
    queryKey: ["company", ticker],
    queryFn: () => getCompany(ticker),
    enabled: !!ticker,
    staleTime: 5 * 60 * 1000,
  });

  return {
    company: query.data,
    isLoading: query.isLoading,
    error: query.error,
  };
}
