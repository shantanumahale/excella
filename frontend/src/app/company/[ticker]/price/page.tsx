"use client";

import { useState, useMemo } from "react";
import { useParams } from "next/navigation";
import { usePrices } from "@/hooks/use-prices";
import { PriceChart } from "@/components/charts/price-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChartSkeleton } from "@/components/shared/loading-skeleton";
import { formatCurrency, formatLargeNumber, formatDate } from "@/lib/formatters";

const RANGE_OPTIONS = [
  { label: "1M", days: 30 },
  { label: "3M", days: 90 },
  { label: "6M", days: 180 },
  { label: "1Y", days: 365 },
  { label: "5Y", days: 1825 },
  { label: "Max", days: 0 },
];

function getStartDate(days: number): string | undefined {
  if (days === 0) return undefined;
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().split("T")[0];
}

export default function PricePage() {
  const params = useParams<{ ticker: string }>();
  const ticker = params.ticker.toUpperCase();

  const [selectedRange, setSelectedRange] = useState(365);

  const startDate = getStartDate(selectedRange);

  const { data: priceData, isLoading, error } = usePrices({
    ticker,
    start: startDate,
    limit: 2000,
  });

  const bars = useMemo(() => {
    if (!priceData?.data) return [];
    return [...priceData.data].sort(
      (a, b) => new Date(a.time).getTime() - new Date(b.time).getTime()
    );
  }, [priceData]);

  const latestBar = bars.length > 0 ? bars[bars.length - 1] : null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-lg font-semibold">Price Chart</h2>
        <div className="flex items-center gap-1.5">
          {RANGE_OPTIONS.map((opt) => (
            <Button
              key={opt.label}
              variant={selectedRange === opt.days ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedRange(opt.days)}
            >
              {opt.label}
            </Button>
          ))}
        </div>
      </div>

      {error ? (
        <Card>
          <CardContent className="p-4 text-red-500 text-sm">
            Error loading prices: {error.message}
          </CardContent>
        </Card>
      ) : isLoading ? (
        <ChartSkeleton className="h-[500px]" />
      ) : (
        <Card>
          <CardContent className="p-2 sm:p-4">
            <PriceChart data={bars} />
          </CardContent>
        </Card>
      )}

      {/* Price stats */}
      {latestBar && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Date</p>
              <p className="text-sm font-medium">
                {formatDate(latestBar.time)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Open</p>
              <p className="text-sm font-medium tabular-nums">
                {formatCurrency(latestBar.open, 2)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">High</p>
              <p className="text-sm font-medium tabular-nums">
                {formatCurrency(latestBar.high, 2)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Low</p>
              <p className="text-sm font-medium tabular-nums">
                {formatCurrency(latestBar.low, 2)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Close</p>
              <p className="text-sm font-medium tabular-nums">
                {formatCurrency(latestBar.close, 2)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Volume</p>
              <p className="text-sm font-medium tabular-nums">
                {formatLargeNumber(latestBar.volume)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
