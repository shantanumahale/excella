"use client";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ReturnBadge } from "@/components/shared/return-badge";
import { formatCurrency, formatLargeNumber } from "@/lib/formatters";
import type { Company, PriceBar, PriceReturns } from "@/lib/types";
import { TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface CompanyHeaderProps {
  company?: Company;
  latestPrice?: PriceBar;
  returns?: PriceReturns;
  isLoading: boolean;
}

function CompanyHeaderSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex items-start gap-4">
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-8 w-64" />
      </div>
      <div className="flex items-center gap-4">
        <Skeleton className="h-10 w-32" />
        <Skeleton className="h-6 w-24" />
      </div>
      <div className="flex flex-wrap gap-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-7 w-24" />
        ))}
      </div>
      <div className="flex gap-2">
        <Skeleton className="h-6 w-28" />
        <Skeleton className="h-6 w-28" />
      </div>
    </div>
  );
}

export function CompanyHeader({
  company,
  latestPrice,
  returns,
  isLoading,
}: CompanyHeaderProps) {
  if (isLoading || !company) {
    return <CompanyHeaderSkeleton />;
  }

  const dailyChange = returns?.returns["1d"] ?? null;
  const priceChangeAmount =
    latestPrice && dailyChange !== null
      ? latestPrice.close - latestPrice.close / (1 + dailyChange)
      : null;

  const isPositive = dailyChange !== null && dailyChange > 0;
  const isNegative = dailyChange !== null && dailyChange < 0;

  return (
    <div className="space-y-3">
      {/* Row 1: Ticker + Name */}
      <div className="flex items-center gap-3">
        <Badge variant="default" className="text-sm px-2.5 py-1">
          {company.ticker}
        </Badge>
        <h1 className="text-2xl font-bold text-foreground">{company.name}</h1>
      </div>

      {/* Row 2: Price + daily change */}
      <div className="flex items-baseline gap-3">
        {latestPrice ? (
          <>
            <span className="text-3xl font-bold tabular-nums text-foreground">
              {formatCurrency(latestPrice.close, 2)}
            </span>
            {priceChangeAmount !== null && dailyChange !== null && (
              <span
                className={cn(
                  "flex items-center gap-1 text-sm font-medium",
                  isPositive && "text-gain",
                  isNegative && "text-loss",
                  !isPositive && !isNegative && "text-muted-foreground"
                )}
              >
                {isPositive ? (
                  <TrendingUp className="h-4 w-4" />
                ) : isNegative ? (
                  <TrendingDown className="h-4 w-4" />
                ) : null}
                <span className="tabular-nums">
                  {priceChangeAmount >= 0 ? "+" : ""}
                  {formatCurrency(priceChangeAmount, 2)}
                </span>
                <span className="tabular-nums">
                  ({(dailyChange * 100).toFixed(2)}%)
                </span>
              </span>
            )}
          </>
        ) : (
          <span className="text-xl text-muted-foreground">Price unavailable</span>
        )}
      </div>

      {/* Row 3: Return badges */}
      {returns && (
        <div className="flex flex-wrap gap-2">
          <ReturnBadge label="1D" value={returns.returns["1d"]} />
          <ReturnBadge label="5D" value={returns.returns["5d"]} />
          <ReturnBadge label="1M" value={returns.returns["21d"]} />
          <ReturnBadge label="3M" value={returns.returns["63d"]} />
          <ReturnBadge label="6M" value={returns.returns["126d"]} />
          <ReturnBadge label="1Y" value={returns.returns["252d"]} />
        </div>
      )}

      {/* Row 4: Sector / Industry badges */}
      <div className="flex flex-wrap gap-2">
        {company.sector && (
          <Badge variant="secondary">{company.sector}</Badge>
        )}
        {company.industry && (
          <Badge variant="outline">{company.industry}</Badge>
        )}
        {company.exchange && (
          <Badge variant="outline">{company.exchange}</Badge>
        )}
        {company.market_cap && (
          <Badge variant="outline">
            MCap: {formatLargeNumber(company.market_cap)}
          </Badge>
        )}
      </div>
    </div>
  );
}
