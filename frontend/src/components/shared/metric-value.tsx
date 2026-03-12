"use client";

import { cn } from "@/lib/utils";

type MetricFormat = "percent" | "currency" | "ratio" | "number" | "score";

interface MetricValueProps {
  value: number | null | undefined;
  format: MetricFormat;
  colorCode?: boolean;
  className?: string;
}

function formatMetric(value: number, format: MetricFormat): string {
  switch (format) {
    case "percent":
      return `${(value * 100).toFixed(2)}%`;
    case "currency":
      if (Math.abs(value) >= 1_000_000_000) {
        return `$${(value / 1_000_000_000).toFixed(2)}B`;
      }
      if (Math.abs(value) >= 1_000_000) {
        return `$${(value / 1_000_000).toFixed(2)}M`;
      }
      if (Math.abs(value) >= 1_000) {
        return `$${(value / 1_000).toFixed(2)}K`;
      }
      return `$${value.toFixed(2)}`;
    case "ratio":
      return value.toFixed(2);
    case "number":
      if (Math.abs(value) >= 1_000_000_000) {
        return `${(value / 1_000_000_000).toFixed(2)}B`;
      }
      if (Math.abs(value) >= 1_000_000) {
        return `${(value / 1_000_000).toFixed(2)}M`;
      }
      if (Math.abs(value) >= 1_000) {
        return `${(value / 1_000).toFixed(2)}K`;
      }
      return value.toFixed(2);
    case "score":
      return value.toFixed(1);
    default:
      return String(value);
  }
}

function MetricValue({
  value,
  format,
  colorCode = false,
  className,
}: MetricValueProps) {
  if (value === null || value === undefined) {
    return (
      <span className={cn("text-muted-foreground", className)}>--</span>
    );
  }

  const formatted = formatMetric(value, format);

  const colorClass = colorCode
    ? value > 0
      ? "text-gain"
      : value < 0
        ? "text-loss"
        : "text-foreground"
    : "";

  return (
    <span className={cn("tabular-nums font-medium", colorClass, className)}>
      {formatted}
    </span>
  );
}

export { MetricValue, formatMetric };
export type { MetricFormat };
