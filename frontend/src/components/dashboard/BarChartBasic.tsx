"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export interface BarDatum {
  label: string;
  value: number;
  /** Etiqueta completa para el tooltip */
  full?: string;
  /** Barra resaltada (con `emphasis`, las demás se atenúan) */
  highlight?: boolean;
}

interface Props {
  data: BarDatum[];
  horizontal?: boolean;
  format?: (n: number) => string;
  seriesName: string;
  emphasis?: boolean;
}

const tick = { fill: "var(--ink-muted)", fontSize: 12 };

function truncate(s: string, n: number) {
  return s.length > n ? `${s.slice(0, n - 1)}…` : s;
}

export function BarChartBasic({ data, horizontal, format = String, seriesName, emphasis }: Props) {
  const fmt = (v: unknown) => format(Number(v));
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={data}
        layout={horizontal ? "vertical" : "horizontal"}
        margin={{ top: 4, right: 8, bottom: 0, left: 0 }}
        barCategoryGap="22%"
      >
        <CartesianGrid
          stroke="var(--border)"
          strokeDasharray="3 3"
          vertical={!!horizontal}
          horizontal={!horizontal}
        />
        {horizontal ? (
          <>
            <XAxis type="number" tick={tick} tickLine={false} axisLine={false} tickFormatter={fmt} allowDecimals={false} />
            <YAxis
              type="category"
              dataKey="label"
              width={110}
              tick={tick}
              tickLine={false}
              axisLine={{ stroke: "var(--border)" }}
              interval={0}
              tickFormatter={(v: string) => truncate(v, 16)}
            />
          </>
        ) : (
          <>
            <XAxis dataKey="label" tick={tick} tickLine={false} axisLine={{ stroke: "var(--border)" }} interval={0} />
            <YAxis tick={tick} tickLine={false} axisLine={false} width={60} tickFormatter={fmt} allowDecimals={false} />
          </>
        )}
        <Tooltip
          cursor={{ fill: "var(--surface-2)", opacity: 0.6 }}
          formatter={(v) => [fmt(v), seriesName]}
          labelFormatter={(_, p) => p?.[0]?.payload?.full ?? p?.[0]?.payload?.label ?? ""}
          contentStyle={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            color: "var(--ink)",
            fontSize: 13,
          }}
          labelStyle={{ color: "var(--ink)", fontWeight: 700 }}
          itemStyle={{ color: "var(--ink)" }}
        />
        <Bar
          dataKey="value"
          name={seriesName}
          fill="var(--red)"
          radius={horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]}
          maxBarSize={36}
        >
          {data.map((d, i) => (
            <Cell key={i} fill="var(--red)" fillOpacity={emphasis && !d.highlight ? 0.55 : 1} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
