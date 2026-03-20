"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, formatPercent } from "@/lib/formatters";
import { useValuationSensitivity } from "@/hooks/use-valuation";
import type { SensitivityResult } from "@/lib/types";
import { cn } from "@/lib/utils";

interface SensitivityTableProps {
  ticker: string;
}

function cellColor(value: number | null, baseWacc: number, growthRate: number): string {
  if (value === null) return "";
  // Higher values = greener (more undervalued potential)
  if (value > 0) return "text-gain";
  return "text-loss";
}

export function SensitivityTable({ ticker }: SensitivityTableProps) {
  const { data, isLoading } = useValuationSensitivity(ticker);

  if (isLoading) {
    return <Skeleton className="h-[300px] w-full" />;
  }

  if (!data) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-muted-foreground">Sensitivity data not available.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Sensitivity Analysis (WACC vs Terminal Growth)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="sticky left-0 bg-card">WACC</TableHead>
                {data.growth_range.map((g) => (
                  <TableHead key={g} className="text-center">
                    {formatPercent(g)}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.matrix.map((row) => {
                const isBase = row.wacc === data.base_wacc;
                return (
                  <TableRow
                    key={row.wacc}
                    className={cn(isBase && "bg-muted/50")}
                  >
                    <TableCell className="sticky left-0 bg-card font-medium">
                      {formatPercent(row.wacc)}
                      {isBase && (
                        <span className="ml-1 text-xs text-muted-foreground">(base)</span>
                      )}
                    </TableCell>
                    {data.growth_range.map((g) => {
                      const val = row.values[String(g)];
                      return (
                        <TableCell key={g} className="text-center">
                          {val !== null && val !== undefined
                            ? formatCurrency(val)
                            : "—"}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
