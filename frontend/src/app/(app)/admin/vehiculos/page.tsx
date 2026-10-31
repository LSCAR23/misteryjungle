"use client";

import Link from "next/link";
import useSWR from "swr";
import { Bike } from "lucide-react";
import { swrFetcher } from "@/lib/api";
import { CATEGORIAS } from "@/lib/constants";
import type { Vehiculo } from "@/lib/types";
import { Button, Card, EmptyState, PageHeader, Skeleton } from "@/components/ui";
import VehicleImage from "@/components/vehiculos/VehicleImage";

export default function AdminVehiculosPage() {
  const { data, error, isLoading, mutate } = useSWR<Vehiculo[]>("/vehiculos", swrFetcher);

  return (
    <div>
      <PageHeader
        title="Vehículos"
        actions={
          <Link
            href="/admin/vehiculos/nuevo"
            className="inline-flex min-h-11 items-center justify-center rounded-xl bg-red px-5 text-base font-semibold text-white hover:bg-red-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red focus-visible:ring-offset-2 focus-visible:ring-offset-bg"
          >
            Nuevo vehículo
          </Link>
        }
      />
      {isLoading ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : error ? (
        <EmptyState
          title="No se pudo cargar"
          description={error instanceof Error ? error.message : undefined}
          action={<Button onClick={() => mutate()}>Reintentar</Button>}
        />
      ) : !data || data.length === 0 ? (
        <EmptyState icon={<Bike />} title="Sin vehículos" description="Agrega el primer vehículo." />
      ) : (
        <div className="space-y-8">
          {CATEGORIAS.map((c) => {
            const items = data.filter((v) => v.categoria === c.value);
            if (items.length === 0) return null;
            return (
              <section key={c.value} aria-labelledby={`cat-${c.value}`}>
                <h2
                  id={`cat-${c.value}`}
                  className="mb-3 font-display text-xl font-bold uppercase tracking-wide"
                >
                  {c.label}
                </h2>
                <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {items.map((v) => (
                    <li key={v.id}>
                      <Link
                        href={`/disponibilidad/${v.categoria.toLowerCase()}/${v.id}`}
                        className="block rounded-2xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red"
                      >
                        <Card interactive className="flex items-center gap-3 overflow-hidden p-2 pr-4">
                          <div className="w-28 shrink-0">
                            <VehicleImage src={v.imagen} categoria={v.categoria} alt="" className="rounded-xl" sizes="112px" />
                          </div>
                          <div className="min-w-0">
                            <p className="truncate font-semibold">
                              {v.marca} {v.modelo}
                            </p>
                            <p className="text-sm text-ink-muted">
                              {v.cilindrada} cc · {v.cantidad} {v.cantidad === 1 ? "unidad" : "unidades"}
                            </p>
                          </div>
                        </Card>
                      </Link>
                    </li>
                  ))}
                </ul>
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
