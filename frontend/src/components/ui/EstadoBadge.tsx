import type { EstadoPlaca } from "@/lib/constants";
import { Badge, type BadgeTone } from "./Badge";

const map: Record<EstadoPlaca, { tone: BadgeTone; dot: string }> = {
  Disponible: { tone: "ok", dot: "bg-ok" },
  Rentada: { tone: "red", dot: "bg-red" },
  "Fuera de Servicio": { tone: "off", dot: "bg-off" },
};

export function EstadoBadge({ estado, className }: { estado: EstadoPlaca; className?: string }) {
  const m = map[estado];
  return (
    <Badge tone={m.tone} className={className}>
      <span className={`size-2 rounded-full ${m.dot}`} aria-hidden="true" />
      {estado}
    </Badge>
  );
}
