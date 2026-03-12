"use client";

import Link from "next/link";
import type { FredSeries } from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import { formatNumber, formatDate } from "@/lib/formatters";
import { TrendingUp } from "lucide-react";

interface MacroSeriesCardProps {
  series: FredSeries;
  latestValue?: number | null;
  href: string;
}

function MacroSeriesCard({
  series,
  latestValue,
  href,
}: MacroSeriesCardProps) {
  return (
    <Link href={href}>
      <Card className="cursor-pointer transition-all hover:shadow-md hover:border-primary/30">
        <CardContent className="p-5">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-primary tracking-wider uppercase">
                {series.series_id}
              </p>
              <p className="mt-1 text-sm font-medium text-foreground leading-snug line-clamp-2">
                {series.title}
              </p>
            </div>
            <div className="shrink-0 rounded-lg bg-primary/10 p-2">
              <TrendingUp className="h-4 w-4 text-primary" />
            </div>
          </div>

          <div className="mt-4">
            {latestValue !== undefined && latestValue !== null ? (
              <p className="text-2xl font-bold tabular-nums text-foreground">
                {formatNumber(latestValue, 2)}
              </p>
            ) : (
              <p className="text-2xl font-bold text-muted-foreground">--</p>
            )}
            <p className="mt-1 text-xs text-muted-foreground">
              {series.units}
            </p>
          </div>

          <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
            <span>{series.frequency}</span>
            <span>{formatDate(series.last_updated)}</span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

export { MacroSeriesCard };
