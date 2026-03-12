"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface ForensicScoresProps {
  forensicMetrics: Record<string, number | null> | undefined;
}

interface ScoreZone {
  label: string;
  color: string;
  bgColor: string;
  borderColor: string;
}

function getAltmanZone(score: number | null): ScoreZone {
  if (score === null) return { label: "N/A", color: "text-muted-foreground", bgColor: "bg-muted", borderColor: "border-border" };
  if (score > 2.99) return { label: "Safe", color: "text-emerald-600 dark:text-emerald-400", bgColor: "bg-emerald-50 dark:bg-emerald-950/30", borderColor: "border-emerald-200 dark:border-emerald-800" };
  if (score >= 1.81) return { label: "Grey Zone", color: "text-amber-600 dark:text-amber-400", bgColor: "bg-amber-50 dark:bg-amber-950/30", borderColor: "border-amber-200 dark:border-amber-800" };
  return { label: "Distress", color: "text-red-600 dark:text-red-400", bgColor: "bg-red-50 dark:bg-red-950/30", borderColor: "border-red-200 dark:border-red-800" };
}

function getPiotroskiZone(score: number | null): ScoreZone {
  if (score === null) return { label: "N/A", color: "text-muted-foreground", bgColor: "bg-muted", borderColor: "border-border" };
  if (score >= 7) return { label: "Strong", color: "text-emerald-600 dark:text-emerald-400", bgColor: "bg-emerald-50 dark:bg-emerald-950/30", borderColor: "border-emerald-200 dark:border-emerald-800" };
  if (score >= 4) return { label: "Moderate", color: "text-amber-600 dark:text-amber-400", bgColor: "bg-amber-50 dark:bg-amber-950/30", borderColor: "border-amber-200 dark:border-amber-800" };
  return { label: "Weak", color: "text-red-600 dark:text-red-400", bgColor: "bg-red-50 dark:bg-red-950/30", borderColor: "border-red-200 dark:border-red-800" };
}

function getBeneishZone(score: number | null): ScoreZone {
  if (score === null) return { label: "N/A", color: "text-muted-foreground", bgColor: "bg-muted", borderColor: "border-border" };
  if (score < -2.22) return { label: "Low Risk", color: "text-emerald-600 dark:text-emerald-400", bgColor: "bg-emerald-50 dark:bg-emerald-950/30", borderColor: "border-emerald-200 dark:border-emerald-800" };
  if (score <= -1.78) return { label: "Grey Zone", color: "text-amber-600 dark:text-amber-400", bgColor: "bg-amber-50 dark:bg-amber-950/30", borderColor: "border-amber-200 dark:border-amber-800" };
  return { label: "High Risk", color: "text-red-600 dark:text-red-400", bgColor: "bg-red-50 dark:bg-red-950/30", borderColor: "border-red-200 dark:border-red-800" };
}

interface ScoreCardProps {
  title: string;
  subtitle: string;
  value: number | null;
  zone: ScoreZone;
  maxValue?: number;
}

function ScoreCard({ title, subtitle, value, zone, maxValue }: ScoreCardProps) {
  const displayValue = value !== null ? value.toFixed(2) : "--";
  const fillPercent =
    value !== null && maxValue
      ? Math.min(Math.max((value / maxValue) * 100, 0), 100)
      : 0;

  return (
    <Card className={cn("border", zone.borderColor, zone.bgColor)}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-semibold text-foreground">{title}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>
          </div>
          <span
            className={cn(
              "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
              zone.color,
              zone.bgColor
            )}
          >
            {zone.label}
          </span>
        </div>
        <div className="mt-4">
          <span className={cn("text-3xl font-bold tabular-nums", zone.color)}>
            {displayValue}
          </span>
        </div>
        {maxValue && value !== null && (
          <div className="mt-3 h-2 w-full rounded-full bg-muted overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                zone.label === "Safe" || zone.label === "Strong" || zone.label === "Low Risk"
                  ? "bg-emerald-500"
                  : zone.label === "Grey Zone" || zone.label === "Moderate"
                    ? "bg-amber-500"
                    : "bg-red-500"
              )}
              style={{ width: `${fillPercent}%` }}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function ForensicScores({ forensicMetrics }: ForensicScoresProps) {
  if (!forensicMetrics) {
    return (
      <p className="text-sm text-muted-foreground">
        No forensic data available.
      </p>
    );
  }

  const altmanZ = forensicMetrics.altman_z_score ?? null;
  const piotroskiF = forensicMetrics.piotroski_f_score ?? null;
  const beneishM = forensicMetrics.beneish_m_score ?? null;

  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <ScoreCard
        title="Altman Z-Score"
        subtitle="Bankruptcy risk assessment"
        value={altmanZ}
        zone={getAltmanZone(altmanZ)}
        maxValue={6}
      />
      <ScoreCard
        title="Piotroski F-Score"
        subtitle="Financial strength (0-9)"
        value={piotroskiF}
        zone={getPiotroskiZone(piotroskiF)}
        maxValue={9}
      />
      <ScoreCard
        title="Beneish M-Score"
        subtitle="Earnings manipulation risk"
        value={beneishM}
        zone={getBeneishZone(beneishM)}
      />
    </div>
  );
}
