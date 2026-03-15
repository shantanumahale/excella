"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { getCompanies } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/providers/theme-provider";
import { useAuth } from "@/providers/auth-provider";
import {
  Search,
  Sun,
  Moon,
  BarChart3,
  GitCompareArrows,
  TrendingUp,
  Star,
  LogOut,
  User,
} from "lucide-react";

const navLinks = [
  { href: "/screener", label: "Screener", icon: BarChart3 },
  { href: "/compare", label: "Compare", icon: GitCompareArrows },
  { href: "/macro", label: "Macro", icon: TrendingUp },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { resolvedTheme, setTheme } = useTheme();
  const { user, isAuthenticated, logout } = useAuth();
  const [searchValue, setSearchValue] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchValue.trim());
    }, 300);
    return () => clearTimeout(timer);
  }, [searchValue]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setIsSearchOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const { data: searchResults, isFetching: isSearching } = useQuery({
    queryKey: ["navbar-search", debouncedSearch],
    queryFn: () => getCompanies({ search: debouncedSearch, limit: 6 }),
    enabled: debouncedSearch.length >= 1,
    staleTime: 30_000,
  });

  const handleSearchSelect = (ticker: string) => {
    setSearchValue("");
    setDebouncedSearch("");
    setIsSearchOpen(false);
    router.push(`/company/${ticker}`);
  };

  const toggleTheme = () => {
    setTheme(resolvedTheme === "dark" ? "light" : "dark");
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-screen-2xl items-center gap-6 px-4 sm:px-6 lg:px-8">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary">
            <span className="text-xs font-bold text-primary-foreground">
              Ex
            </span>
          </div>
          <span className="text-lg font-bold tracking-tight text-foreground">
            Excella
          </span>
        </Link>

        {/* Nav Links */}
        <nav className="hidden items-center gap-1 md:flex">
          {navLinks.map(({ href, label, icon: Icon }) => {
            const isActive =
              pathname === href || pathname.startsWith(href + "/");
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            );
          })}

          {/* Watchlist link — only when authenticated */}
          {isAuthenticated && (
            <Link
              href="/watchlist"
              className={cn(
                "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                pathname === "/watchlist" || pathname.startsWith("/watchlist/")
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Star className="h-4 w-4" />
              Watchlist
            </Link>
          )}
        </nav>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Search */}
        <div ref={searchRef} className="relative hidden w-64 sm:block lg:w-80">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search ticker or company..."
            value={searchValue}
            onChange={(e) => {
              setSearchValue(e.target.value);
              setIsSearchOpen(true);
            }}
            onFocus={() => {
              if (debouncedSearch.length >= 1) setIsSearchOpen(true);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && searchResults?.data?.[0]) {
                handleSearchSelect(searchResults.data[0].ticker);
              }
              if (e.key === "Escape") setIsSearchOpen(false);
            }}
            className="pl-9 h-8 text-sm"
          />

          {isSearchOpen && debouncedSearch.length >= 1 && (
            <div className="absolute z-50 mt-1 w-full rounded-lg border border-border bg-card shadow-lg">
              {isSearching && (
                <div className="px-4 py-3 text-sm text-muted-foreground">
                  Searching...
                </div>
              )}

              {!isSearching && (searchResults?.data ?? []).length === 0 && (
                <div className="px-4 py-3 text-sm text-muted-foreground">
                  No results found
                </div>
              )}

              {!isSearching &&
                (searchResults?.data ?? []).map((company) => (
                  <button
                    key={company.ticker}
                    type="button"
                    className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm transition-colors hover:bg-muted/50 first:rounded-t-lg last:rounded-b-lg"
                    onClick={() => handleSearchSelect(company.ticker)}
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

        {/* Auth section */}
        {isAuthenticated ? (
          <div className="flex items-center gap-3 shrink-0">
            <div className="hidden items-center gap-1.5 text-sm text-muted-foreground sm:flex">
              <User className="h-3.5 w-3.5" />
              <span className="max-w-30 truncate">
                {user?.name || user?.email}
              </span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={logout}
              className="text-muted-foreground hover:text-foreground"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Log out</span>
            </Button>
          </div>
        ) : (
          <Link href="/login">
            <Button variant="outline" size="sm" className="shrink-0">
              Log in
            </Button>
          </Link>
        )}

        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          aria-label="Toggle theme"
          className="shrink-0"
        >
          {resolvedTheme === "dark" ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </Button>
      </div>
    </header>
  );
}
