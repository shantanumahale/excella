"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { LineChart } from "@/components/charts/line-chart";
import {
  formatChartTick,
  formatChartTooltipDate,
  formatCurrency,
  computeDateSpanYears,
} from "@/lib/formatters";
import { useValuationHistory } from "@/hooks/use-valuation";

interface ValuationHistoryChartProps {
  ticker: string;
}

export function ValuationHistoryChart({ ticker }: ValuationHistoryChartProps) {
  const { data, isLoading } = useValuationHistory(ticker);

  const chartData = useMemo(() => {
    if (!data) return [];
    return data
      .filter((p) => p.intrinsic_value !== null || p.price !== null)
      .map((p) => ({
        date: p.period_end,
        intrinsic_value: p.intrinsic_value,
        market_price: p.price,
      }));
  }, [data]);

  const spanYears = useMemo(
    () => computeDateSpanYears(chartData.map((d) => d.date)),
    [chartData],
  );

  if (isLoading) {
    return <Skeleton className="h-[400px] w-full" />;
  }

  if (chartData.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-muted-foreground">
            No historical valuation data available.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Intrinsic Value vs Market Price</CardTitle>
      </CardHeader>
      <CardContent>
        <LineChart
          data={chartData}
          xKey="date"
          lines={[
            { key: "intrinsic_value", label: "Intrinsic Value", color: "var(--color-gain, #22c55e)" },
            { key: "market_price", label: "Market Price", color: "var(--color-primary, #3b82f6)" },
          ]}
          height={350}
          tickFormatter={(v) => formatChartTick(v, spanYears)}
          tooltipLabelFormatter={(v) => formatChartTooltipDate(String(v))}
        />
      </CardContent>
    </Card>
  );
}
