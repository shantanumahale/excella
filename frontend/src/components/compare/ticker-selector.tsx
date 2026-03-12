"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { getCompanies } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Search, X } from "lucide-react";

interface TickerSelectorProps {
  tickers: string[];
  onAdd: (ticker: string) => void;
  onRemove: (ticker: string) => void;
}

function TickerSelector({ tickers, onAdd, onRemove }: TickerSelectorProps) {
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search.trim());
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const { data: results, isFetching } = useQuery({
    queryKey: ["company-search", debouncedSearch],
    queryFn: () => getCompanies({ search: debouncedSearch, limit: 8 }),
    enabled: debouncedSearch.length >= 1,
    staleTime: 30_000,
  });

  const filteredResults = (results?.data ?? []).filter(
    (c) => !tickers.includes(c.ticker),
  );

  const handleSelect = useCallback(
    (ticker: string) => {
      if (tickers.length >= 5) return;
      onAdd(ticker);
      setSearch("");
      setDebouncedSearch("");
      setIsOpen(false);
    },
    [tickers, onAdd],
  );

  const atMax = tickers.length >= 5;

  return (
    <div className="space-y-3">
      {/* Selected tickers */}
      {tickers.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tickers.map((ticker) => (
            <Badge
              key={ticker}
              variant="secondary"
              className="gap-1.5 py-1 px-3 text-sm"
            >
              {ticker}
              <button
                type="button"
                onClick={() => onRemove(ticker)}
                className="ml-0.5 rounded-full hover:bg-background/50 p-0.5 transition-colors"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}

      {/* Search input */}
      <div ref={containerRef} className="relative max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={atMax ? "Maximum 5 companies reached" : "Search companies by name or ticker..."}
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setIsOpen(true);
            }}
            onFocus={() => {
              if (debouncedSearch.length >= 1) setIsOpen(true);
            }}
            disabled={atMax}
            className="pl-9"
          />
        </div>

        {/* Dropdown */}
        {isOpen && debouncedSearch.length >= 1 && (
          <div className="absolute z-50 mt-1 w-full rounded-lg border border-border bg-card shadow-lg">
            {isFetching && (
              <div className="px-4 py-3 text-sm text-muted-foreground">
                Searching...
              </div>
            )}

            {!isFetching && filteredResults.length === 0 && (
              <div className="px-4 py-3 text-sm text-muted-foreground">
                No results found
              </div>
            )}

            {!isFetching &&
              filteredResults.map((company) => (
                <button
                  key={company.ticker}
                  type="button"
                  className={cn(
                    "flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm transition-colors",
                    "hover:bg-muted/50 first:rounded-t-lg last:rounded-b-lg",
                  )}
                  onClick={() => handleSelect(company.ticker)}
                >
                  <span className="font-semibold text-foreground min-w-[60px]">
                    {company.ticker}
                  </span>
                  <span className="text-muted-foreground truncate">
                    {company.name}
                  </span>
                  {company.sector && (
                    <span className="ml-auto text-xs text-muted-foreground/70 shrink-0">
                      {company.sector}
                    </span>
                  )}
                </button>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}

export { TickerSelector };
