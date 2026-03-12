"use client";

import { useMemo } from "react";
import {
  ResponsiveContainer,
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

export interface LineConfig {
  key: string;
  label: string;
  color: string;
}

interface LineChartProps {
  data: Record<string, unknown>[];
  xKey: string;
  lines: LineConfig[];
  height?: number;
  className?: string;
  tickFormatter?: (value: string) => string;
  tooltipLabelFormatter?: (label: unknown) => string;
}

const TICK_STYLE = { fontSize: 12, fill: "var(--color-muted-foreground, #6b7280)" };

function LineChart({
  data,
  xKey,
  lines,
  height = 350,
  className,
  tickFormatter,
  tooltipLabelFormatter,
}: LineChartProps) {
  // Auto-calculate a reasonable tick interval to avoid overcrowding
  const tickInterval = useMemo(() => {
    if (data.length <= 12) return 0;
    return Math.max(0, Math.floor(data.length / 8) - 1);
  }, [data.length]);

  return (
    <div className={className} style={{ width: "100%", height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsLineChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border, #e5e7eb)" opacity={0.5} />
          <XAxis
            dataKey={xKey}
            tick={TICK_STYLE}
            tickLine={false}
            axisLine={false}
            tickFormatter={tickFormatter}
            interval={tickInterval}
          />
          <YAxis
            tick={TICK_STYLE}
            tickLine={false}
            axisLine={false}
            width={60}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "var(--color-card, #fff)",
              border: "1px solid var(--color-border, #e5e7eb)",
              borderRadius: 8,
              fontSize: 13,
            }}
            labelFormatter={tooltipLabelFormatter}
          />
          {lines.length > 1 && (
            <Legend
              wrapperStyle={{ fontSize: 12 }}
            />
          )}
          {lines.map((line) => (
            <Line
              key={line.key}
              type="monotone"
              dataKey={line.key}
              name={line.label}
              stroke={line.color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              isAnimationActive={data.length < 500}
            />
          ))}
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
}

export { LineChart };
