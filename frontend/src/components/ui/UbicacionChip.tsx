import { AlertTriangle, MapPin } from "lucide-react";
import { UBICACION_NO_ACTUALIZADA } from "@/lib/constants";
import { cn } from "./cn";

export interface UbicacionChipProps {
  value: string;
  count?: number;
  className?: string;
}

export function UbicacionChip({ value, count, className }: UbicacionChipProps) {
  const warn = value === UBICACION_NO_ACTUALIZADA;
  const Icon = warn ? AlertTriangle : MapPin;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-1 text-sm font-medium",
        warn ? "bg-warn/15 text-warn" : "bg-surface-2 text-ink",
        className,
      )}
    >
      <Icon className="size-3.5 shrink-0" aria-hidden="true" />
      {value}
      {count !== undefined && <span className="tabular-nums"> · {count}</span>}
    </span>
  );
}
