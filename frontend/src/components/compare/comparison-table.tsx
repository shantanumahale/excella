"use client";

import type { Company } from "@/lib/types";
import type { MetricMeta } from "@/lib/metric-metadata";
import { getMetricsByCategory } from "@/lib/metric-metadata";
import { formatMetricValue } from "@/lib/formatters";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

interface ComparisonTableProps {
  companies: Company[];
  category: string;
}

// Metrics where lower is better
const LOWER_IS_BETTER = new Set([
  "effective_tax_rate",
  "sga_ratio",
  "sbc_pct_revenue",
  "rd_intensity",
  "days_inventory_outstanding",
  "days_sales_outstanding",
  "days_payable_outstanding",
  "cash_conversion_cycle",
  "total_debt",
  "net_debt",
  "debt_to_equity",
  "debt_to_assets",
  "debt_to_ebitda",
  "debt_to_capital",
  "long_term_debt_to_equity",
  "financial_leverage_ratio",
  "equity_multiplier",
  "operating_cycle",
  "cash_cycle",
  "capex_to_operating_cash_flow",
  "pe_ratio",
  "price_to_book",
  "price_to_sales",
  "price_to_cash_flow",
  "ev_to_ebitda",
  "ev_to_ebit",
  "ev_to_revenue",
  "ev_to_fcf",
  "peg_ratio",
  "accruals_ratio",
  "sloan_ratio",
  "beneish_m_score",
  "reinvestment_rate",
  "total_debt_per_share",
  "net_debt_per_share",
]);

function getMetricValue(
  company: Company,
  metric: MetricMeta,
): number | null {
  const metrics = company.latest_metrics;
  if (!metrics) return null;

  const categoryData = metrics[metric.category as keyof typeof metrics];
  if (!categoryData || typeof categoryData !== "object") return null;

  const val = (categoryData as Record<string, number | null>)[metric.key];
  return val ?? null;
}

function ComparisonTable({ companies, category }: ComparisonTableProps) {
  const metrics = getMetricsByCategory(category);

  if (companies.length === 0) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        Add companies above to start comparing
      </div>
    );
  }

  if (metrics.length === 0) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        No metrics available for this category
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="min-w-[200px] sticky left-0 bg-card z-10">
            Metric
          </TableHead>
          {companies.map((c) => (
            <TableHead key={c.ticker} className="text-center min-w-[130px]">
              <div className="font-semibold text-foreground">{c.ticker}</div>
              <div className="text-xs font-normal text-muted-foreground truncate max-w-[130px]">
                {c.name}
              </div>
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {metrics.map((metric) => {
          const values = companies.map((c) => getMetricValue(c, metric));
          const numericValues = values.filter(
            (v): v is number => v !== null && !Number.isNaN(v),
          );

          let bestIdx = -1;
          let worstIdx = -1;

          if (numericValues.length >= 2) {
            const lowerBetter = LOWER_IS_BETTER.has(metric.key);

            let bestVal = lowerBetter ? Infinity : -Infinity;
            let worstVal = lowerBetter ? -Infinity : Infinity;

            values.forEach((v, i) => {
              if (v === null || Number.isNaN(v)) return;
              if (lowerBetter) {
                if (v < bestVal) { bestVal = v; bestIdx = i; }
                if (v > worstVal) { worstVal = v; worstIdx = i; }
              } else {
                if (v > bestVal) { bestVal = v; bestIdx = i; }
                if (v < worstVal) { worstVal = v; worstIdx = i; }
              }
            });
          }

          return (
            <TableRow key={metric.key}>
              <TableCell className="sticky left-0 bg-card z-10">
                <div className="font-medium text-foreground text-sm">
                  {metric.label}
                </div>
                <div className="text-xs text-muted-foreground mt-0.5 max-w-[220px]">
                  {metric.description}
                </div>
              </TableCell>
              {values.map((value, i) => (
                <TableCell
                  key={companies[i].ticker}
                  className={cn(
                    "text-center tabular-nums font-medium",
                    i === bestIdx && "text-emerald-600 dark:text-emerald-400 bg-emerald-500/5",
                    i === worstIdx && numericValues.length >= 2 && "text-red-600 dark:text-red-400 bg-red-500/5",
                  )}
                >
                  {value === null || value === undefined
                    ? <span className="text-muted-foreground">--</span>
                    : formatMetricValue(value, metric.format)}
                </TableCell>
              ))}
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

export { ComparisonTable };
