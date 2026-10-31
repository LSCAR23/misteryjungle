"use client";

import useSWR from "swr";
import { Button, EmptyState, PageHeader, Skeleton } from "@/components/ui";
import CategoriaCard from "@/components/vehiculos/CategoriaCard";
import { swrFetcher } from "@/lib/api";
import type { CategoriaResumen } from "@/lib/types";

const GRID = "grid grid-cols-1 min-[361px]:grid-cols-2 gap-3 md:grid-cols-3 md:gap-4 lg:grid-cols-5";

export default function DisponibilidadPage() {
  const { data, error, isLoading, mutate } = useSWR<CategoriaResumen[]>(
    "/disponibilidad/categorias",
    swrFetcher,
    { revalidateOnFocus: true },
  );

  return (
    <div>
      <PageHeader title="Disponibilidad" subtitle="Elige una categoría" />
      {error && !data ? (
        <EmptyState
          title="No se pudo cargar"
          description={error instanceof Error ? error.message : undefined}
          action={<Button onClick={() => void mutate()}>Reintentar</Button>}
        />
      ) : isLoading || !data ? (
        <div className={GRID}>
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-64" />
          ))}
        </div>
      ) : (
        <div className={GRID}>
          {data.map((r) => (
            <CategoriaCard key={r.categoria} resumen={r} />
          ))}
        </div>
      )}
    </div>
  );
}
