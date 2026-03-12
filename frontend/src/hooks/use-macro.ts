"use client";

import { useQuery } from "@tanstack/react-query";
import {
  getMacroSeries,
  getMacroObservations,
  type GetMacroObservationsParams,
} from "@/lib/api";

export function useMacroSeries() {
  return useQuery({
    queryKey: ["macro-series"],
    queryFn: getMacroSeries,
    staleTime: 10 * 60 * 1000,
  });
}

export function useMacroObservations(
  seriesId: string | null,
  params?: GetMacroObservationsParams,
) {
  return useQuery({
    queryKey: ["macro-observations", seriesId, params],
    queryFn: () => getMacroObservations(seriesId!, params),
    enabled: !!seriesId,
    staleTime: 5 * 60 * 1000,
  });
}
