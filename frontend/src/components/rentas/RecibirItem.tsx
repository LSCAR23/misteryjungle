"use client";

import { Badge, Button, Checkbox, UbicacionChip, cn } from "@/components/ui";
import { UBICACION_NO_ACTUALIZADA } from "@/lib/constants";
import { formatCR, formatHoraCR } from "@/lib/time";
import type { Renta, Placa } from "@/lib/types";

export type RecibirVariant = "vencida" | "hoy" | "sin_ubicacion";

export type RecibirData =
  | { kind: "renta"; renta: Renta }
  | { kind: "placa"; placa: Placa & { vehiculo: string } };

export function recibirKey(d: RecibirData): string {
  return d.kind === "renta" ? `renta:${d.renta.id}` : `placa:${d.placa.id}`;
}

interface Props {
  data: RecibirData;
  variant: RecibirVariant;
  selected: boolean;
  onToggle: () => void;
  onRecibir: () => void;
  now: number;
}

export function RecibirItem({ data, variant, selected, onToggle, onRecibir, now }: Props) {
  const vehiculo = data.kind === "renta" ? data.renta.vehiculo : data.placa.vehiculo;
  const placa = data.kind === "renta" ? data.renta.placa : data.placa.placa;
  const atrasada =
    data.kind === "renta" && variant === "hoy" && new Date(data.renta.fin_programado).getTime() < now;

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-2xl border bg-bg p-3 shadow-sm dark:shadow-none",
        variant === "vencida" ? "border-l-4 border-border border-l-warn" : "border-border",
        selected && "ring-2 ring-red",
      )}
    >
      <label className="flex min-h-11 min-w-11 cursor-pointer items-center justify-center">
        <Checkbox
          checked={selected}
          onChange={onToggle}
          aria-label={`Seleccionar ${vehiculo} ${placa}`}
          className="size-8"
        />
      </label>
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <span className="font-semibold">{vehiculo}</span>
          <span className="font-mono text-sm text-ink-muted">{placa}</span>
          {atrasada && <Badge tone="red">Atrasada</Badge>}
        </div>
        {data.kind === "renta" && (
          <>
            <p className="text-sm text-ink-muted">
              {variant === "vencida"
                ? `Venció ${formatCR(data.renta.fin_programado)}`
                : `Vence ${formatHoraCR(data.renta.fin_programado)}`}
            </p>
            <p className="text-sm text-ink-muted">
              {variant === "vencida" ? `Rentó: ${data.renta.usuario}` : data.renta.usuario}
            </p>
            <UbicacionChip
              value={variant === "vencida" ? UBICACION_NO_ACTUALIZADA : data.renta.ubicacion_placa}
            />
          </>
        )}
      </div>
      <Button size="sm" variant="outline" onClick={onRecibir} className="min-h-11 shrink-0">
        Recibir
      </Button>
    </div>
  );
}
