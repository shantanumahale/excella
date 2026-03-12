"use client";

import { useState, useMemo, useCallback } from "react";
import { useParams } from "next/navigation";
import { useMetrics } from "@/hooks/use-metrics";
import { LineChart, type LineConfig } from "@/components/charts/line-chart";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { METRIC_CATEGORIES } from "@/lib/constants";
import { getMetricsByCategory } from "@/lib/metric-metadata";
import { formatMetricValue, formatDate, formatChartTick, formatChartTooltipDate, computeDateSpanYears } from "@/lib/formatters";
import { ChartSkeleton, TableSkeleton } from "@/components/shared/loading-skeleton";
import { cn } from "@/lib/utils";

const CHART_COLORS = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
  "#06b6d4",
  "#f97316",
];

export default function MetricsPage() {
  const params = useParams<{ ticker: string }>();
  const ticker = params.ticker.toUpperCase();

  const [selectedCategory, setSelectedCategory] = useState("profitability");
  const [periodType, setPeriodType] = useState("annual");
  const [selectedMetricKeys, setSelectedMetricKeys] = useState<string[]>([]);

  const { data: metricsHistory, isLoading } = useMetrics({
    ticker,
    period_type: periodType,
    limit: 20,
  });

  const categoryMetrics = useMemo(
    () => getMetricsByCategory(selectedCategory),
    [selectedCategory]
  );

  // Filter to numeric-only metrics (skip objects like components/signals)
  const numericMetrics = useMemo(
    () =>
      categoryMetrics.filter(
        (m) =>
          m.format !== "boolean" &&
          !m.key.includes("components") &&
          !m.key.includes("signals") &&
          !m.key.includes("flags") &&
          !m.key.includes("zone") &&
          !m.key.includes("strength") &&
          !m.key.includes("risk") &&
          !m.key.includes("flag")
      ),
    [categoryMetrics]
  );

  // When category changes, auto-select first 3 metrics
  const activeKeys = useMemo(() => {
    if (selectedMetricKeys.length > 0) return selectedMetricKeys;
    return numericMetrics.slice(0, 3).map((m) => m.key);
  }, [selectedMetricKeys, numericMetrics]);

  // Build chart data: each row is a period, columns are metric values
  const chartData = useMemo(() => {
    if (!metricsHistory || metricsHistory.length === 0) return [];

    // Reverse to chronological order
    const sorted = [...metricsHistory].reverse();

    return sorted.map((entry) => {
      const categoryData = entry[selectedCategory as keyof typeof entry] as
        | Record<string, number | null>
        | undefined;
      const row: Record<string, unknown> = {
        date: entry.period_end,
      };
      if (categoryData) {
        for (const key of activeKeys) {
          row[key] = categoryData[key] ?? null;
        }
      }
      return row;
    });
  }, [metricsHistory, selectedCategory, activeKeys]);

  const spanYears = useMemo(
    () => computeDateSpanYears(chartData.map((d) => d.date as string)),
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

  const chartLines: LineConfig[] = activeKeys.map((key, idx) => {
    const meta = numericMetrics.find((m) => m.key === key);
    return {
      key,
      label: meta?.label ?? key,
      color: CHART_COLORS[idx % CHART_COLORS.length],
    };
  });

  function toggleMetric(key: string) {
    setSelectedMetricKeys((prev) => {
      const isDefault = prev.length === 0;
      const current = isDefault
        ? numericMetrics.slice(0, 3).map((m) => m.key)
        : prev;

      if (current.includes(key)) {
        const next = current.filter((k) => k !== key);
        return next.length === 0 ? [] : next;
      }
      if (current.length >= 6) return current;
      return [...current, key];
    });
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-lg font-semibold">Metrics History</h2>
        <div className="flex items-center gap-2">
          <Button
            variant={periodType === "annual" ? "default" : "outline"}
            size="sm"
            onClick={() => setPeriodType("annual")}
          >
            Annual
          </Button>
          <Button
            variant={periodType === "quarterly" ? "default" : "outline"}
            size="sm"
            onClick={() => setPeriodType("quarterly")}
          >
            Quarterly
          </Button>
        </div>
      </div>

      {/* Category selector */}
      <div className="flex flex-wrap gap-2">
        {METRIC_CATEGORIES.map((cat) => (
          <Button
            key={cat.id}
            variant={selectedCategory === cat.id ? "default" : "outline"}
            size="sm"
            onClick={() => {
              setSelectedCategory(cat.id);
              setSelectedMetricKeys([]);
            }}
          >
            {cat.label}
          </Button>
        ))}
      </div>

      {/* Metric toggles */}
      <div className="flex flex-wrap gap-1.5">
        {numericMetrics.map((meta, idx) => {
          const isActive = activeKeys.includes(meta.key);
          return (
            <button
              key={meta.key}
              onClick={() => toggleMetric(meta.key)}
              className={cn(
                "rounded-md px-2.5 py-1 text-xs font-medium transition-colors border",
                isActive
                  ? "bg-primary text-primary-foreground border-primary"
                  : "bg-transparent text-muted-foreground border-border hover:bg-muted"
              )}
            >
              {meta.label}
            </button>
          );
        })}
      </div>

      {/* Chart */}
      {isLoading ? (
        <ChartSkeleton />
      ) : (
        <Card>
          <CardContent className="p-4">
            <LineChart
              data={chartData}
              xKey="date"
              lines={chartLines}
              height={400}
              tickFormatter={tickFmt}
              tooltipLabelFormatter={tooltipFmt}
            />
          </CardContent>
        </Card>
      )}

      {/* Historical table */}
      {isLoading ? (
        <TableSkeleton rows={10} columns={6} />
      ) : metricsHistory && metricsHistory.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Historical Values</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="sticky left-0 z-10 bg-card">
                      Metric
                    </TableHead>
                    {[...metricsHistory].map((entry, idx) => (
                        <TableHead
                          key={idx}
                          className="text-right min-w-[100px]"
                        >
                          {formatDate(entry.period_end)}
                        </TableHead>
                      ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {numericMetrics.map((meta) => (
                    <TableRow key={meta.key}>
                      <TableCell className="sticky left-0 z-10 bg-card font-medium text-sm whitespace-nowrap">
                        {meta.label}
                      </TableCell>
                      {[...metricsHistory].map((entry, idx) => {
                        const catData = entry[
                          selectedCategory as keyof typeof entry
                        ] as Record<string, number | null> | undefined;
                        const val = catData?.[meta.key] ?? null;
                        return (
                          <TableCell
                            key={idx}
                            className="text-right tabular-nums text-sm"
                          >
                            {typeof val === "number"
                              ? formatMetricValue(val, meta.format)
                              : "--"}
                          </TableCell>
                        );
                      })}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      ) : (
        <p className="text-sm text-muted-foreground text-center py-8">
          No metrics history available.
        </p>
      )}
    </div>
  );
}
