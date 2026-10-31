"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import useSWR from "swr";
import { Button, EmptyState, PageHeader, Skeleton } from "@/components/ui";
import VehiculoCard from "@/components/vehiculos/VehiculoCard";
import { swrFetcher } from "@/lib/api";
import { categoriaLabel, slugToCategoria } from "@/lib/categorias";
import type { VehiculoDisponibilidad } from "@/lib/types";

const GRID = "grid grid-cols-1 gap-3 md:grid-cols-2 md:gap-4 xl:grid-cols-3";

export default function CategoriaPage() {
  const params = useParams<{ categoria: string }>();
  const categoria = slugToCategoria(params.categoria ?? "");

  const { data, error, isLoading, mutate } = useSWR<VehiculoDisponibilidad[]>(
    categoria ? `/disponibilidad?categoria=${encodeURIComponent(categoria)}` : null,
    swrFetcher,
    { revalidateOnFocus: true },
  );

  if (!categoria) {
    return (
      <EmptyState
        title="Categoría no encontrada"
        description="La categoría que buscas no existe."
        action={
          <Link href="/disponibilidad" className="font-semibold text-red underline">
            Volver a Disponibilidad
          </Link>
        }
      />
    );
  }

  const total = data?.reduce((s, v) => s + v.disponibles, 0);
  const ordenados = data
    ? [...data].sort((a, b) => Number(a.disponibles === 0) - Number(b.disponibles === 0))
    : [];

  return (
    <div>
      <PageHeader
        backHref="/disponibilidad"
        title={categoriaLabel(categoria)}
        subtitle={total !== undefined ? `${total} ${total === 1 ? "disponible" : "disponibles"} en total` : undefined}
      />
      {error && !data ? (
        <EmptyState
          title="No se pudo cargar"
          description={error instanceof Error ? error.message : undefined}
          action={<Button onClick={() => void mutate()}>Reintentar</Button>}
        />
      ) : isLoading || !data ? (
        <div className={GRID}>
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-72" />
          ))}
        </div>
      ) : ordenados.length === 0 ? (
        <EmptyState title="Sin vehículos" description="No hay vehículos en esta categoría." />
      ) : (
        <div className={GRID}>
          {ordenados.map((v) => (
            <VehiculoCard key={v.id} vehiculo={v} />
          ))}
        </div>
      )}
    </div>
  );
}
