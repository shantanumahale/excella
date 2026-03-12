"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { METRIC_CATEGORIES, CATEGORY_COLORS } from "@/lib/constants";
import { getMetricsByCategory } from "@/lib/metric-metadata";
import { cn } from "@/lib/utils";
import { Columns3 } from "lucide-react";

const STORAGE_KEY = "excella-screener-columns";

interface ColumnEditorProps {
  selectedColumns: string[];
  onColumnsChange: (columns: string[]) => void;
}

export function ColumnEditor({ selectedColumns, onColumnsChange }: ColumnEditorProps) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<Set<string>>(new Set(selectedColumns));

  // Sync draft when dialog opens
  useEffect(() => {
    if (open) {
      setDraft(new Set(selectedColumns));
    }
  }, [open, selectedColumns]);

  const toggleMetric = useCallback((key: string) => {
    setDraft((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }, []);

  const toggleCategory = useCallback((categoryId: string) => {
    const metrics = getMetricsByCategory(categoryId);
    setDraft((prev) => {
      const next = new Set(prev);
      const allSelected = metrics.every((m) => next.has(m.key));
      if (allSelected) {
        metrics.forEach((m) => next.delete(m.key));
      } else {
        metrics.forEach((m) => next.add(m.key));
      }
      return next;
    });
  }, []);

  const handleSave = () => {
    const arr = Array.from(draft);
    onColumnsChange(arr);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(arr));
    } catch {
      // localStorage unavailable
    }
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium h-9 px-4 border border-border bg-transparent shadow-sm hover:bg-accent hover:text-accent-foreground transition-colors">
        <Columns3 className="h-4 w-4" />
        Columns
        <Badge variant="secondary" className="text-[10px] ml-1">
          {selectedColumns.length}
        </Badge>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Customize Columns</DialogTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Select which metrics to display in the results table.
          </p>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto mt-4 -mx-6 px-6 space-y-5">
          {METRIC_CATEGORIES.map((cat) => {
            const metrics = getMetricsByCategory(cat.id);
            const selectedCount = metrics.filter((m) => draft.has(m.key)).length;
            const allSelected = selectedCount === metrics.length;
            const someSelected = selectedCount > 0 && !allSelected;

            return (
              <div key={cat.id}>
                {/* Category header */}
                <div className="flex items-center gap-3 mb-2">
                  <button
                    className="flex items-center gap-2 text-sm font-medium hover:text-foreground transition-colors"
                    onClick={() => toggleCategory(cat.id)}
                  >
                    <Checkbox
                      checked={allSelected}
                      onCheckedChange={() => toggleCategory(cat.id)}
                      className={cn(someSelected && "opacity-60")}
                    />
                    <span
                      className={cn(
                        "h-2 w-2 rounded-full shrink-0",
                        CATEGORY_COLORS[cat.id] ?? "bg-muted",
                      )}
                    />
                    {cat.label}
                  </button>
                  <span className="text-xs text-muted-foreground">
                    {selectedCount}/{metrics.length}
                  </span>
                </div>

                {/* Metric checkboxes */}
                <div className="grid grid-cols-2 gap-x-6 gap-y-1 pl-7">
                  {metrics.map((metric) => (
                    <label
                      key={metric.key}
                      className="flex items-center gap-2 py-1 text-sm cursor-pointer hover:text-foreground transition-colors text-muted-foreground"
                    >
                      <Checkbox
                        checked={draft.has(metric.key)}
                        onCheckedChange={() => toggleMetric(metric.key)}
                      />
                      <span className={cn(draft.has(metric.key) && "text-foreground")}>
                        {metric.label}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 mt-4 border-t border-border -mx-6 px-6">
          <p className="text-xs text-muted-foreground">
            {draft.size} columns selected
          </p>
          <div className="flex items-center gap-2">
            <DialogClose className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium h-9 px-4 border border-border bg-transparent shadow-sm hover:bg-accent hover:text-accent-foreground transition-colors">
              Cancel
            </DialogClose>
            <Button onClick={handleSave}>
              Apply
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/** Load saved columns from localStorage, or return fallback */
export function loadSavedColumns(fallback: string[]): string[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    }
  } catch {
    // localStorage unavailable
  }
  return fallback;
}
