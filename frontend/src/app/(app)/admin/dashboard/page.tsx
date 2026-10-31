"use client";

import useSWR from "swr";
import { AlertTriangle, CalendarDays, Trophy, TrendingUp, UserRound } from "lucide-react";
import { Button, EmptyState, PageHeader } from "@/components/ui";
import { swrFetcher } from "@/lib/api";
import { formatMoney, pluralize } from "@/lib/format";
import { CATEGORIAS } from "@/lib/constants";
import type { Metricas } from "@/lib/types";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { HighlightCard } from "@/components/dashboard/HighlightCard";
import { ChartCard } from "@/components/dashboard/ChartCard";
import { BarChartBasic } from "@/components/dashboard/BarChartBasic";
import { DashboardSkeleton } from "@/components/dashboard/DashboardSkeleton";

const MESES_CORTO = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const MESES_LARGO = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];

function parseMes(m: string): { y: number; i: number } {
  const [y, mm] = m.split("-").map(Number);
  return { y, i: (mm || 1) - 1 };
}

function mesLargo(m: string): string {
  const { y, i } = parseMes(m);
  return `${MESES_LARGO[i] ?? m} ${y}`;
}

function formatDuracion(h: number): string {
  if (h >= 24) return `${(h / 24).toFixed(1)} días`;
  return `${h.toFixed(1)} h`;
}

function rentasTxt(n: number): string {
  return `${n} ${pluralize(n, "renta", "rentas")}`;
}

function Delta({ actual, anterior }: { actual: number; anterior: number }) {
  if (anterior <= 0) return <span>—</span>;
  const pct = ((actual - anterior) / anterior) * 100;
  const up = pct >= 0;
  return (
    <span className={up ? "font-semibold text-ok" : "font-semibold text-red"}>
      {up ? "↑" : "↓"} {Math.abs(pct).toFixed(0)}%{" "}
      <span className="font-normal text-ink-muted">vs mes anterior</span>
    </span>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-surface px-3 py-2">
      <p className="truncate text-xs text-ink-muted">{label}</p>
      <p className="truncate text-base font-bold tabular-nums">{value}</p>
    </div>
  );
}

export default function Page() {
  const { data, error, isLoading, mutate } = useSWR<Metricas>("/metricas?meses=12", swrFetcher, {
    refreshInterval: 60000,
  });

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Últimos 12 meses" />
      {!data && isLoading ? (
        <DashboardSkeleton />
      ) : !data ? (
        <EmptyState
          icon={<AlertTriangle />}
          title="No se pudo cargar"
          description={error instanceof Error ? error.message : "Ocurrió un error inesperado"}
          action={<Button onClick={() => mutate()}>Reintentar</Button>}
        />
      ) : (
        <Content m={data} />
      )}
    </div>
  );
}

function Content({ m }: { m: Metricas }) {
  const k = m.kpis;
  const lastMes = m.por_mes.length ? m.por_mes[m.por_mes.length - 1].mes : null;

  const porMes = m.por_mes.map((d) => ({
    label: MESES_CORTO[parseMes(d.mes).i] ?? d.mes,
    full: mesLargo(d.mes),
    value: d.ingresos,
    highlight: d.mes === lastMes,
  }));
  const porVehiculo = m.por_vehiculo
    .slice(0, 8)
    .map((d) => ({ label: d.vehiculo.replace(/^Honda /, ""), full: d.vehiculo, value: d.ingresos }));
  const porCategoria = m.por_categoria.map((d) => ({
    label: CATEGORIAS.find((c) => c.value === d.categoria)?.label ?? d.categoria,
    value: d.rentas,
  }));
  const porDia = m.por_dia_semana.map((d) => ({ label: d.dia, value: d.rentas }));
  const porUbic = m.disponibles_por_ubicacion.map((d) => ({
    label: d.ubicacion,
    full: d.ubicacion,
    value: d.disponibles,
  }));

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <KpiCard
          label="Ingresos del mes"
          value={formatMoney(k.ingresos_mes_actual)}
          sub={<Delta actual={k.ingresos_mes_actual} anterior={k.ingresos_mes_anterior} />}
        />
        <KpiCard label="Rentas del mes" value={String(k.rentas_mes_actual)} />
        <KpiCard
          label="Ocupación actual"
          value={`${Math.round(k.ocupacion_actual * 100)}%`}
          sub={`${k.unidades_rentadas} de ${k.unidades_total - k.unidades_fuera_servicio} operativas`}
        />
        <KpiCard
          label="Por recibir"
          value={String(k.pendientes_recibir)}
          tone={k.pendientes_recibir > 0 ? "warn" : "default"}
          href="/recibir"
          sub="Ver pendientes"
        />
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4">
        <HighlightCard
          icon={<Trophy />}
          label="Vehículo más popular"
          title={m.vehiculo_mas_popular?.vehiculo}
          detail={m.vehiculo_mas_popular ? rentasTxt(m.vehiculo_mas_popular.rentas) : undefined}
        />
        <HighlightCard
          icon={<TrendingUp />}
          label="Vehículo que más deja"
          title={m.vehiculo_mas_ingresos?.vehiculo}
          detail={m.vehiculo_mas_ingresos ? formatMoney(m.vehiculo_mas_ingresos.ingresos) : undefined}
        />
        <HighlightCard
          icon={<UserRound />}
          label="Usuario que más renta"
          title={m.usuario_top?.usuario}
          detail={
            m.usuario_top
              ? `${rentasTxt(m.usuario_top.rentas)} · ${formatMoney(m.usuario_top.ingresos)}`
              : undefined
          }
        />
        <HighlightCard
          icon={<CalendarDays />}
          label="Mejor mes"
          title={m.mes_top ? mesLargo(m.mes_top.mes) : null}
          detail={m.mes_top ? formatMoney(m.mes_top.ingresos) : undefined}
        />
      </div>

      <div className="grid grid-cols-3 gap-3">
        <Mini label="Ticket promedio" value={formatMoney(Math.round(k.ticket_promedio * 100) / 100)} />
        <Mini label="Duración promedio" value={formatDuracion(k.duracion_promedio_horas)} />
        <Mini label="Fuera de servicio" value={String(k.unidades_fuera_servicio)} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard title="Ingresos por mes" className="lg:col-span-2">
          <BarChartBasic data={porMes} format={formatMoney} seriesName="Ingresos" emphasis />
        </ChartCard>
        <ChartCard title="Ingresos por vehículo">
          <BarChartBasic data={porVehiculo} horizontal format={formatMoney} seriesName="Ingresos" />
        </ChartCard>
        <ChartCard title="Rentas por categoría">
          <BarChartBasic data={porCategoria} seriesName="Rentas" />
        </ChartCard>
        <ChartCard title="Rentas por día de la semana">
          <BarChartBasic data={porDia} seriesName="Rentas" />
        </ChartCard>
        <ChartCard title="Disponibles por ubicación">
          <BarChartBasic data={porUbic} horizontal seriesName="Disponibles" />
        </ChartCard>
      </div>
    </div>
  );
}
