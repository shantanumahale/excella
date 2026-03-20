"use client";

import { useParams } from "next/navigation";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { useValuation } from "@/hooks/use-valuation";
import { ValuationSummary } from "@/components/valuation/valuation-summary";
import { DCFPanel } from "@/components/valuation/dcf-panel";
import { SensitivityTable } from "@/components/valuation/sensitivity-table";
import { CompsTable } from "@/components/valuation/comps-table";
import { ValuationHistoryChart } from "@/components/valuation/valuation-history-chart";

export default function ValuationPage() {
  const params = useParams<{ ticker: string }>();
  const ticker = params.ticker.toUpperCase();

  const { data, isLoading } = useValuation(ticker);

  return (
    <div className="space-y-6">
      <ValuationSummary data={data} isLoading={isLoading} />

      <Tabs defaultValue="dcf">
        <TabsList>
          <TabsTrigger value="dcf">DCF</TabsTrigger>
          <TabsTrigger value="comps">Comps</TabsTrigger>
          <TabsTrigger value="sensitivity">Sensitivity</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="dcf">
          <DCFPanel ticker={ticker} data={data} isLoading={isLoading} />
        </TabsContent>

        <TabsContent value="comps">
          <CompsTable ticker={ticker} />
        </TabsContent>

        <TabsContent value="sensitivity">
          <SensitivityTable ticker={ticker} />
        </TabsContent>

        <TabsContent value="history">
          <ValuationHistoryChart ticker={ticker} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
