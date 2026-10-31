import Link from "next/link";
import { Badge, Card, UbicacionChip, cn } from "@/components/ui";
import { categoriaToSlug } from "@/lib/categorias";
import type { VehiculoDisponibilidad } from "@/lib/types";
import VehicleImage from "./VehicleImage";

export default function VehiculoCard({ vehiculo: v }: { vehiculo: VehiculoDisponibilidad }) {
  const nombre = `${v.marca} ${v.modelo}`;
  const vacio = v.disponibles === 0;
  return (
    <Link
      href={`/disponibilidad/${categoriaToSlug(v.categoria)}/${v.id}`}
      className="block rounded-2xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red"
    >
      <Card interactive className={cn("h-full overflow-hidden", vacio && "opacity-60")}>
        <VehicleImage src={v.imagen} categoria={v.categoria} alt={nombre} />
        <div className="flex flex-col gap-3 p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h2 className="truncate font-display text-xl font-bold uppercase tracking-wide">{nombre}</h2>
              <p className="text-sm text-ink-muted">{v.cilindrada} cc</p>
            </div>
            <Badge tone={vacio ? "off" : "ok"}>{vacio ? "Sin disponibles" : `${v.disponibles} ${v.disponibles === 1 ? "disponible" : "disponibles"}`}</Badge>
          </div>
          {v.por_ubicacion.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {v.por_ubicacion.map((u) => (
                <UbicacionChip key={u.ubicacion} value={u.ubicacion} count={u.disponibles} />
              ))}
            </div>
          )}
        </div>
      </Card>
    </Link>
  );
}
