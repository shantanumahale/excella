"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useFinancials } from "@/hooks/use-financials";
import { FinancialTable } from "@/components/company/financial-table";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { TableSkeleton } from "@/components/shared/loading-skeleton";
import { cn } from "@/lib/utils";

const STATEMENT_TYPES = [
  { id: "income", label: "Income Statement" },
  { id: "balance", label: "Balance Sheet" },
  { id: "cashflow", label: "Cash Flow" },
];

const PERIOD_TYPES = [
  { id: "annual", label: "Annual" },
  { id: "quarterly", label: "Quarterly" },
];

export default function FinancialsPage() {
  const params = useParams<{ ticker: string }>();
  const ticker = params.ticker.toUpperCase();

  const [statementType, setStatementType] = useState("income");
  const [periodType, setPeriodType] = useState("annual");

  const { data: statements, isLoading } = useFinancials({
    ticker,
    statement_type: statementType,
    period_type: periodType,
    limit: 10,
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-lg font-semibold">Financial Statements</h2>
        <div className="flex items-center gap-2">
          {PERIOD_TYPES.map((pt) => (
            <Button
              key={pt.id}
              variant={periodType === pt.id ? "default" : "outline"}
              size="sm"
              onClick={() => setPeriodType(pt.id)}
            >
              {pt.label}
            </Button>
          ))}
        </div>
      </div>

      <Tabs defaultValue="income" onValueChange={setStatementType}>
        <TabsList>
          {STATEMENT_TYPES.map((st) => (
            <TabsTrigger key={st.id} value={st.id}>
              {st.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {STATEMENT_TYPES.map((st) => (
          <TabsContent key={st.id} value={st.id}>
            {isLoading ? (
              <TableSkeleton rows={15} columns={8} />
            ) : (
              <FinancialTable
                statements={statements ?? []}
                statementType={st.id}
              />
            )}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
