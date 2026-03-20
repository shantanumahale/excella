"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

interface CompanyNavProps {
  ticker: string;
}

const NAV_ITEMS = [
  { label: "Overview", href: "" },
  { label: "Financials", href: "/financials" },
  { label: "Metrics", href: "/metrics" },
  { label: "Valuation", href: "/valuation" },
  { label: "Price", href: "/price" },
  { label: "Filings", href: "/filings" },
];

export function CompanyNav({ ticker }: CompanyNavProps) {
  const pathname = usePathname();
  const basePath = `/company/${ticker}`;

  return (
    <nav className="flex items-center gap-1 rounded-lg bg-muted p-1">
      {NAV_ITEMS.map((item) => {
        const href = `${basePath}${item.href}`;
        const isActive =
          item.href === ""
            ? pathname === basePath
            : pathname.startsWith(href);

        return (
          <Link
            key={item.href}
            href={href}
            className={cn(
              "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all",
              isActive
                ? "bg-background text-foreground shadow"
                : "text-muted-foreground hover:bg-background/50 hover:text-foreground"
            )}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
