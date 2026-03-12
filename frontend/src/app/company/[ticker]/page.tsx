"use client";

import { useParams } from "next/navigation";
import { useCompany } from "@/hooks/use-company";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { KeyMetricsGrid } from "@/components/company/key-metrics-grid";
import { ForensicScores } from "@/components/company/forensic-scores";
import { formatLargeNumber, formatNumber } from "@/lib/formatters";
import { METRIC_CATEGORIES } from "@/lib/constants";
import { getMetricsByCategory } from "@/lib/metric-metadata";
import { formatMetricValue } from "@/lib/formatters";
import type { DerivedMetrics } from "@/lib/types";
import { useState } from "react";
import {
  Building2,
  Globe,
  Users,
  Calendar,
  Hash,
  ExternalLink,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

function InfoItem({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: string | null | undefined;
}) {
  return (
    <div className="flex items-center gap-3 py-2">
      <Icon className="h-4 w-4 text-muted-foreground shrink-0" />
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-sm font-medium text-foreground truncate">
          {value || "--"}
        </p>
      </div>
    </div>
  );
}

function CategoryMetricsCard({
  categoryId,
  categoryLabel,
  metrics,
}: {
  categoryId: string;
  categoryLabel: string;
  metrics: DerivedMetrics;
}) {
  const [expanded, setExpanded] = useState(false);
  const metricsMeta = getMetricsByCategory(categoryId);
  const categoryData = metrics[categoryId as keyof DerivedMetrics];

  if (!categoryData) return null;

  // Check if there's any non-null data in this category
  const hasData = Object.values(categoryData).some((v) => v !== null);
  if (!hasData) return null;

  return (
    <Card>
      <button
        className="w-full text-left"
        onClick={() => setExpanded(!expanded)}
      >
        <CardHeader className="flex flex-row items-center justify-between py-4">
          <CardTitle className="text-sm">{categoryLabel}</CardTitle>
          {expanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
        </CardHeader>
      </button>
      {expanded && (
        <CardContent className="pt-0">
          <div className="grid grid-cols-2 gap-x-6 gap-y-2 sm:grid-cols-3 lg:grid-cols-4">
            {metricsMeta.map((meta) => {
              const value = categoryData[meta.key] ?? null;
              // Skip complex object values (like components/signals)
              if (typeof value === "object" && value !== null) return null;
              return (
                <div key={meta.key} className="py-1.5">
                  <p className="text-xs text-muted-foreground truncate">
                    {meta.label}
                  </p>
                  <p className="text-sm font-medium tabular-nums text-foreground">
                    {formatMetricValue(value as number | null, meta.format)}
                  </p>
                </div>
              );
            })}
          </div>
        </CardContent>
      )}
    </Card>
  );
}

export default function CompanyOverviewPage() {
  const params = useParams<{ ticker: string }>();
  const ticker = params.ticker.toUpperCase();
  const { company, isLoading } = useCompany(ticker);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <Skeleton className="h-[400px] rounded-lg" />
          </div>
          <div className="lg:col-span-2">
            <Skeleton className="h-[400px] rounded-lg" />
          </div>
        </div>
      </div>
    );
  }

  if (!company) {
    return (
      <div className="py-16 text-center">
        <p className="text-muted-foreground">Company not found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Top section: Company Info + Forensic Scores */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Company Info Card */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Company Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <InfoItem icon={Building2} label="Sector" value={company.sector} />
            <InfoItem
              icon={Building2}
              label="Industry"
              value={company.industry}
            />
            <InfoItem
              icon={Globe}
              label="Exchange"
              value={company.exchange}
            />
            <InfoItem icon={Hash} label="CIK" value={company.cik} />
            <InfoItem
              icon={Calendar}
              label="Fiscal Year End"
              value={company.fiscal_year_end}
            />
            <InfoItem
              icon={Users}
              label="Employees"
              value={
                company.employees
                  ? formatNumber(company.employees, 0)
                  : null
              }
            />
            <InfoItem
              icon={Building2}
              label="Market Cap"
              value={
                company.market_cap
                  ? formatLargeNumber(company.market_cap)
                  : null
              }
            />

            {company.website && (
              <div className="pt-2">
                <a
                  href={company.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
                >
                  <Globe className="h-3.5 w-3.5" />
                  Website
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            )}

            {company.description && (
              <>
                <Separator className="my-3" />
                <div>
                  <p className="text-xs text-muted-foreground mb-1">
                    Description
                  </p>
                  <p className="text-sm text-foreground leading-relaxed line-clamp-6">
                    {company.description}
                  </p>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Forensic Scores + Key highlights */}
        <div className="lg:col-span-2 space-y-6">
          <div>
            <h2 className="text-lg font-semibold mb-3">Forensic Scores</h2>
            <ForensicScores
              forensicMetrics={company.latest_metrics?.forensic}
            />
          </div>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Key Financial Metrics</h2>
        <KeyMetricsGrid metrics={company.latest_metrics} />
      </div>

      {/* Expandable category cards for all metrics */}
      <div>
        <h2 className="text-lg font-semibold mb-4">All Metrics by Category</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {company.latest_metrics &&
            METRIC_CATEGORIES.map((cat) => (
              <CategoryMetricsCard
                key={cat.id}
                categoryId={cat.id}
                categoryLabel={cat.label}
                metrics={company.latest_metrics!}
              />
            ))}
        </div>
        {!company.latest_metrics && (
          <p className="text-sm text-muted-foreground">
            No metrics data available for this company.
          </p>
        )}
      </div>
    </div>
  );
}
