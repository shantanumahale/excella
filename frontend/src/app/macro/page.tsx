"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { getMacroSeries, getMacroAllLatest } from "@/lib/api";
import type { FredSeries, FredObservation } from "@/lib/types";
import { MacroSeriesCard } from "@/components/macro/macro-series-card";
import { CardSkeleton } from "@/components/shared/loading-skeleton";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { Activity } from "lucide-react";

// ---------------------------------------------------------------------------
// Theme groupings
// ---------------------------------------------------------------------------

interface ThemeGroup {
  id: string;
  label: string;
  description: string;
  seriesIds: string[];
}

const THEMES: ThemeGroup[] = [
  {
    id: "interest-rates",
    label: "Interest Rates",
    description: "Treasury yields, federal funds rate, and term spreads",
    seriesIds: [
      "DGS1", "DGS2", "DGS5", "DGS10", "DGS20", "DGS30",
      "T10Y2Y", "FEDFUNDS", "DFF", "T10YIE",
    ],
  },
  {
    id: "inflation",
    label: "Inflation",
    description: "Consumer price indices and personal consumption expenditures",
    seriesIds: ["CPIAUCSL", "CPILFESL", "PCEPI"],
  },
  {
    id: "economic-activity",
    label: "Economic Activity",
    description: "GDP, employment, industrial production, and consumer sentiment",
    seriesIds: ["GDP", "GDPC1", "UNRATE", "PAYEMS", "INDPRO", "UMCSENT"],
  },
  {
    id: "market",
    label: "Market",
    description: "Volatility, credit spreads, and broad market indices",
    seriesIds: ["VIXCLS", "BAMLH0A0HYM2", "SP500"],
  },
];

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function MacroPage() {
  // Fetch all available series metadata
  const {
    data: allSeries,
    isLoading: isLoadingSeries,
  } = useQuery({
    queryKey: ["macro-series"],
    queryFn: getMacroSeries,
    staleTime: 10 * 60 * 1000,
  });

  // Single batch call to get latest values for all series
  const {
    data: latestValues,
    isLoading: isLoadingLatest,
  } = useQuery({
    queryKey: ["macro-latest-all"],
    queryFn: getMacroAllLatest,
    staleTime: 5 * 60 * 1000,
  });

  // Build lookup for series metadata
  const seriesMap = useMemo(() => {
    const map: Record<string, FredSeries> = {};
    if (allSeries) {
      for (const s of allSeries) {
        map[s.series_id] = s;
      }
    }
    return map;
  }, [allSeries]);

  const isLoading = isLoadingSeries || isLoadingLatest;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Macro Dashboard
        </h1>
        <p className="mt-1 text-muted-foreground">
          Track key macroeconomic indicators from the Federal Reserve Economic Data (FRED).
        </p>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="space-y-10">
          {Array.from({ length: 4 }).map((_, gi) => (
            <div key={gi} className="space-y-4">
              <Skeleton className="h-7 w-48" />
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {Array.from({ length: 4 }).map((_, ci) => (
                  <CardSkeleton key={ci} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Theme sections */}
      {!isLoading &&
        THEMES.map((theme) => (
          <section key={theme.id} className="space-y-4">
            <div>
              <h2 className="text-xl font-semibold text-foreground">
                {theme.label}
              </h2>
              <p className="text-sm text-muted-foreground">
                {theme.description}
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {theme.seriesIds.map((seriesId) => {
                const meta = seriesMap[seriesId];
                const latest = latestValues?.[seriesId];

                const displaySeries: FredSeries = meta ?? {
                  id: 0,
                  series_id: seriesId,
                  title: seriesId,
                  frequency: "",
                  units: "",
                  seasonal_adjustment: "",
                  notes: null,
                  last_updated: "",
                };

                return (
                  <MacroSeriesCard
                    key={seriesId}
                    series={displaySeries}
                    latestValue={latest?.value}
                    href={`/macro/${seriesId}`}
                  />
                );
              })}
            </div>
          </section>
        ))}

      {/* Empty state if no series data at all */}
      {!isLoading && !allSeries?.length && (
        <EmptyState
          icon={Activity}
          title="No macro data available"
          description="Macro economic series data could not be loaded. Please check your connection and try again."
        />
      )}
    </div>
  );
}
