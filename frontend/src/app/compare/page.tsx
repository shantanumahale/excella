"use client";

import { useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useQueries } from "@tanstack/react-query";
import { getCompany } from "@/lib/api";
import { METRIC_CATEGORIES } from "@/lib/constants";
import { TickerSelector } from "@/components/compare/ticker-selector";
import { ComparisonTable } from "@/components/compare/comparison-table";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { TableSkeleton } from "@/components/shared/loading-skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { GitCompareArrows } from "lucide-react";

function ComparePageInner() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const tickerParam = searchParams.get("tickers") ?? "";
  const tickers = tickerParam
    ? tickerParam.split(",").filter(Boolean).slice(0, 5)
    : [];

  const updateTickers = useCallback(
    (newTickers: string[]) => {
      const params = new URLSearchParams(searchParams.toString());
      if (newTickers.length > 0) {
        params.set("tickers", newTickers.join(","));
      } else {
        params.delete("tickers");
      }
      router.replace(`/compare?${params.toString()}`);
    },
    [searchParams, router],
  );

  const handleAdd = useCallback(
    (ticker: string) => {
      if (!tickers.includes(ticker) && tickers.length < 5) {
        updateTickers([...tickers, ticker]);
      }
    },
    [tickers, updateTickers],
  );

  const handleRemove = useCallback(
    (ticker: string) => {
      updateTickers(tickers.filter((t) => t !== ticker));
    },
    [tickers, updateTickers],
  );

  // Fetch all company details in parallel
  const companyQueries = useQueries({
    queries: tickers.map((ticker) => ({
      queryKey: ["company", ticker],
      queryFn: () => getCompany(ticker),
      staleTime: 5 * 60 * 1000,
      retry: 1,
    })),
  });

  const isLoading = companyQueries.some((q) => q.isLoading);
  const companies = companyQueries
    .filter((q) => q.data)
    .map((q) => q.data!);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Peer Comparison
        </h1>
        <p className="mt-1 text-muted-foreground">
          Compare financial metrics across up to 5 companies side by side.
        </p>
      </div>

      {/* Ticker selector */}
      <Card>
        <CardContent className="pt-6">
          <TickerSelector
            tickers={tickers}
            onAdd={handleAdd}
            onRemove={handleRemove}
          />
        </CardContent>
      </Card>

      {/* Comparison content */}
      {tickers.length === 0 ? (
        <EmptyState
          icon={GitCompareArrows}
          title="No companies selected"
          description="Search and add companies above to compare their financial metrics across categories."
        />
      ) : isLoading ? (
        <div className="space-y-4">
          <div className="flex gap-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-24 rounded-md" />
            ))}
          </div>
          <TableSkeleton rows={10} columns={tickers.length + 1} />
        </div>
      ) : (
        <Tabs defaultValue="profitability">
          <TabsList className="flex flex-wrap h-auto gap-1 bg-transparent p-0">
            {METRIC_CATEGORIES.map((cat) => (
              <TabsTrigger
                key={cat.id}
                value={cat.id}
                className="rounded-md border border-border data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:border-primary"
              >
                {cat.label}
              </TabsTrigger>
            ))}
          </TabsList>

          {METRIC_CATEGORIES.map((cat) => (
            <TabsContent key={cat.id} value={cat.id}>
              <Card className="mt-4">
                <CardContent className="p-0">
                  <ComparisonTable
                    companies={companies}
                    category={cat.id}
                  />
                </CardContent>
              </Card>
            </TabsContent>
          ))}
        </Tabs>
      )}
    </div>
  );
}

export default function ComparePage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-6">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-12 w-full max-w-md" />
        </div>
      }
    >
      <ComparePageInner />
    </Suspense>
  );
}
