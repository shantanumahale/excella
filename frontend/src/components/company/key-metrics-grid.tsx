"use client";

import { Card, CardContent } from "@/components/ui/card";
import { getMetricMeta } from "@/lib/metric-metadata";
import { formatMetricValue } from "@/lib/formatters";
import type { DerivedMetrics } from "@/lib/types";
import { cn } from "@/lib/utils";

interface KeyMetricsGridProps {
  metrics: DerivedMetrics | null;
}

interface MetricDisplayConfig {
  key: string;
  category: keyof DerivedMetrics;
}

const KEY_METRICS: { group: string; items: MetricDisplayConfig[] }[] = [
  {
    group: "Profitability",
    items: [
      { key: "return_on_equity", category: "profitability" },
      { key: "return_on_assets", category: "profitability" },
      { key: "net_margin", category: "profitability" },
      { key: "operating_margin", category: "profitability" },
      { key: "gross_margin", category: "profitability" },
      { key: "return_on_invested_capital", category: "profitability" },
    ],
  },
  {
    group: "Valuation",
    items: [
      { key: "pe_ratio", category: "valuation" },
      { key: "price_to_book", category: "valuation" },
      { key: "ev_to_ebitda", category: "valuation" },
      { key: "price_to_sales", category: "valuation" },
      { key: "earnings_yield", category: "valuation" },
      { key: "fcf_yield", category: "valuation" },
    ],
  },
  {
    group: "Leverage",
    items: [
      { key: "debt_to_equity", category: "leverage" },
      { key: "interest_coverage", category: "leverage" },
      { key: "debt_to_ebitda", category: "leverage" },
      { key: "current_ratio", category: "liquidity" },
      { key: "quick_ratio", category: "liquidity" },
      { key: "debt_to_assets", category: "leverage" },
    ],
  },
  {
    group: "Growth",
    items: [
      { key: "revenue_growth", category: "growth" },
      { key: "net_income_growth", category: "growth" },
      { key: "eps_growth", category: "growth" },
      { key: "operating_income_growth", category: "growth" },
      { key: "free_cash_flow_growth", category: "growth" },
      { key: "ebitda_growth", category: "growth" },
    ],
  },
];

export function KeyMetricsGrid({ metrics }: KeyMetricsGridProps) {
  if (!metrics) {
    return (
      <p className="text-sm text-muted-foreground">No metrics available.</p>
    );
  }

  return (
    <div className="space-y-6">
      {KEY_METRICS.map((group) => (
        <div key={group.group}>
          <h3 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            {group.group}
          </h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {group.items.map((item) => {
              const meta = getMetricMeta(item.key);
              const categoryData = metrics[item.category];
              const value = categoryData?.[item.key] ?? null;

              return (
                <Card key={item.key} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <p className="text-xs text-muted-foreground truncate">
                      {meta?.label ?? item.key}
                    </p>
                    <p
                      className={cn(
                        "mt-1 text-lg font-semibold tabular-nums",
                        meta?.format === "percent" && value !== null
                          ? value > 0
                            ? "text-gain"
                            : value < 0
                              ? "text-loss"
                              : "text-foreground"
                          : "text-foreground"
                      )}
                    >
                      {meta
                        ? formatMetricValue(value, meta.format)
                        : value !== null
                          ? String(value)
                          : "--"}
                    </p>
                    {meta && (
                      <p className="mt-1 text-[10px] text-muted-foreground leading-tight line-clamp-2">
                        {meta.description}
                      </p>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
