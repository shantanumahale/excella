"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, formatPercent, formatRatio } from "@/lib/formatters";
import type { ValuationResult } from "@/lib/types";

interface ValuationSummaryProps {
  data: ValuationResult | null;
  isLoading: boolean;
}

function marginBadgeVariant(mos: number | null): "success" | "danger" | "secondary" {
  if (mos === null) return "secondary";
  if (mos >= 0.15) return "success";
  if (mos <= -0.15) return "danger";
  return "secondary";
}

function marginLabel(mos: number | null): string {
  if (mos === null) return "N/A";
  if (mos >= 0.30) return "Undervalued";
  if (mos >= 0.15) return "Slight Discount";
  if (mos >= -0.15) return "Fair Value";
  if (mos >= -0.30) return "Slight Premium";
  return "Overvalued";
}

export function ValuationSummary({ data, isLoading }: ValuationSummaryProps) {
  if (isLoading) {
    return <Skeleton className="h-[200px] w-full" />;
  }

  if (!data) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-muted-foreground">No valuation data available.</p>
        </CardContent>
      </Card>
    );
  }

  const summary = data.summary;
  const mos = summary?.margin_of_safety ?? null;
  const consensus = summary?.consensus_value ?? null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Intrinsic Value Estimate</span>
          <Badge variant={marginBadgeVariant(mos)}>
            {marginLabel(mos)}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
          <div>
            <p className="text-sm text-muted-foreground">Consensus Value</p>
            <p className="text-2xl font-bold">{formatCurrency(consensus)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Margin of Safety</p>
            <p className="text-2xl font-bold">{formatPercent(mos)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Beta</p>
            <p className="text-2xl font-bold">
              {formatRatio(data.beta?.beta ?? null)}
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">WACC</p>
            <p className="text-2xl font-bold">
              {formatPercent(data.wacc?.wacc ?? null)}
            </p>
          </div>
        </div>

        {summary?.model_values && summary.model_values.length > 0 && (
          <div className="mt-6">
            <p className="mb-2 text-sm font-medium text-muted-foreground">
              Model Estimates ({summary.model_count} models)
            </p>
            <div className="flex flex-wrap gap-3">
              {summary.model_values.map((mv) => (
                <div
                  key={mv.model}
                  className="rounded-md border border-border px-3 py-1.5 text-sm"
                >
                  <span className="text-muted-foreground capitalize">{mv.model.replace("_", " ")}: </span>
                  <span className="font-medium">{formatCurrency(mv.value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
