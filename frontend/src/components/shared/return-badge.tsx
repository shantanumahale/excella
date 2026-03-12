"use client";

import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface ReturnBadgeProps {
  value: number | null;
  label: string;
  className?: string;
}

function ReturnBadge({ value, label, className }: ReturnBadgeProps) {
  if (value === null || value === undefined) {
    return (
      <div
        className={cn(
          "inline-flex items-center gap-1.5 rounded-md border border-border px-2 py-1 text-xs",
          className
        )}
      >
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium text-muted-foreground">--</span>
      </div>
    );
  }

  const isPositive = value > 0;
  const isNeutral = value === 0;
  const displayValue = `${isPositive ? "+" : ""}${(value * 100).toFixed(2)}%`;

  const Icon = isNeutral ? Minus : isPositive ? TrendingUp : TrendingDown;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs",
        isNeutral && "border-border bg-muted",
        isPositive && "border-gain/20 bg-gain-bg",
        !isPositive && !isNeutral && "border-loss/20 bg-loss-bg",
        className
      )}
    >
      <span className="text-muted-foreground">{label}</span>
      <Icon
        className={cn(
          "h-3 w-3",
          isNeutral && "text-muted-foreground",
          isPositive && "text-gain",
          !isPositive && !isNeutral && "text-loss"
        )}
      />
      <span
        className={cn(
          "font-medium tabular-nums",
          isNeutral && "text-muted-foreground",
          isPositive && "text-gain",
          !isPositive && !isNeutral && "text-loss"
        )}
      >
        {displayValue}
      </span>
    </div>
  );
}

export { ReturnBadge };
