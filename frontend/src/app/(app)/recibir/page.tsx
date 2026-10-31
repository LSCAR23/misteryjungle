"use client";

import { useEffect, useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { PackageCheck } from "lucide-react";
import { Badge, Button, EmptyState, PageHeader, Skeleton } from "@/components/ui";
import { RecibirItem, recibirKey, type RecibirData, type RecibirVariant } from "@/components/rentas/RecibirItem";
import { RecibirSheet } from "@/components/rentas/RecibirSheet";
import { swrFetcher } from "@/lib/api";
import ExtenderSheet from "@/components/rentas/ExtenderSheet";
import type { Renta, RecibirResponse } from "@/lib/types";

interface Section {
  id: RecibirVariant;
  title: string;
  items: RecibirData[];
}

export default function RecibirPage() {
  const { data, error, isLoading, mutate } = useSWR<RecibirResponse>("/recibir", swrFetcher, {
    refreshInterval: 60000,
  });
  const { mutate: globalMutate } = useSWRConfig();
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 30000);
    return () => clearInterval(t);
  }, []);
  const [target, setTarget] = useState<string[] | null>(null);
  const [extender, setExtender] = useState<Renta | null>(null);

  const allSections: Section[] = data
    ? [
        {
          id: "vencida",
          title: "Vencidas sin recibir",
          items: data.vencidas.map((renta) => ({ kind: "renta", renta })),
        },
        {
          id: "hoy",
          title: "Vencen hoy",
          items: data.hoy.map((renta) => ({ kind: "renta", renta })),
        },
        {
          id: "sin_ubicacion",
          title: "Ubicación no actualizada",
          items: data.sin_ubicacion.map((placa) => ({ kind: "placa", placa })),
        },
      ]
    : [];
  const sections = allSections.filter((s) => s.items.length > 0);

  const validKeys = new Set(sections.flatMap((s) => s.items.map(recibirKey)));
  const activeSel = [...selected].filter((k) => validKeys.has(k));
  const sheetKeys = target ?? [];

  function toggle(key: string) {
    setSelected((prev) => {
      const n = new Set(prev);
      if (n.has(key)) n.delete(key);
      else n.add(key);
      return n;
    });
  }

  function toggleSection(s: Section) {
    const keys = s.items.map(recibirKey);
    setSelected((prev) => {
      const n = new Set(prev);
      const all = keys.every((k) => n.has(k));
      keys.forEach((k) => (all ? n.delete(k) : n.add(k)));
      return n;
    });
  }

  const ids = (keys: string[], prefix: string) =>
    keys.filter((k) => k.startsWith(prefix)).map((k) => k.slice(prefix.length));

  async function done() {
    setTarget(null);
    setSelected(new Set());
    await Promise.all([
      mutate(),
      globalMutate(
        (key) => typeof key === "string" && (key.startsWith("/disponibilidad") || key.startsWith("/vehiculos")),
      ),
    ]);
  }

  async function extenderDone() {
    await Promise.all([
      mutate(),
      globalMutate(
        (key) => typeof key === "string" && (key.startsWith("/disponibilidad") || key.startsWith("/vehiculos")),
      ),
    ]);
  }

  return (
    <div className={activeSel.length > 0 ? "pb-28" : undefined}>
      <PageHeader title="Recibir" subtitle="Actualiza dónde quedó cada vehículo al recibirlo" />

      {isLoading && (
        <div className="space-y-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-28 w-full" />
          ))}
        </div>
      )}

      {error && !data && (
        <EmptyState
          title="No se pudo cargar"
          description={error instanceof Error ? error.message : "Ocurrió un error inesperado"}
          action={<Button onClick={() => mutate()}>Reintentar</Button>}
        />
      )}

      {data && sections.length === 0 && (
        <EmptyState icon={<PackageCheck />} title="Todo al día" description="No hay vehículos por recibir" />
      )}

      {sections.map((s) => {
        const allSel = s.items.every((i) => selected.has(recibirKey(i)));
        return (
          <section key={s.id} className="mb-6">
            <div className="mb-2 flex items-center justify-between gap-2">
              <h2 className="flex items-center gap-2 font-display text-xl font-bold uppercase tracking-wide">
                {s.title}
                <Badge tone={s.id === "vencida" ? "warn" : "neutral"}>{s.items.length}</Badge>
              </h2>
              <Button size="sm" variant="ghost" onClick={() => toggleSection(s)} className="min-h-11">
                {allSel ? "Quitar todo" : "Seleccionar todo"}
              </Button>
            </div>
            <div className="space-y-2">
              {s.items.map((it) => {
                const key = recibirKey(it);
                return (
                  <RecibirItem
                    key={key}
                    data={it}
                    variant={s.id}
                    now={now}
                    selected={selected.has(key)}
                    onToggle={() => toggle(key)}
                    onRecibir={() => setTarget([key])}
                    onExtender={
                      it.kind === "renta" && s.id !== "sin_ubicacion"
                        ? () => setExtender(it.renta)
                        : undefined
                    }
                  />
                );
              })}
            </div>
          </section>
        );
      })}

      {activeSel.length > 0 && (
        <div className="fixed inset-x-0 bottom-[calc(4.25rem+env(safe-area-inset-bottom))] z-20 border-t border-border bg-bg/95 px-4 py-3 backdrop-blur lg:bottom-0 lg:left-64">
          <div className="mx-auto flex max-w-3xl items-center justify-between gap-3">
            <span className="font-semibold tabular-nums">{activeSel.length} seleccionados</span>
            <Button size="lg" onClick={() => setTarget(activeSel)}>
              Recibir en…
            </Button>
          </div>
        </div>
      )}

      <ExtenderSheet
        open={extender !== null}
        onClose={() => setExtender(null)}
        renta={extender}
        onDone={extenderDone}
      />

      <RecibirSheet
        open={target !== null}
        onClose={() => setTarget(null)}
        rentaIds={ids(sheetKeys, "renta:")}
        placaIds={ids(sheetKeys, "placa:")}
        onDone={done}
      />
    </div>
  );
}
