"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ExternalLink, FileText, Loader2 } from "lucide-react";
import api from "@/lib/api";

const FORM_TYPES = ["All", "10-K", "10-Q", "8-K"] as const;
type FormType = (typeof FORM_TYPES)[number];

interface Filing {
  form_type: string;
  filing_date: string;
  period_of_report: string;
  description: string;
  edgar_url: string;
  accession_number: string;
  primary_document: string;
}

interface FilingsResponse {
  total: number;
  offset: number;
  limit: number;
  data: Filing[];
}

export default function FilingsPage() {
  const params = useParams<{ ticker: string }>();
  const ticker = params.ticker.toUpperCase();

  const [formFilter, setFormFilter] = useState<FormType>("All");
  const [filings, setFilings] = useState<Filing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchFilings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams: Record<string, string> = {};
      if (formFilter !== "All") {
        queryParams.form_type = formFilter;
      }
      const { data } = await api.get<FilingsResponse>(
        `/companies/${ticker}/filings`,
        { params: queryParams },
      );
      setFilings(data.data);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to load filings";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [ticker, formFilter]);

  useEffect(() => {
    fetchFilings();
  }, [fetchFilings]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-lg font-semibold">SEC Filings</h2>
        <div className="flex items-center gap-1.5">
          {FORM_TYPES.map((ft) => (
            <Button
              key={ft}
              variant={formFilter === ft ? "default" : "outline"}
              size="sm"
              onClick={() => setFormFilter(ft)}
            >
              {ft}
            </Button>
          ))}
        </div>
      </div>

      {/* Filings table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="py-12 text-center text-sm text-destructive">
              {error}
            </div>
          ) : filings.length === 0 ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              No filings found for {ticker}
              {formFilter !== "All" ? ` with form type ${formFilter}` : ""}.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">Form Type</TableHead>
                  <TableHead className="w-[120px]">Filing Date</TableHead>
                  <TableHead className="w-[120px]">Period</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="w-[80px] text-right">Link</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filings.map((filing) => (
                  <TableRow key={filing.accession_number}>
                    <TableCell>
                      <Badge
                        variant={
                          filing.form_type === "10-K"
                            ? "default"
                            : filing.form_type === "10-Q"
                              ? "secondary"
                              : "outline"
                        }
                      >
                        {filing.form_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm tabular-nums">
                      {filing.filing_date}
                    </TableCell>
                    <TableCell className="text-sm tabular-nums">
                      {filing.period_of_report}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {filing.description}
                    </TableCell>
                    <TableCell className="text-right">
                      <a
                        href={filing.edgar_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                      >
                        <FileText className="h-3.5 w-3.5" />
                        EDGAR
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
