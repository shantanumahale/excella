"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, formatRatio } from "@/lib/formatters";
import { useValuationComps } from "@/hooks/use-valuation";

interface CompsTableProps {
  ticker: string;
}

const MULTIPLE_LABELS: Record<string, string> = {
  pe_ratio: "P/E",
  ev_to_ebitda: "EV/EBITDA",
  price_to_sales: "P/S",
  price_to_book: "P/B",
  ev_to_revenue: "EV/Rev",
};

export function CompsTable({ ticker }: CompsTableProps) {
  const { data, isLoading } = useValuationComps(ticker);

  if (isLoading) {
    return <Skeleton className="h-[300px] w-full" />;
  }

  if (!data) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-muted-foreground">
            No comparable companies found.
          </p>
        </CardContent>
      </Card>
    );
  }

  const multiples = Object.keys(MULTIPLE_LABELS);

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Comparable Companies ({data.peer_count} peers)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="sticky left-0 bg-card">Company</TableHead>
                {multiples.map((m) => (
                  <TableHead key={m} className="text-right">
                    {MULTIPLE_LABELS[m]}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.peers.map((peer) => (
                <TableRow key={peer.ticker}>
                  <TableCell className="sticky left-0 bg-card font-medium">
                    {peer.ticker}
                  </TableCell>
                  {multiples.map((m) => (
                    <TableCell key={m} className="text-right">
                      {formatRatio(peer.multiples[m])}
                    </TableCell>
                  ))}
                </TableRow>
              ))}

              {/* Median row */}
              <TableRow className="border-t-2 font-semibold">
                <TableCell className="sticky left-0 bg-card">Median</TableCell>
                {multiples.map((m) => (
                  <TableCell key={m} className="text-right">
                    {formatRatio(data.multiples[m])}
                  </TableCell>
                ))}
              </TableRow>
            </TableBody>
          </Table>
        </div>

        {/* Implied values */}
        {data.implied_values && Object.keys(data.implied_values).length > 0 && (
          <div className="mt-6">
            <p className="mb-2 text-sm font-medium text-muted-foreground">
              Implied Value per Share
            </p>
            <div className="flex flex-wrap gap-3">
              {Object.entries(data.implied_values).map(([key, val]) => (
                <div
                  key={key}
                  className="rounded-md border border-border px-3 py-1.5 text-sm"
                >
                  <span className="text-muted-foreground">
                    {key.replace("_implied", "").toUpperCase()}:{" "}
                  </span>
                  <span className="font-medium">{formatCurrency(val)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
