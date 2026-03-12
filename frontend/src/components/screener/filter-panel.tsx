"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { METRIC_CATEGORIES, CATEGORY_COLORS } from "@/lib/constants";
import { getMetricsByCategory, type MetricMeta } from "@/lib/metric-metadata";
import { FilterRow } from "./filter-row";
import { Plus, Trash2, SlidersHorizontal, ChevronLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ScreenerFilterState } from "@/hooks/use-screener";

interface FilterPanelProps {
  filters: ScreenerFilterState[];
  onAdd: (category: string, metric: string) => void;
  onUpdate: (index: number, patch: Partial<ScreenerFilterState>) => void;
  onRemove: (index: number) => void;
  onClear: () => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export function FilterPanel({
  filters,
  onAdd,
  onUpdate,
  onRemove,
  onClear,
  isCollapsed,
  onToggleCollapse,
}: FilterPanelProps) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const pickerRef = useRef<HTMLDivElement>(null);

  // Close picker on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (pickerRef.current && !pickerRef.current.contains(e.target as Node)) {
        setPickerOpen(false);
        setSelectedCategory(null);
      }
    }
    if (pickerOpen) {
      document.addEventListener("mousedown", handleClick);
    }
    return () => document.removeEventListener("mousedown", handleClick);
  }, [pickerOpen]);

  const handleSelectMetric = (category: string, metric: MetricMeta) => {
    onAdd(category, metric.key);
    setPickerOpen(false);
    setSelectedCategory(null);
  };

  if (isCollapsed) {
    return (
      <div className="flex flex-col items-center gap-2 py-4 px-1">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleCollapse}
          aria-label="Expand filters"
        >
          <SlidersHorizontal className="h-4 w-4" />
        </Button>
        {filters.length > 0 && (
          <Badge variant="default" className="text-[10px] h-5 w-5 flex items-center justify-center p-0 rounded-full">
            {filters.length}
          </Badge>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold text-foreground">Filters</h2>
          {filters.length > 0 && (
            <Badge variant="secondary" className="text-[10px]">
              {filters.length}
            </Badge>
          )}
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={onToggleCollapse}
          aria-label="Collapse filters"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
      </div>

      {/* Add filter button + picker */}
      <div className="px-4 pt-3 relative" ref={pickerRef}>
        <Button
          variant="outline"
          size="sm"
          className="w-full justify-start gap-2"
          onClick={() => {
            setPickerOpen(!pickerOpen);
            setSelectedCategory(null);
          }}
        >
          <Plus className="h-3.5 w-3.5" />
          Add Filter
        </Button>

        {/* Cascading dropdown */}
        {pickerOpen && (
          <div className="absolute left-4 right-4 top-full z-50 mt-1 rounded-lg border border-border bg-card shadow-lg overflow-hidden">
            {!selectedCategory ? (
              // Step 1: Pick category
              <div className="max-h-80 overflow-y-auto py-1">
                {METRIC_CATEGORIES.map((cat) => {
                  const count = getMetricsByCategory(cat.id).length;
                  return (
                    <button
                      key={cat.id}
                      className="flex w-full items-center gap-3 px-3 py-2 text-left text-sm hover:bg-accent transition-colors"
                      onClick={() => setSelectedCategory(cat.id)}
                    >
                      <span
                        className={cn(
                          "h-2 w-2 rounded-full shrink-0",
                          CATEGORY_COLORS[cat.id] ?? "bg-muted",
                        )}
                      />
                      <span className="flex-1 font-medium">{cat.label}</span>
                      <span className="text-xs text-muted-foreground">{count}</span>
                    </button>
                  );
                })}
              </div>
            ) : (
              // Step 2: Pick metric from category
              <div>
                <button
                  className="flex w-full items-center gap-2 border-b border-border px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
                  onClick={() => setSelectedCategory(null)}
                >
                  <ChevronLeft className="h-3 w-3" />
                  {METRIC_CATEGORIES.find((c) => c.id === selectedCategory)?.label}
                </button>
                <div className="max-h-64 overflow-y-auto py-1">
                  {getMetricsByCategory(selectedCategory).map((metric) => {
                    const alreadyAdded = filters.some((f) => f.metric === metric.key);
                    return (
                      <button
                        key={metric.key}
                        className={cn(
                          "flex w-full items-center gap-3 px-3 py-2 text-left text-sm transition-colors",
                          alreadyAdded
                            ? "opacity-40 cursor-not-allowed"
                            : "hover:bg-accent",
                        )}
                        onClick={() => {
                          if (!alreadyAdded) {
                            handleSelectMetric(selectedCategory, metric);
                          }
                        }}
                        disabled={alreadyAdded}
                      >
                        <span className="flex-1">{metric.label}</span>
                        {alreadyAdded && (
                          <span className="text-[10px] text-muted-foreground">Added</span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Active filters list */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        {filters.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <SlidersHorizontal className="h-8 w-8 text-muted-foreground/40 mb-3" />
            <p className="text-sm text-muted-foreground">No filters applied</p>
            <p className="text-xs text-muted-foreground/70 mt-1">
              Add filters to narrow down companies
            </p>
          </div>
        )}
        {filters.map((filter, idx) => (
          <FilterRow
            key={`${filter.metric}-${idx}`}
            filter={filter}
            index={idx}
            onUpdate={onUpdate}
            onRemove={onRemove}
          />
        ))}
      </div>

      {/* Clear all */}
      {filters.length > 0 && (
        <div className="px-4 py-3 border-t border-border">
          <Button
            variant="ghost"
            size="sm"
            className="w-full text-muted-foreground hover:text-destructive"
            onClick={onClear}
          >
            <Trash2 className="h-3.5 w-3.5 mr-2" />
            Clear All Filters
          </Button>
        </div>
      )}
    </div>
  );
}
