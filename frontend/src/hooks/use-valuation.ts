"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import {
  getValuation,
  getValuationComps,
  getValuationHistory,
  getValuationSensitivity,
  runCustomDCF,
} from "@/lib/api";
import type { DCFParams } from "@/lib/types";

export function useValuation(ticker: string) {
  const query = useQuery({
    queryKey: ["valuation", ticker],
    queryFn: () => getValuation(ticker),
    enabled: !!ticker,
    staleTime: 5 * 60 * 1000,
  });

  return {
    data: query.data?.valuation_models ?? null,
    isLoading: query.isLoading,
    error: query.error,
  };
}

export function useCustomDCF(ticker: string) {
  return useMutation({
    mutationFn: (params: DCFParams) => runCustomDCF(ticker, params),
  });
}

export function useValuationSensitivity(ticker: string) {
  const query = useQuery({
    queryKey: ["valuation-sensitivity", ticker],
    queryFn: () => getValuationSensitivity(ticker),
    enabled: !!ticker,
    staleTime: 5 * 60 * 1000,
  });

  return {
    data: query.data ?? null,
    isLoading: query.isLoading,
  };
}

export function useValuationComps(ticker: string) {
  const query = useQuery({
    queryKey: ["valuation-comps", ticker],
    queryFn: () => getValuationComps(ticker),
    enabled: !!ticker,
    staleTime: 5 * 60 * 1000,
  });

  return {
    data: query.data ?? null,
    isLoading: query.isLoading,
  };
}

export function useValuationHistory(ticker: string) {
  const query = useQuery({
    queryKey: ["valuation-history", ticker],
    queryFn: () => getValuationHistory(ticker),
    enabled: !!ticker,
    staleTime: 5 * 60 * 1000,
  });

  return {
    data: query.data?.history ?? null,
    isLoading: query.isLoading,
  };
}
