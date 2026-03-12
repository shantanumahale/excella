"use client";

import { useState, useMemo, useCallback } from "react";
import { useMacroObservations } from "@/hooks/use-macro";
import type { FredSeries } from "@/lib/types";
import { LineChart } from "@/components/charts/line-chart";
import { formatChartTick, formatChartTooltipDate, computeDateSpanYears } from "@/lib/formatters";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ChartSkeleton } from "@/components/shared/loading-skeleton";
import { Badge } from "@/components/ui/badge";
import { X } from "lucide-react";

interface MacroDetailProps {
  seriesId: string;
  seriesMeta?: FredSeries;
  onClose?: () => void;
}

const DATE_RANGES = [
  { label: "1Y", years: 1 },
  { label: "2Y", years: 2 },
  { label: "5Y", years: 5 },
  { label: "10Y", years: 10 },
  { label: "Max", years: 0 },
] as const;

function getStartDate(years: number): string | undefined {
  if (years === 0) return undefined;
  const d = new Date();
  d.setFullYear(d.getFullYear() - years);
  return d.toISOString().split("T")[0];
}

function MacroDetail({ seriesId, seriesMeta, onClose }: MacroDetailProps) {
  const [rangeIdx, setRangeIdx] = useState(2); // default 5Y
  const selectedRange = DATE_RANGES[rangeIdx];

  const startDate = getStartDate(selectedRange.years);

  const { data: observations, isLoading } = useMacroObservations(seriesId, {
    start: startDate,
    limit: 5000,
  });

  const chartData = useMemo(() => {
    if (!observations?.data) return [];
    const sorted = [...observations.data]
      .filter((obs) => obs.value !== null)
      .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());

    // Downsample to ~500 points max for performance (Recharts is DOM-based)
    const MAX_POINTS = 500;
    if (sorted.length <= MAX_POINTS) {
      return sorted.map((obs) => ({ date: obs.time, value: obs.value }));
    }
    const step = sorted.length / MAX_POINTS;
    const sampled: { date: string; value: number | null }[] = [];
    for (let i = 0; i < MAX_POINTS; i++) {
      const obs = sorted[Math.round(i * step)];
      sampled.push({ date: obs.time, value: obs.value });
    }
    // Always include the last point
    const last = sorted[sorted.length - 1];
    if (sampled[sampled.length - 1].date !== last.time) {
      sampled.push({ date: last.time, value: last.value });
    }
    return sampled;
  }, [observations]);

  const spanYears = useMemo(
    () => computeDateSpanYears(chartData.map((d) => d.date)),
    [chartData],
  );

  const tickFmt = useCallback(
    (val: string) => formatChartTick(val, spanYears),
    [spanYears],
  );

  const tooltipFmt = useCallback(
    (label: unknown) => formatChartTooltipDate(String(label)),
    [],
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <CardTitle className="text-xl">
              {seriesMeta?.title ?? seriesId}
            </CardTitle>
            {seriesMeta && (
              <CardDescription className="mt-1">
                {seriesMeta.series_id}
              </CardDescription>
            )}
          </div>
          {onClose && (
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Metadata badges */}
        {seriesMeta && (
          <div className="flex flex-wrap gap-2 mt-3">
            <Badge variant="outline">{seriesMeta.frequency}</Badge>
            <Badge variant="outline">{seriesMeta.units}</Badge>
            <Badge variant="outline">{seriesMeta.seasonal_adjustment}</Badge>
          </div>
        )}

        {/* Date range selector */}
        <div className="flex gap-1 mt-4">
          {DATE_RANGES.map((range, idx) => (
            <Button
              key={range.label}
              variant={idx === rangeIdx ? "default" : "outline"}
              size="sm"
              onClick={() => setRangeIdx(idx)}
              className="min-w-[48px]"
            >
              {range.label}
            </Button>
          ))}
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-[350px] w-full rounded-lg" />
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex items-center justify-center h-[350px] text-muted-foreground">
            No observation data available for this period
          </div>
        ) : (
          <LineChart
            data={chartData}
            xKey="date"
            lines={[
              {
                key: "value",
                label: seriesMeta?.title ?? seriesId,
                color: "hsl(221, 83%, 53%)",
              },
            ]}
            height={350}
            tickFormatter={tickFmt}
            tooltipLabelFormatter={tooltipFmt}
          />
        )}

        {/* Notes */}
        {seriesMeta?.notes && (
          <div className="mt-6 rounded-lg bg-muted/50 p-4">
            <p className="text-xs font-medium text-muted-foreground mb-1">Notes</p>
            <p className="text-sm text-muted-foreground leading-relaxed line-clamp-4">
              {seriesMeta.notes}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export { MacroDetail };
