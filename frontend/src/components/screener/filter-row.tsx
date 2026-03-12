"use client";

import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tooltip } from "@/components/ui/tooltip";
import { X, Info } from "lucide-react";
import { getMetricMeta } from "@/lib/metric-metadata";
import { METRIC_CATEGORIES } from "@/lib/constants";
import type { ScreenerFilterState } from "@/hooks/use-screener";

const OPERATORS = [
  { value: "gt", label: ">" },
  { value: "gte", label: ">=" },
  { value: "lt", label: "<" },
  { value: "lte", label: "<=" },
  { value: "eq", label: "=" },
  { value: "between", label: "Between" },
  { value: "not_null", label: "Has value" },
] as const;

interface FilterRowProps {
  filter: ScreenerFilterState;
  index: number;
  onUpdate: (index: number, patch: Partial<ScreenerFilterState>) => void;
  onRemove: (index: number) => void;
}

export function FilterRow({ filter, index, onUpdate, onRemove }: FilterRowProps) {
  const meta = getMetricMeta(filter.metric);
  const categoryMeta = METRIC_CATEGORIES.find((c) => c.id === filter.category);

  const categoryLabel = categoryMeta?.label ?? filter.category;
  const metricLabel = meta?.label ?? filter.metric;

  return (
    <div className="group rounded-lg border border-border bg-card p-3 space-y-2.5 transition-colors hover:border-primary/30">
      {/* Header: metric name + remove */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Badge variant="secondary" className="shrink-0 text-[10px] font-medium uppercase tracking-wide">
            {categoryLabel}
          </Badge>
          <span className="text-sm font-medium text-foreground truncate">
            {metricLabel}
          </span>
          {meta?.description && (
            <Tooltip content={meta.description} side="right">
              <Info className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
            </Tooltip>
          )}
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
          onClick={() => onRemove(index)}
          aria-label="Remove filter"
        >
          <X className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Operator + value inputs */}
      <div className="flex items-center gap-2">
        <Select
          className="w-[110px] shrink-0"
          value={filter.operator}
          onChange={(e) => onUpdate(index, { operator: e.target.value })}
        >
          {OPERATORS.map((op) => (
            <option key={op.value} value={op.value}>
              {op.label}
            </option>
          ))}
        </Select>

        {filter.operator !== "not_null" && filter.operator !== "between" && (
          <Input
            type="number"
            step="any"
            placeholder="Value"
            className="flex-1"
            value={filter.value ?? ""}
            onChange={(e) =>
              onUpdate(index, {
                value: e.target.value === "" ? null : Number(e.target.value),
              })
            }
          />
        )}

        {filter.operator === "between" && (
          <>
            <Input
              type="number"
              step="any"
              placeholder="Min"
              className="flex-1"
              value={filter.value ?? ""}
              onChange={(e) =>
                onUpdate(index, {
                  value: e.target.value === "" ? null : Number(e.target.value),
                })
              }
            />
            <span className="text-xs text-muted-foreground">to</span>
            <Input
              type="number"
              step="any"
              placeholder="Max"
              className="flex-1"
              value={filter.valueTo ?? ""}
              onChange={(e) =>
                onUpdate(index, {
                  valueTo: e.target.value === "" ? null : Number(e.target.value),
                })
              }
            />
          </>
        )}
      </div>
    </div>
  );
}
