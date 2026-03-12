"use client";

import { useParams, useRouter } from "next/navigation";
import { MacroDetail } from "@/components/macro/macro-detail";
import { useMacroSeries } from "@/hooks/use-macro";
import { useMemo } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function MacroSeriesPage() {
  const router = useRouter();
  const params = useParams<{ seriesId: string }>();
  const seriesId = params.seriesId.toUpperCase();

  const { data: allSeries } = useMacroSeries();

  const seriesMeta = useMemo(
    () => allSeries?.find((s) => s.series_id === seriesId),
    [allSeries, seriesId],
  );

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm">
        <div onClick={() => {
          router.back();
        }} className="flex items-center">
          <ArrowLeft className="mr-1.5 h-4 w-4" />
          Back to Macro Dashboard
        </div>
      </Button>

      <MacroDetail seriesId={seriesId} seriesMeta={seriesMeta} />
    </div>
  );
}
