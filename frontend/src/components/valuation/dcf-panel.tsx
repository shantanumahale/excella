"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency } from "@/lib/formatters";
import { useCustomDCF } from "@/hooks/use-valuation";
import type { DCFParams, DCFResult, ValuationResult } from "@/lib/types";

interface DCFPanelProps {
  ticker: string;
  data: ValuationResult | null;
  isLoading: boolean;
}

export function DCFPanel({ ticker, data, isLoading }: DCFPanelProps) {
  const dcf = data?.models?.dcf ?? null;

  const [growthRate, setGrowthRate] = useState("10");
  const [terminalGrowth, setTerminalGrowth] = useState("2.5");
  const [discountRate, setDiscountRate] = useState(
    data?.wacc?.wacc ? (data.wacc.wacc * 100).toFixed(1) : "10",
  );
  const [projectionYears, setProjectionYears] = useState("5");

  const customDCF = useCustomDCF(ticker);
  const customResult = customDCF.data?.models?.dcf ?? null;
  const displayDCF = customResult ?? dcf;

  function handleRecalculate() {
    const params: DCFParams = {
      growth_rate: parseFloat(growthRate) / 100,
      terminal_growth: parseFloat(terminalGrowth) / 100,
      wacc: parseFloat(discountRate) / 100,
      projection_years: parseInt(projectionYears, 10),
      terminal_method: "perpetuity",
    };
    customDCF.mutate(params);
  }

  if (isLoading) {
    return <Skeleton className="h-[300px] w-full" />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>DCF Model</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Inputs */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <div>
            <label className="mb-1 block text-sm text-muted-foreground">
              Growth Rate (%)
            </label>
            <Input
              type="number"
              value={growthRate}
              onChange={(e) => setGrowthRate(e.target.value)}
              step="0.5"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-muted-foreground">
              Terminal Growth (%)
            </label>
            <Input
              type="number"
              value={terminalGrowth}
              onChange={(e) => setTerminalGrowth(e.target.value)}
              step="0.5"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-muted-foreground">
              Discount Rate (%)
            </label>
            <Input
              type="number"
              value={discountRate}
              onChange={(e) => setDiscountRate(e.target.value)}
              step="0.5"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-muted-foreground">
              Years
            </label>
            <Input
              type="number"
              value={projectionYears}
              onChange={(e) => setProjectionYears(e.target.value)}
              min="1"
              max="15"
            />
          </div>
        </div>

        <Button onClick={handleRecalculate} disabled={customDCF.isPending}>
          {customDCF.isPending ? "Calculating..." : "Recalculate"}
        </Button>

        {/* Results */}
        {displayDCF && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
              <ResultItem
                label="Intrinsic Value / Share"
                value={formatCurrency(displayDCF.intrinsic_value_per_share)}
              />
              <ResultItem
                label="Enterprise Value"
                value={formatCurrency(displayDCF.enterprise_value)}
              />
              <ResultItem
                label="Terminal Value"
                value={formatCurrency(displayDCF.terminal_value)}
              />
            </div>

            {/* Projected FCFF */}
            <div>
              <p className="mb-2 text-sm font-medium text-muted-foreground">
                Projected Free Cash Flow
              </p>
              <div className="flex gap-2 overflow-x-auto">
                {displayDCF.projected_fcff.map((val, i) => (
                  <div
                    key={i}
                    className="flex-shrink-0 rounded border border-border px-3 py-1.5 text-sm"
                  >
                    <span className="text-muted-foreground">Y{i + 1}: </span>
                    <span className="font-medium">{formatCurrency(val)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {!displayDCF && (
          <p className="text-sm text-muted-foreground">
            DCF not available — company may have negative free cash flow.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function ResultItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}
