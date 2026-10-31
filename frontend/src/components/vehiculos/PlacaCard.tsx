import { Pencil } from "lucide-react";
import { Checkbox, EstadoBadge, UbicacionChip, cn } from "@/components/ui";
import { formatPlaca } from "@/lib/format";
import { formatCR } from "@/lib/time";
import type { Placa } from "@/lib/types";

export interface PlacaCardProps {
  placa: Placa;
  selected: boolean;
  selectable: boolean;
  onToggle: () => void;
  onEdit?: () => void;
}

export default function PlacaCard({ placa, selected, selectable, onToggle, onEdit }: PlacaCardProps) {
  const rentada = placa.estado === "Rentada";
  const label = formatPlaca(placa);
  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-2xl border bg-bg p-3 shadow-sm transition-colors dark:shadow-none",
        selected ? "border-red bg-red-soft" : "border-border",
        rentada && "bg-surface opacity-70",
      )}
    >
      {selectable ? (
        <label className="flex size-11 shrink-0 cursor-pointer items-center justify-center">
          <Checkbox checked={selected} onChange={onToggle} aria-label={`Seleccionar ${label}`} />
        </label>
      ) : (
        <span className="size-11 shrink-0" aria-hidden="true" />
      )}
      <div className="min-w-0 flex-1">
        <p className="truncate font-display text-xl font-bold tracking-wide tabular-nums">{label}</p>
        <div className="mt-1 flex flex-wrap items-center gap-1.5">
          <EstadoBadge estado={placa.estado} />
          {!rentada && <UbicacionChip value={placa.ubicacion_actual} />}
        </div>
        {rentada && placa.fecha_hora_finalizacion && (
          <p className="mt-1 text-sm text-ink-muted">Vuelve: {formatCR(placa.fecha_hora_finalizacion)}</p>
        )}
      </div>
      {onEdit && (
        <button
          type="button"
          onClick={onEdit}
          aria-label={`Editar ${label}`}
          className="inline-flex size-11 shrink-0 items-center justify-center rounded-full text-ink-muted hover:bg-surface-2 hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red"
        >
          <Pencil className="size-5" />
        </button>
      )}
    </div>
  );
}
