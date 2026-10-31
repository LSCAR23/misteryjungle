"use client";

import Link from "next/link";
import useSWR from "swr";
import { Users } from "lucide-react";
import { swrFetcher } from "@/lib/api";
import type { Usuario } from "@/lib/types";
import { Badge, Button, Card, EmptyState, PageHeader, Skeleton } from "@/components/ui";

export default function UsuariosPage() {
  const { data, error, isLoading, mutate } = useSWR<Usuario[]>("/usuarios", swrFetcher);

  return (
    <div>
      <PageHeader
        title="Usuarios"
        actions={
          <Link
            href="/admin/usuarios/nuevo"
            className="inline-flex min-h-11 items-center justify-center rounded-xl bg-red px-5 text-base font-semibold text-white hover:bg-red-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red focus-visible:ring-offset-2 focus-visible:ring-offset-bg"
          >
            Nuevo usuario
          </Link>
        }
      />
      {isLoading ? (
        <div className="space-y-3">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-[72px]" />
          ))}
        </div>
      ) : error ? (
        <EmptyState
          title="No se pudo cargar"
          description={error instanceof Error ? error.message : undefined}
          action={<Button onClick={() => mutate()}>Reintentar</Button>}
        />
      ) : !data || data.length === 0 ? (
        <EmptyState icon={<Users />} title="Sin usuarios" description="Crea el primer usuario." />
      ) : (
        <ul className="space-y-3">
          {data.map((u) => (
            <li key={u.id}>
              <Card className="flex items-center gap-4 p-4">
                <div
                  aria-hidden="true"
                  className="flex size-11 shrink-0 items-center justify-center rounded-full bg-surface-2 font-display text-lg font-bold uppercase"
                >
                  {u.username.charAt(0)}
                </div>
                <span className="min-w-0 flex-1 truncate text-base font-semibold">{u.username}</span>
                <Badge tone={u.rol === "admin" ? "red" : "neutral"}>
                  {u.rol === "admin" ? "Admin" : "Empleado"}
                </Badge>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
