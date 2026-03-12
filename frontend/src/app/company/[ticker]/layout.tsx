"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getLatestPrice, getReturns } from "@/lib/api";
import { useCompany } from "@/hooks/use-company";
import { CompanyHeader } from "@/components/company/company-header";
import { CompanyNav } from "@/components/company/company-nav";
import { Separator } from "@/components/ui/separator";

export default function CompanyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams<{ ticker: string }>();
  const ticker = params.ticker.toUpperCase();

  const { company, isLoading: companyLoading } = useCompany(ticker);

  const { data: latestPrice, isLoading: priceLoading } = useQuery({
    queryKey: ["latestPrice", ticker],
    queryFn: () => getLatestPrice(ticker),
    enabled: !!ticker,
    staleTime: 60 * 1000,
  });

  const { data: returns, isLoading: returnsLoading } = useQuery({
    queryKey: ["returns", ticker],
    queryFn: () => getReturns(ticker),
    enabled: !!ticker,
    staleTime: 60 * 1000,
  });

  const isLoading = companyLoading || priceLoading || returnsLoading;

  return (
    <div className="space-y-6">
      <CompanyHeader
        company={company}
        latestPrice={latestPrice}
        returns={returns}
        isLoading={isLoading}
      />
      <CompanyNav ticker={ticker} />
      <Separator />
      {children}
    </div>
  );
}
