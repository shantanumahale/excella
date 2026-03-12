// ---------------------------------------------------------------------------
// Value formatting utilities for the financial screener UI
// ---------------------------------------------------------------------------

/**
 * Format a number with commas and fixed decimals.
 * Returns "—" for null / undefined / NaN.
 */
export function formatNumber(
  value: number | null | undefined,
  decimals: number = 2,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Format a decimal ratio as a percentage (e.g. 0.1523 → "15.23%").
 */
export function formatPercent(
  value: number | null | undefined,
  decimals: number = 2,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${(value * 100).toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}%`;
}

/**
 * Format a number as USD currency with commas.
 */
export function formatCurrency(
  value: number | null | undefined,
  decimals: number = 0,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `$${value.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}`;
}

/**
 * Format a ratio value (no special prefix/suffix, just fixed decimals).
 */
export function formatRatio(
  value: number | null | undefined,
  decimals: number = 2,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Format large numbers with abbreviated suffixes (e.g. 1.2B, 345M, 12.5K).
 */
export function formatLargeNumber(
  value: number | null | undefined,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";

  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";

  if (abs >= 1_000_000_000_000) {
    return `${sign}${(abs / 1_000_000_000_000).toFixed(2)}T`;
  }
  if (abs >= 1_000_000_000) {
    return `${sign}${(abs / 1_000_000_000).toFixed(2)}B`;
  }
  if (abs >= 1_000_000) {
    return `${sign}${(abs / 1_000_000).toFixed(2)}M`;
  }
  if (abs >= 1_000) {
    return `${sign}${(abs / 1_000).toFixed(2)}K`;
  }
  return `${sign}${abs.toFixed(2)}`;
}

/**
 * Format an ISO date string as "Jan 15, 2024".
 */
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/**
 * Format a date for chart X-axis ticks.
 * Shows "Oct 2025" for shorter ranges, "2025" when span > 8 years.
 */
export function formatChartTick(dateStr: string, spanYears: number): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return dateStr;

  if (spanYears > 8) {
    return d.toLocaleDateString("en-US", { year: "numeric", timeZone: "UTC" });
  }
  return d.toLocaleDateString("en-US", { month: "short", year: "numeric", timeZone: "UTC" });
}

/**
 * Format a date for chart tooltip / hover display.
 * Always shows "Oct 15, 2025" style.
 */
export function formatChartTooltipDate(dateStr: string): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}

/**
 * Compute the span in years from an array of date strings.
 */
export function computeDateSpanYears(dates: string[]): number {
  if (dates.length < 2) return 0;
  const times = dates
    .map((d) => new Date(d).getTime())
    .filter((t) => !Number.isNaN(t));
  if (times.length < 2) return 0;
  const min = Math.min(...times);
  const max = Math.max(...times);
  return (max - min) / (365.25 * 24 * 60 * 60 * 1000);
}

// ---------------------------------------------------------------------------
// Dispatcher — pick formatter based on format type
// ---------------------------------------------------------------------------

export type FormatType =
  | "percent"
  | "ratio"
  | "currency"
  | "number"
  | "large_number"
  | "score"
  | "boolean"
  | "date";

/**
 * Dispatch to the appropriate formatter based on a format type string.
 */
export function formatMetricValue(
  value: number | null | undefined,
  formatType: FormatType,
): string {
  switch (formatType) {
    case "percent":
      return formatPercent(value);
    case "ratio":
      return formatRatio(value);
    case "currency":
      return formatCurrency(value);
    case "large_number":
      return formatLargeNumber(value);
    case "number":
      return formatNumber(value);
    case "score":
      return formatNumber(value, 1);
    case "boolean":
      if (value === null || value === undefined) return "—";
      return value ? "Yes" : "No";
    case "date":
      return "—";
    default:
      return formatNumber(value);
  }
}
